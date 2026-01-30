"""Langfuse integration for LLM observability.

Provides tracing of LLM calls including prompts, responses,
token usage, latency, and metadata for debugging and evaluation.
"""

import logging
import time
from typing import Any, Dict, Optional

from gitai.providers.base import BaseProvider, GenerationRequest, GenerationResponse
from gitai.utils.logger import log_with_context, setup_logger

try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class LangfuseTracer:
    """Traces LLM calls to Langfuse for observability.

    Wraps provider generate() calls with Langfuse tracing to capture:
    - System prompt and user prompt sent to the LLM
    - Generated response content
    - Token usage and latency
    - Model and provider metadata
    - Git context (files changed, scope, change type)

    Usage:
        tracer = LangfuseTracer(config)
        response = tracer.trace_generation(provider, request, command="commit")
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Langfuse tracer.

        Args:
            config: Langfuse configuration with keys:
                - public_key: Langfuse public key
                - secret_key: Langfuse secret key
                - host: Langfuse server URL (default: https://cloud.langfuse.com)
                - enabled: Whether tracing is active (default: True)

        Raises:
            ImportError: If langfuse package is not installed
        """
        self.logger: logging.Logger = setup_logger(__name__)
        self.enabled: bool = config.get("enabled", True)
        self._client: Optional[Any] = None

        if not self.enabled:
            log_with_context(
                self.logger, "debug", "Langfuse tracing disabled by config"
            )
            return

        if not LANGFUSE_AVAILABLE:
            log_with_context(
                self.logger,
                "warning",
                "langfuse package not installed, tracing disabled. "
                "Install with: pip install langfuse",
            )
            self.enabled = False
            return

        try:
            self._client = Langfuse(
                public_key=config.get("public_key"),
                secret_key=config.get("secret_key"),
                host=config.get("host", "https://cloud.langfuse.com"),
            )
            log_with_context(
                self.logger,
                "info",
                "Langfuse tracer initialized",
                host=config.get("host", "https://cloud.langfuse.com"),
            )
        except Exception as e:
            log_with_context(
                self.logger,
                "warning",
                "Failed to initialize Langfuse, tracing disabled",
                error=str(e),
            )
            self.enabled = False

    def trace_generation(
        self,
        provider: BaseProvider,
        request: GenerationRequest,
        command: str = "commit",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GenerationResponse:
        """Execute and trace a provider generation call.

        Args:
            provider: The AI provider to call
            request: The generation request
            command: Command type for trace name (e.g., "commit", "pr")
            metadata: Additional metadata to attach to the trace

        Returns:
            GenerationResponse from the provider
        """
        if not self.enabled or self._client is None:
            return provider.generate(request)

        generation = None
        try:
            # Build metadata for the trace
            trace_metadata = self._build_trace_metadata(request, command, metadata)
            trace_metadata["provider"] = provider.get_provider_name()

            # Extract project name from repository context for trace identification
            project_name = self._extract_project_name(request)
            trace_name = (
                f"gitai-{command}:{project_name}" if project_name
                else f"gitai-{command}"
            )
            if project_name:
                trace_metadata["project"] = project_name

            # Create generation observation (Langfuse v3 API)
            model_name = request.model or provider.get_default_model() or "unknown"
            generation = self._client.start_observation(
                name=trace_name,
                as_type="generation",
                model=model_name,
                input={
                    "system_prompt": request.system_prompt or "",
                    "user_prompt": request.prompt,
                },
                model_parameters={
                    "temperature": str(request.temperature) if request.temperature else None,
                    "max_tokens": str(request.max_tokens) if request.max_tokens else None,
                },
                metadata=trace_metadata,
            )

            # Execute the actual LLM call
            start_time = time.time()
            response = provider.generate(request)
            latency_ms = (time.time() - start_time) * 1000

            # Record the output
            usage: Dict[str, int] = {}
            if response.tokens_used:
                usage["total"] = response.tokens_used

            generation.update(
                output=response.content,
                usage_details=usage if usage else None,
                metadata={
                    "latency_ms": round(latency_ms, 2),
                    "model_used": response.model_used,
                    "response_metadata": response.metadata or {},
                },
            )
            generation.end()

            log_with_context(
                self.logger,
                "info",
                "Generation traced to Langfuse",
                trace_id=generation.trace_id,
                latency_ms=round(latency_ms, 2),
                model=response.model_used,
            )

            return response

        except Exception as e:
            # If tracing fails, log the error but still return the response
            # from the provider (tracing should never break generation)
            if generation is not None:
                try:
                    generation.update(
                        level="ERROR",
                        status_message=f"Generation failed: {e}",
                    )
                    generation.end()
                except Exception:
                    pass

            log_with_context(
                self.logger,
                "warning",
                "Langfuse tracing error, falling back to untraced call",
                error=str(e),
            )

            # If we haven't gotten a response yet, call the provider directly
            return provider.generate(request)

        finally:
            self._flush_safe()

    def _extract_project_name(self, request: GenerationRequest) -> str:
        """Extract the project/repository name from the request context.

        Looks for repository info in the request context to identify
        which project generated this trace.
        """
        context = request.context or {}
        repository = context.get("repository")
        if repository is not None:
            name = getattr(repository, "name", None)
            if name:
                return str(name)
        return ""

    def _build_trace_metadata(
        self,
        request: GenerationRequest,
        command: str,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build metadata dict for the Langfuse trace.

        Args:
            request: The generation request
            command: Command type
            extra_metadata: Additional metadata to include

        Returns:
            Metadata dictionary
        """
        metadata: Dict[str, Any] = {
            "command": command,
            "prompt_length": len(request.prompt),
        }

        # Extract git context from request if available
        context = request.context or {}
        changes = context.get("changes")
        if changes is not None:
            affected = getattr(changes, "affected_files", None)
            metadata["files_changed"] = len(affected) if affected else 0
            metadata["lines_added"] = getattr(changes, "lines_added", 0)
            metadata["lines_deleted"] = getattr(changes, "lines_deleted", 0)
            scope = getattr(changes, "scope", None)
            if scope:
                metadata["scope"] = scope

        if extra_metadata:
            metadata.update(extra_metadata)

        return metadata

    def _flush_safe(self) -> None:
        """Flush Langfuse client, ignoring errors."""
        if self._client is not None:
            try:
                self._client.flush()
            except Exception:
                pass

    def shutdown(self) -> None:
        """Gracefully shut down the Langfuse client."""
        if self._client is not None:
            try:
                self._client.shutdown()
            except Exception:
                pass
