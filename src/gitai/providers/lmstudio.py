"""LMStudio provider implementation."""

import time
from typing import Any, Dict

import requests

from ..utils.exceptions import (
    GenerationTimeoutError,
    ProviderConfigError,
    ProviderError,
    ProviderUnavailableError,
)
from ..utils.logger import log_with_context, setup_logger
from .base import BaseProvider, GenerationRequest, GenerationResponse


class LMStudioProvider(BaseProvider):
    """LMStudio provider for generating content using local models.

    LMStudio provides an OpenAI-compatible API for running models locally.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize LMStudio provider.

        Args:
            config: Provider configuration containing model, base_url, etc.

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        self.logger = setup_logger(__name__)

        # Extract configuration
        # LMStudio doesn't need API key (it's local)
        self.api_key = config.get("api_key", "lm-studio")  # Dummy key for compatibility
        self.model = config.get("model", "local-model")  # Model loaded in LMStudio
        self.base_url = config.get("base_url", "http://localhost:1234/v1")
        self.timeout = config.get("timeout", 30)
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 1000)

        # Validate configuration
        self.validate_config(config)

        # Call parent constructor after setting attributes
        super().__init__(config)

        # Remove trailing slash from base_url
        self.base_url = self.base_url.rstrip("/")

        log_with_context(
            self.logger,
            "info",
            "LMStudioProvider initialized",
            model=self.model,
            timeout=self.timeout,
        )

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate LMStudio provider configuration.

        Args:
            config: Configuration to validate

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        if self.temperature < 0 or self.temperature > 1:
            raise ProviderConfigError("Temperature must be between 0 and 1")

        if self.timeout <= 0:
            raise ProviderConfigError("Timeout must be positive")

    def health_check(self) -> bool:
        """Check if LMStudio is available.

        Returns:
            True if LMStudio API is healthy, False otherwise
        """
        try:
            headers = {
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{self.base_url}/models",
                headers=headers,
                timeout=10,
            )

            return response.status_code == 200
        except Exception as e:
            log_with_context(
                self.logger, "warning", "LMStudio health check failed", error=str(e)
            )
            return False

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using LMStudio.

        Args:
            request: Generation request with prompt and context

        Returns:
            GenerationResponse with generated content

        Raises:
            ProviderUnavailableError: If LMStudio is not available
            GenerationTimeoutError: If generation times out
            ProviderError: If generation fails
        """
        # Check if LMStudio is available
        if not self.health_check():
            raise ProviderUnavailableError(
                "LMStudio is not available. Make sure LMStudio is running on localhost:1234"
            )

        log_with_context(
            self.logger,
            "info",
            "Generating content with LMStudio",
            model=self.model,
            prompt_length=len(request.prompt),
        )

        # Prepare request payload
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates clear, concise commit messages and PR descriptions based on git changes. Follow the template format provided and focus on the actual changes made.",
            },
            {"role": "user", "content": request.prompt},
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Content-Type": "application/json",
        }

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_with_context(
                    self.logger, "info", "Generating content with LMStudio"
                )

                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                generation_time = time.time() - start_time

                response.raise_for_status()
                result = response.json()

                # Extract generated content
                if "choices" not in result or not result["choices"]:
                    raise ProviderError("No response from LMStudio")

                content = result["choices"][0]["message"]["content"].strip()

                if not content:
                    raise ProviderError("Empty response from LMStudio")

                log_with_context(
                    self.logger,
                    "info",
                    "Content generated successfully",
                    generation_time=generation_time,
                    content_length=len(content),
                )

                return GenerationResponse(
                    content=content,
                    model_used=self.model,
                    metadata={
                        "usage": result.get("usage", {}),
                        "finish_reason": result["choices"][0].get("finish_reason"),
                        "generation_time": generation_time,
                        "provider_name": "lmstudio",
                    },
                )

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise GenerationTimeoutError(
                        f"LMStudio request timed out after {self.timeout} seconds"
                    )
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} timed out, retrying...",
                )
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise ProviderError(f"LMStudio request failed: {e}")
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} request failed: {e}, retrying...",
                )
                time.sleep(1)

            except Exception as e:
                if attempt == max_retries - 1:
                    log_with_context(
                        self.logger, "error", "All generation attempts failed"
                    )
                    raise ProviderError(f"LMStudio generation failed: {e}")
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} failed: {e}, retrying...",
                )
                time.sleep(1)

        # This should never be reached, but just in case
        raise ProviderError("Unexpected error in LMStudio generation")

    def get_available_models(self) -> list[str]:
        """Get list of available models for LMStudio.

        Returns:
            List of model names (generic since it depends on what's loaded)
        """
        return [
            "local-model",  # Default/generic
            "mistral",
            "llama-2",
            "llama-3",
            "codellama",
            "phi-2",
            "gemma",
        ]
