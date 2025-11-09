"""Provider factory for creating and managing AI providers."""

from typing import Any, Dict, Optional, Type

from gitai.providers.anthropic import AnthropicProvider
from gitai.providers.base import BaseProvider
from gitai.providers.lmstudio import LMStudioProvider
from gitai.providers.ollama import OllamaProvider
from gitai.providers.openai import OpenAIProvider
from gitai.utils.exceptions import ProviderConfigError, ProviderError
from gitai.utils.logger import setup_logger


class ProviderFactory:
    """Factory for creating AI provider instances."""

    _providers: Dict[str, Type[BaseProvider]] = {
        "ollama": OllamaProvider,
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "lmstudio": LMStudioProvider,
    }

    def __init__(self) -> None:
        """Initialize provider factory."""
        self.logger = setup_logger(__name__)

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[BaseProvider]) -> None:
        """Register a new provider.

        Args:
            name: Provider name
            provider_class: Provider class implementing BaseProvider
        """
        cls._providers[name] = provider_class

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    def create_provider(
        self, provider_name: str, config: Dict[str, Any]
    ) -> BaseProvider:
        """Create a provider instance.

        Args:
            provider_name: Name of the provider to create
            config: Provider configuration

        Returns:
            Configured provider instance

        Raises:
            ProviderError: If provider is not available
            ProviderConfigError: If configuration is invalid
        """
        if provider_name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ProviderError(
                f"Provider '{provider_name}' not available. "
                f"Available providers: {available}"
            )

        provider_class = self._providers[provider_name]

        try:
            provider = provider_class(config)
            self.logger.info(f"Created {provider_name} provider")
            return provider
        except Exception as e:
            raise ProviderConfigError(
                f"Failed to create {provider_name} provider: {e}"
            ) from e

    def create_with_fallback(
        self,
        primary_provider: str,
        primary_config: Dict[str, Any],
        fallback_providers: Optional[list[tuple[str, Dict[str, Any]]]] = None,
    ) -> BaseProvider:
        """Create provider with fallback options.

        Args:
            primary_provider: Primary provider name
            primary_config: Primary provider configuration
            fallback_providers: List of (provider_name, config) tuples for fallback

        Returns:
            First available provider instance

        Raises:
            ProviderError: If no providers are available
        """
        # Try primary provider
        try:
            provider = self.create_provider(primary_provider, primary_config)
            if provider.health_check():
                return provider
            else:
                self.logger.warning(
                    f"Primary provider {primary_provider} failed health check"
                )
        except Exception as e:
            self.logger.warning(f"Primary provider {primary_provider} failed: {e}")

        # Try fallback providers
        if fallback_providers:
            for fallback_name, fallback_config in fallback_providers:
                try:
                    provider = self.create_provider(fallback_name, fallback_config)
                    if provider.health_check():
                        self.logger.info(f"Using fallback provider: {fallback_name}")
                        return provider
                    else:
                        self.logger.warning(
                            f"Fallback provider {fallback_name} failed health check"
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Fallback provider {fallback_name} failed: {e}"
                    )

        # No providers available
        raise ProviderError("No healthy providers available")


# Global factory instance
provider_factory = ProviderFactory()
