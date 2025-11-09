"""Base provider interface for AI content generation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from gitai.utils.exceptions import ProviderConfigError


@dataclass
class GenerationRequest:
    """Request for AI content generation.

    Attributes:
        prompt: The prompt text for the AI
        context: Additional context data
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        model: Specific model to use (provider-dependent)
    """

    prompt: str
    context: Dict[str, Any]
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
