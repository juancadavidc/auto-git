"""OpenAI provider implementation."""

import os
import time
from typing import Dict, Any, Optional

import requests

from .base import BaseProvider, GenerationRequest, GenerationResponse
from ..utils.exceptions import (
    ProviderUnavailableError,
    GenerationTimeoutError,
    ProviderError,
    ProviderConfigError,
)
from ..utils.logger import setup_logger, log_with_context


class OpenAIProvider(BaseProvider):
    """OpenAI provider for generating content using GPT models."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider.

        Args:
            config: Provider configuration containing API key, model, etc.

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        self.logger = setup_logger(__name__)

        # Extract configuration
        self.api_key = config.get("api_key") or os.environ.get("OPENAI_API_KEY")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
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
            "OpenAIProvider initialized",
            model=self.model,
            timeout=self.timeout,
        )

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate OpenAI provider configuration.

        Args:
            config: Configuration to validate

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        if not self.api_key:
            raise ProviderConfigError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or provide api_key in config."
            )

        if self.temperature < 0 or self.temperature > 1:
            raise ProviderConfigError("Temperature must be between 0 and 1")

        if self.timeout <= 0:
            raise ProviderConfigError("Timeout must be positive")

    def health_check(self) -> bool:
        """Check if OpenAI API is available.

        Returns:
            True if OpenAI API is healthy, False otherwise
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
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
                self.logger, "warning", "OpenAI health check failed", error=str(e)
            )
            return False

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using OpenAI.

        Args:
            request: Generation request with prompt and context

        Returns:
            GenerationResponse with generated content

        Raises:
            ProviderUnavailableError: If OpenAI is not available
            GenerationTimeoutError: If generation times out
            ProviderError: If generation fails
        """
        # Check if OpenAI is available
        if not self.health_check():
            raise ProviderUnavailableError(
                "OpenAI API is not available. Check your API key and internet connection."
            )

        log_with_context(
            self.logger,
            "info",
            "Generating content with OpenAI",
            model=self.model,
            prompt_length=len(request.prompt),
        )

        # Prepare request payload
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates clear, concise commit messages and PR descriptions based on git changes. Follow the template format provided and focus on the actual changes made."
            },
            {
                "role": "user", 
                "content": request.prompt
            }
        ]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_with_context(
                    self.logger, "info", "Generating content with OpenAI"
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
                    raise ProviderError("No response from OpenAI")

                content = result["choices"][0]["message"]["content"].strip()
                
                if not content:
                    raise ProviderError("Empty response from OpenAI")

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
                    generation_time=generation_time,
                    provider_name="openai",
                    metadata={
                        "usage": result.get("usage", {}),
                        "finish_reason": result["choices"][0].get("finish_reason"),
                    },
                )

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise GenerationTimeoutError(
                        f"OpenAI request timed out after {self.timeout} seconds"
                    )
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} timed out, retrying...",
                )
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise ProviderError(f"OpenAI request failed: {e}")
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
                    raise ProviderError(f"OpenAI generation failed: {e}")
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} failed: {e}, retrying...",
                )
                time.sleep(1)

        # This should never be reached, but just in case
        raise ProviderError("Unexpected error in OpenAI generation")

    def get_available_models(self) -> list[str]:
        """Get list of available models for OpenAI.
        
        Returns:
            List of model names
        """
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k", 
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini",
        ]