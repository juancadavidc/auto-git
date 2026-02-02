"""Base provider interface for AI content generation."""

import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from gitai.utils.exceptions import (
    GenerationTimeoutError,
    ProviderConfigError,
    ProviderError,
    ProviderUnavailableError,
)


@dataclass
class GenerationRequest:
    """Request for AI content generation.

    Attributes:
        prompt: The prompt text for the AI
        context: Additional context data
        system_prompt: System-level prompt for the AI (command-specific)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        model: Specific model to use (provider-dependent)
    """

    prompt: str
    context: Dict[str, Any]
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    model: Optional[str] = None


@dataclass
class GenerationResponse:
    """Response from AI content generation.

    Attributes:
        content: Generated content
        model_used: Model that generated the content
        tokens_used: Number of tokens consumed
        metadata: Additional response metadata
    """

    content: str
    model_used: str
    tokens_used: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for AI providers.

    All AI providers must implement this interface to be used with GitAI.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration.

        Args:
            config: Provider-specific configuration

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        self.config = config
        self.validate_config(config)

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using the AI provider.

        Args:
            request: Generation request with prompt and context

        Returns:
            GenerationResponse with the generated content

        Raises:
            ProviderError: If generation fails
        """
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate provider configuration.

        Args:
            config: Configuration to validate

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if the provider is available and healthy.

        Returns:
            True if provider is available, False otherwise
        """
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available models for this provider.

        Returns:
            List of model names
        """
        pass

    def get_provider_name(self) -> str:
        """Get the name of this provider.

        Returns:
            Provider name
        """
        return self.__class__.__name__.replace("Provider", "").lower()

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses.

        Returns:
            True if streaming is supported, False otherwise
        """
        return False

    def get_default_model(self) -> Optional[str]:
        """Get the default model for this provider.

        Returns:
            Default model name or None
        """
        return self.config.get("default_model")

    def get_max_tokens(self) -> Optional[int]:
        """Get maximum tokens supported by this provider.

        Returns:
            Maximum tokens or None if unlimited
        """
        return self.config.get("max_tokens")

    def prepare_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Prepare the final prompt by combining prompt and context.

        This method can be overridden by providers to customize prompt formatting.

        Args:
            prompt: Base prompt text
            context: Context data to include

        Returns:
            Final formatted prompt
        """
        # Default implementation: simple concatenation
        context_str = ""
        if context:
            context_str = "\n\nContext:\n"
            for key, value in context.items():
                if isinstance(value, (str, int, float, bool)):
                    context_str += f"- {key}: {value}\n"
                elif isinstance(value, (list, dict)):
                    context_str += f"- {key}: {str(value)[:200]}{'...' if len(str(value)) > 200 else ''}\n"

        return prompt + context_str

    def _validate_required_config(
        self, config: Dict[str, Any], required_keys: list[str]
    ) -> None:
        """Helper to validate required configuration keys.

        Args:
            config: Configuration to validate
            required_keys: List of required keys

        Raises:
            ProviderConfigError: If required keys are missing
        """
        missing_keys = [key for key in required_keys if key not in config]
        if missing_keys:
            raise ProviderConfigError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )

    def _validate_config_types(
        self, config: Dict[str, Any], expected_types: Dict[str, type]
    ) -> None:
        """Helper to validate configuration value types.

        Args:
            config: Configuration to validate
            expected_types: Dictionary mapping keys to expected types

        Raises:
            ProviderConfigError: If types don't match
        """
        for key, expected_type in expected_types.items():
            if key in config and not isinstance(config[key], expected_type):
                raise ProviderConfigError(
                    f"Configuration key '{key}' must be of type {expected_type.__name__}, "
                    f"got {type(config[key]).__name__}"
                )

    def supports_tool_calling(self) -> bool:
        """Check if provider supports tool-calling (agentic mode).

        Returns:
            True if provider supports chat_with_tools(), False otherwise.
        """
        return False

    def chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Chat with tool-calling support.

        Args:
            messages: Conversation history in OpenAI format.
            tools: Tool definitions in OpenAI function-calling format.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.

        Returns:
            Dict with keys: content, tool_calls, model, tokens_used, metadata.

        Raises:
            NotImplementedError: If provider does not support tool calling.
        """
        raise NotImplementedError(
            f"{self.get_provider_name()} does not support tool calling. "
            "Use a provider that supports it (ollama, openai, lmstudio)."
        )

    def _openai_compatible_chat_with_tools(
        self,
        endpoint_url: str,
        headers: Dict[str, str],
        model: str,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: int = 120,
        max_retries: int = 3,
        retry_delay: int = 1,
    ) -> Dict[str, Any]:
        """Shared implementation for OpenAI-compatible chat with tools.

        Works with OpenAI, Ollama (/v1/chat/completions), and LMStudio.

        Args:
            endpoint_url: Full URL to the chat completions endpoint.
            headers: HTTP headers (auth, content-type).
            model: Model name.
            messages: Conversation messages in OpenAI format.
            tools: Tool definitions in OpenAI format.
            temperature: Sampling temperature.
            max_tokens: Max tokens.
            timeout: Request timeout in seconds.
            max_retries: Number of retries.
            retry_delay: Base delay between retries.

        Returns:
            Dict with: content, tool_calls (list of dicts with id/name/arguments),
            model, tokens_used, metadata.
        """
        payload: Dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        if tools:
            payload["tools"] = tools

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        last_error: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                start_time = time.time()

                response = requests.post(
                    endpoint_url,
                    headers=headers,
                    json=payload,
                    timeout=timeout,
                )
                response.raise_for_status()

                latency_ms = (time.time() - start_time) * 1000
                result = response.json()

                message = result.get("choices", [{}])[0].get("message", {})
                content = message.get("content") or ""

                # Parse tool calls
                tool_calls = []
                raw_tool_calls = message.get("tool_calls") or []
                for i, tc in enumerate(raw_tool_calls):
                    func = tc.get("function", {})
                    args_raw = func.get("arguments", "{}")
                    if isinstance(args_raw, str):
                        try:
                            args = json.loads(args_raw)
                        except json.JSONDecodeError:
                            args = {}
                    else:
                        args = args_raw

                    tool_calls.append({
                        "id": tc.get("id", f"call_{i}"),
                        "name": func.get("name", ""),
                        "arguments": args,
                    })

                # Token usage
                usage = result.get("usage", {})
                tokens_used = usage.get("total_tokens")

                return {
                    "content": content,
                    "tool_calls": tool_calls,
                    "model": result.get("model", model),
                    "tokens_used": tokens_used,
                    "metadata": {
                        "latency_ms": round(latency_ms, 2),
                        "finish_reason": result.get("choices", [{}])[0].get(
                            "finish_reason"
                        ),
                        "usage": usage,
                    },
                }

            except Timeout:
                last_error = GenerationTimeoutError(
                    f"Request timed out after {timeout}s"
                )
            except ConnectionError as e:
                last_error = ProviderUnavailableError(
                    f"Could not connect: {e}"
                )
            except RequestException as e:
                last_error = ProviderError(f"Request failed: {e}")
            except Exception as e:
                last_error = ProviderError(f"Unexpected error: {e}")

            if attempt < max_retries - 1:
                time.sleep(retry_delay * (attempt + 1))

        raise last_error or ProviderError(
            "chat_with_tools failed after all retries"
        )
