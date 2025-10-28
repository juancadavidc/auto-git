"""Anthropic (Claude) provider implementation."""

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


class AnthropicProvider(BaseProvider):
    """Anthropic provider for generating content using Claude models."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider.

        Args:
            config: Provider configuration containing API key, model, etc.

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        self.logger = setup_logger(__name__)

        # Extract configuration
        self.api_key = config.get("api_key") or os.environ.get("ANTHROPIC_API_KEY")
        self.model = config.get("model", "claude-3-haiku-20240307")
        self.base_url = config.get("base_url", "https://api.anthropic.com/v1")
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
            "AnthropicProvider initialized",
            model=self.model,
            timeout=self.timeout,
        )

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate Anthropic provider configuration.

        Args:
            config: Configuration to validate

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        if not self.api_key:
            raise ProviderConfigError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable or provide api_key in config."
            )

        if self.temperature < 0 or self.temperature > 1:
            raise ProviderConfigError("Temperature must be between 0 and 1")

        if self.timeout <= 0:
            raise ProviderConfigError("Timeout must be positive")

    def health_check(self) -> bool:
        """Check if Anthropic API is available.

        Returns:
            True if Anthropic API is healthy, False otherwise
        """
        try:
            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            }
            
            # Simple test message to check connectivity
            payload = {
                "model": self.model,
                "max_tokens": 10,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ]
            }
            
            response = requests.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=headers,
                timeout=10,
            )
            
            return response.status_code == 200
        except Exception as e:
            log_with_context(
                self.logger, "warning", "Anthropic health check failed", error=str(e)
            )
            return False

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using Anthropic Claude.

        Args:
            request: Generation request with prompt and context

        Returns:
            GenerationResponse with generated content

        Raises:
            ProviderUnavailableError: If Anthropic is not available
            GenerationTimeoutError: If generation times out
            ProviderError: If generation fails
        """
        # Check if Anthropic is available
        if not self.health_check():
            raise ProviderUnavailableError(
                "Anthropic API is not available. Check your API key and internet connection."
            )

        log_with_context(
            self.logger,
            "info",
            "Generating content with Anthropic",
            model=self.model,
            prompt_length=len(request.prompt),
        )

        # Prepare request payload
        system_message = "You are a helpful assistant that generates clear, concise commit messages and PR descriptions based on git changes. Follow the template format provided and focus on the actual changes made."
        
        messages = [
            {
                "role": "user", 
                "content": request.prompt
            }
        ]

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_message,
            "messages": messages,
        }

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                log_with_context(
                    self.logger, "info", "Generating content with Anthropic"
                )

                start_time = time.time()
                response = requests.post(
                    f"{self.base_url}/messages",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                generation_time = time.time() - start_time

                response.raise_for_status()
                result = response.json()

                # Extract generated content
                if "content" not in result or not result["content"]:
                    raise ProviderError("No response from Anthropic")

                # Anthropic returns content as an array of content blocks
                content_blocks = result["content"]
                if not content_blocks or content_blocks[0]["type"] != "text":
                    raise ProviderError("Invalid response format from Anthropic")

                content = content_blocks[0]["text"].strip()
                
                if not content:
                    raise ProviderError("Empty response from Anthropic")

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
                    provider_name="anthropic",
                    metadata={
                        "usage": result.get("usage", {}),
                        "stop_reason": result.get("stop_reason"),
                        "stop_sequence": result.get("stop_sequence"),
                    },
                )

            except requests.exceptions.Timeout:
                if attempt == max_retries - 1:
                    raise GenerationTimeoutError(
                        f"Anthropic request timed out after {self.timeout} seconds"
                    )
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} timed out, retrying...",
                )
                time.sleep(1)

            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise ProviderError(f"Anthropic request failed: {e}")
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
                    raise ProviderError(f"Anthropic generation failed: {e}")
                log_with_context(
                    self.logger,
                    "warning",
                    f"Attempt {attempt + 1} failed: {e}, retrying...",
                )
                time.sleep(1)

        # This should never be reached, but just in case
        raise ProviderError("Unexpected error in Anthropic generation")

    def get_available_models(self) -> list[str]:
        """Get list of available models for Anthropic.
        
        Returns:
            List of model names
        """
        return [
            "claude-3-haiku-20240307",   # Fast and affordable
            "claude-3-sonnet-20240229",  # Balanced performance  
            "claude-3-opus-20240229",    # Most capable
            "claude-3-5-sonnet-20240620", # Latest model
        ]