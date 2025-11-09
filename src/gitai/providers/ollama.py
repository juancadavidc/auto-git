"""Ollama provider implementation for local AI content generation."""

import time
from typing import Any, Dict, List, Optional

import requests
from requests.exceptions import ConnectionError, RequestException, Timeout

from gitai.providers.base import BaseProvider, GenerationRequest, GenerationResponse
from gitai.utils.exceptions import (
    GenerationTimeoutError,
    ProviderConfigError,
    ProviderError,
    ProviderUnavailableError,
)
from gitai.utils.logger import log_with_context, setup_logger


class OllamaProvider(BaseProvider):
    """Ollama provider for local AI content generation.

    Integrates with Ollama's HTTP API to generate commit messages and PR descriptions
    using locally running language models.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Ollama provider.

        Args:
            config: Configuration with base_url, model, timeout, etc.
        """
        self.logger = setup_logger(__name__)
        super().__init__(config)

        self.base_url: str = str(config.get("base_url", "http://localhost:11434"))
        self.model: str = str(config.get("model", "llama3.1"))
        self.timeout: int = int(config.get("timeout", 30))
        self.max_retries: int = int(config.get("max_retries", 3))
        self.retry_delay: int = int(config.get("retry_delay", 1))

        # Remove trailing slash from base_url
        self.base_url = self.base_url.rstrip("/")

        log_with_context(
            self.logger,
            "info",
            "OllamaProvider initialized",
            base_url=self.base_url,
            model=self.model,
            timeout=self.timeout,
        )

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate Ollama provider configuration.

        Args:
            config: Configuration to validate

        Raises:
            ProviderConfigError: If configuration is invalid
        """
        # Optional: base_url defaults to localhost
        if "base_url" in config:
            base_url = config["base_url"]
            if not isinstance(base_url, str) or not base_url.startswith(
                ("http://", "https://")
            ):
                raise ProviderConfigError("base_url must be a valid HTTP/HTTPS URL")

        # Optional: model defaults to llama3.1
        if "model" in config and not isinstance(config["model"], str):
            raise ProviderConfigError("model must be a string")

        # Optional: timeout must be positive number
        if "timeout" in config:
            timeout = config["timeout"]
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ProviderConfigError("timeout must be a positive number")

    def health_check(self) -> bool:
        """Check if Ollama is available and responsive.

        Returns:
            True if Ollama is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama.

        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            response.raise_for_status()

            data = response.json()
            models = []

            if "models" in data:
                for model in data["models"]:
                    if "name" in model:
                        models.append(model["name"])

            return models

        except Exception as e:
            self.logger.warning(f"Could not fetch available models: {e}")
            return [self.model]  # Return configured model as fallback

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate content using Ollama.

        Args:
            request: Generation request with prompt and context

        Returns:
            GenerationResponse with generated content

        Raises:
            ProviderUnavailableError: If Ollama is not available
            GenerationTimeoutError: If generation times out
            ProviderError: If generation fails
        """
        # Check if Ollama is available
        if not self.health_check():
            raise ProviderUnavailableError("Ollama is not available or not responding")

        # Prepare the prompt
        final_prompt = self.prepare_prompt(request.prompt, request.context)

        # Use model from request or default
        model = request.model or self.model

        # Prepare request payload
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": final_prompt,
            "stream": False,
        }

        # Add optional parameters
        if request.max_tokens:
            options = payload.get("options", {})
            if not isinstance(options, dict):
                options = {}
            options["num_predict"] = request.max_tokens
            payload["options"] = options

        if request.temperature is not None:
            options = payload.get("options", {})
            if not isinstance(options, dict):
                options = {}
            options["temperature"] = request.temperature
            payload["options"] = options

        # Perform generation with retries
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                log_with_context(
                    self.logger,
                    "info",
                    "Generating content with Ollama",
                    model=model,
                    attempt=attempt + 1,
                    prompt_length=len(final_prompt),
                )

                start_time = time.time()

                response = requests.post(
                    f"{self.base_url}/api/generate", json=payload, timeout=self.timeout
                )

                generation_time = time.time() - start_time

                response.raise_for_status()
                result = response.json()

                if "response" not in result:
                    raise ProviderError("Invalid response format from Ollama")

                content = result["response"].strip()

                if not content:
                    raise ProviderError("Empty response from Ollama")

                log_with_context(
                    self.logger,
                    "info",
                    "Content generated successfully",
                    model=model,
                    generation_time=generation_time,
                    content_length=len(content),
                )

                return GenerationResponse(
                    content=content,
                    model_used=model,
                    tokens_used=result.get("eval_count"),
                    metadata={
                        "generation_time": generation_time,
                        "eval_duration": result.get("eval_duration"),
                        "total_duration": result.get("total_duration"),
                    },
                )

            except Timeout as e:
                last_error = GenerationTimeoutError(
                    f"Ollama request timed out after {self.timeout}s"
                )
                self.logger.warning(f"Attempt {attempt + 1} timed out: {e}")

            except ConnectionError as e:
                last_error = ProviderUnavailableError(
                    f"Could not connect to Ollama: {e}"
                )
                self.logger.warning(f"Attempt {attempt + 1} connection failed: {e}")

            except RequestException as e:
                last_error = ProviderError(f"Ollama request failed: {e}")
                self.logger.warning(f"Attempt {attempt + 1} request failed: {e}")

            except Exception as e:
                last_error = ProviderError(f"Unexpected error: {e}")
                self.logger.error(f"Attempt {attempt + 1} unexpected error: {e}")

            # Wait before retry (except on last attempt)
            if attempt < self.max_retries - 1:
                time.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff

        # All retries failed
        log_with_context(
            self.logger,
            "error",
            "All generation attempts failed",
            model=model,
            attempts=self.max_retries,
        )

        raise last_error or ProviderError("Generation failed after all retries")

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses.

        Returns:
            True - Ollama supports streaming
        """
        return True

    def get_default_model(self) -> str:
        """Get the default model for Ollama.

        Returns:
            Default model name
        """
        return self.model

    def prepare_prompt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Prepare prompt for Ollama with git context.

        Args:
            prompt: Base prompt text
            context: Git analysis context

        Returns:
            Formatted prompt optimized for commit/PR generation
        """
        # Extract key context information
        files_info = ""
        if "files_changed" in context:
            files_changed = context["files_changed"]
            if files_changed:
                files_info = f"\nFiles changed ({len(files_changed)}):\n"
                for file_change in files_changed[:10]:  # Limit to first 10 files
                    files_info += f"- {file_change.get('path', 'unknown')}: "
                    files_info += f"{file_change.get('change_type', 'M')} "
                    files_info += f"(+{file_change.get('lines_added', 0)}, -{file_change.get('lines_removed', 0)})\n"

                if len(files_changed) > 10:
                    files_info += f"... and {len(files_changed) - 10} more files\n"

        # Add statistics
        stats_info = ""
        if "total_additions" in context and "total_deletions" in context:
            stats_info = f"\nStatistics: +{context['total_additions']} -{context['total_deletions']} lines\n"

        # Add change summary if available
        summary_info = ""
        if "change_summary" in context:
            summary_info = f"\nSummary: {context['change_summary']}\n"

        # Add repository context
        repo_info = ""
        if "repository_info" in context:
            repo_info = (
                f"\nRepository: {context['repository_info'].get('name', 'unknown')}\n"
            )

        # Build final prompt
        final_prompt = f"{prompt}\n{repo_info}{summary_info}{stats_info}{files_info}"

        # Add instruction for concise output
        final_prompt += "\nPlease provide a concise, clear response. Avoid unnecessary explanations."

        return final_prompt
