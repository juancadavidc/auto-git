"""Langfuse integration for LLM observability.

Provides tracing of LLM calls including prompts, responses,
token usage, latency, and metadata for debugging and evaluation.

Supports both single-shot generation and agentic tool-calling loops.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from gitai.providers.base import BaseProvider, GenerationRequest, GenerationResponse
from gitai.utils.logger import log_with_context, setup_logger

try:
    from langfuse import Langfuse

    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class LangfuseAgenticTracer:
    """Traces LLM calls and tool executions to Langfuse.

    Supports two modes:
    1. Single-shot: trace_generation() for backward compatibility
    2. Agentic: start_trace/start_llm_span/start_tool_span/end_trace
       for full loop observability with nested spans.

    Fail-safe: tracing errors NEVER break generation.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.logger: logging.Logger = setup_logger(__name__)
        self.enabled: bool = config.get("enabled", True)
        self._client: Optional[Any] = None
        self._trace: Optional[Any] = None
        self._current_llm_span: Optional[Any] = None
        self._current_tool_span: Optional[Any] = None

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

    # ── Agentic loop tracing ──────────────────────────────────────

    def start_trace(
        self, command: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Start a parent trace for an agentic loop."""
        if not self.enabled or not self._client:
            return

        try:
            self._trace = self._client.start_span(
                name=f"gitai-{command}-agentic",
                metadata=metadata or {},
            )
        except Exception as e:
            log_with_context(
                self.logger, "warning", "Failed to start trace", error=str(e)
            )

    def start_llm_span(
        self,
        iteration: int,
        messages: List[Dict[str, Any]],
    ) -> None:
        """Start a generation span for an LLM call within the loop."""
        if not self.enabled or not self._trace:
            return

        try:
            self._current_llm_span = self._trace.start_observation(
                as_type="generation",
                name=f"llm-call-{iteration}",
                input={"messages_count": len(messages)},
                metadata={"iteration": iteration},
            )
        except Exception as e:
            log_with_context(
                self.logger, "warning", "Failed to start LLM span", error=str(e)
            )
            self._current_llm_span = None

    def end_llm_span(
        self, response: Dict[str, Any], latency_ms: float
    ) -> None:
        """End the current LLM generation span."""
        if not self.enabled or not self._current_llm_span:
            return

        try:
            tool_calls = response.get("tool_calls", [])
            self._current_llm_span.update(
                output={
                    "content": (response.get("content") or "")[:500],
                    "tool_calls_count": len(tool_calls),
                    "tool_calls": [
                        {"name": tc.get("name", ""), "id": tc.get("id", "")}
                        for tc in tool_calls
                    ],
                },
                usage_details={"total": response.get("tokens_used", 0)},
                metadata={
                    "latency_ms": round(latency_ms, 2),
                    "model": response.get("model", "unknown"),
                    "has_tool_calls": bool(tool_calls),
                },
            )
            self._current_llm_span.end()
        except Exception as e:
            log_with_context(
                self.logger, "warning", "Failed to end LLM span", error=str(e)
            )
        finally:
            self._current_llm_span = None

    def start_tool_span(self, tool_call: Any) -> None:
        """Start a span for a tool execution."""
        if not self.enabled or not self._trace:
            return

        try:
            self._current_tool_span = self._trace.start_span(
                name=f"tool-{tool_call.name}",
                input={
                    "tool_name": tool_call.name,
                    "arguments": tool_call.arguments,
                },
            )
        except Exception as e:
            log_with_context(
                self.logger, "warning", "Failed to start tool span", error=str(e)
            )
            self._current_tool_span = None

    def end_tool_span(self, result: Any, latency_ms: float) -> None:
        """End the current tool execution span."""
        if not self.enabled or not self._current_tool_span:
            return

        try:
            self._current_tool_span.update(
                output=result.content[:500],
                metadata={
                    "latency_ms": round(latency_ms, 2),
                    "is_error": result.is_error,
                    "tool_name": result.name,
                },
            )
            self._current_tool_span.end()
        except Exception as e:
            log_with_context(
                self.logger, "warning", "Failed to end tool span", error=str(e)
            )
        finally:
            self._current_tool_span = None

    def end_trace(self) -> None:
        """Finalize the parent trace and flush."""
        if not self.enabled:
            return
        if self._trace is not None:
            try:
                self._trace.end()
            except Exception:
                pass
        self._flush_safe()
        self._trace = None

    # ── Single-shot tracing (backward compatible) ─────────────────

    def trace_generation(
        self,
        provider: BaseProvider,
        request: GenerationRequest,
        command: str = "commit",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GenerationResponse:
        """Execute and trace a single-shot provider generation call."""
        if not self.enabled or self._client is None:
            return provider.generate(request)

        trace = None
        generation = None
        try:
            trace_metadata: Dict[str, Any] = {
                "command": command,
                "prompt_length": len(request.prompt),
            }
            if metadata:
                trace_metadata.update(metadata)

            trace = self._client.start_span(
                name=f"gitai-{command}",
                metadata=trace_metadata,
            )

            model_name = request.model or provider.get_default_model() or "unknown"
            generation = trace.start_observation(
                as_type="generation",
                name=f"{command}-generation",
                model=model_name,
                input={
                    "system_prompt": request.system_prompt or "",
                    "user_prompt": request.prompt,
                },
                model_parameters={
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens,
                },
                metadata={
                    "provider": provider.get_provider_name(),
                    "command": command,
                },
            )

            start_time = time.time()
            response = provider.generate(request)
            latency_ms = (time.time() - start_time) * 1000

            generation.update(
                output=response.content,
                usage_details={"total": response.tokens_used or 0},
                metadata={
                    "latency_ms": round(latency_ms, 2),
                    "model_used": response.model_used,
                },
            )
            generation.end()

            log_with_context(
                self.logger,
                "info",
                "Generation traced to Langfuse",
                trace_id=trace.trace_id,
                latency_ms=round(latency_ms, 2),
            )

            return response

        except Exception as e:
            if generation is not None:
                try:
                    generation.update(
                        output=str(e),
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
            return provider.generate(request)

        finally:
            if trace is not None:
                try:
                    trace.end()
                except Exception:
                    pass
            self._flush_safe()

    # ── Internal helpers ──────────────────────────────────────────

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
