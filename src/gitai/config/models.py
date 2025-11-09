"""Configuration data models using Pydantic."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class ProviderConfig(BaseModel):
    """Configuration for an AI provider."""

    name: str = Field(..., description="Provider name (e.g., 'ollama', 'openai')")
    enabled: bool = Field(default=True, description="Whether this provider is enabled")
    priority: int = Field(
        default=1, description="Provider priority (higher = preferred)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific configuration"
    )

    class Config:
        extra = "allow"


class OllamaConfig(BaseModel):
    """Ollama-specific configuration."""

    base_url: str = Field(
        default="http://localhost:11434", description="Ollama server base URL"
    )
    model: str = Field(default="qwen2.5:7b", description="Model name to use")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate"
    )

    @field_validator("temperature")  # type: ignore[misc]
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    @field_validator("timeout")  # type: ignore[misc]
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class OpenAIConfig(BaseModel):
    """OpenAI-specific configuration."""

    api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model: str = Field(default="gpt-3.5-turbo", description="Model name to use")
    base_url: str = Field(
        default="https://api.openai.com/v1", description="OpenAI API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(
        default=1000, description="Maximum tokens to generate"
    )

    @field_validator("temperature")  # type: ignore[misc]
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    @field_validator("timeout")  # type: ignore[misc]
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class AnthropicConfig(BaseModel):
    """Anthropic (Claude) specific configuration."""

    api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    model: str = Field(
        default="claude-3-haiku-20240307", description="Model name to use"
    )
    base_url: str = Field(
        default="https://api.anthropic.com/v1", description="Anthropic API base URL"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(
        default=1000, description="Maximum tokens to generate"
    )

    @field_validator("temperature")  # type: ignore[misc]
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    @field_validator("timeout")  # type: ignore[misc]
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class LMStudioConfig(BaseModel):
    """LMStudio-specific configuration."""

    base_url: str = Field(
        default="http://localhost:1234/v1", description="LMStudio server base URL"
    )
    model: str = Field(default="local-model", description="Model name to use")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    temperature: float = Field(default=0.7, description="Generation temperature")
    max_tokens: Optional[int] = Field(
        default=1000, description="Maximum tokens to generate"
    )

    @field_validator("temperature")  # type: ignore[misc]
    def validate_temperature(cls, v: float) -> float:
        if not 0 <= v <= 1:
            raise ValueError("Temperature must be between 0 and 1")
        return v

    @field_validator("timeout")  # type: ignore[misc]
    def validate_timeout(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v


class TemplateConfig(BaseModel):
    """Template configuration."""

    default_commit_template: str = Field(
        default="conventional", description="Default commit message template"
    )
    default_pr_template: str = Field(
        default="github", description="Default PR description template"
    )
    search_paths: List[Path] = Field(
        default_factory=list, description="Template search paths"
    )
    variables: Dict[str, Any] = Field(
        default_factory=dict, description="Global template variables"
    )

    class Config:
        json_encoders = {Path: str}


class GitConfig(BaseModel):
    """Git-related configuration."""

    default_branch: str = Field(
        default="main", description="Default base branch for PRs"
    )
    ignore_patterns: List[str] = Field(
        default_factory=lambda: ["*.log", "*.tmp", ".env*"],
        description="Patterns for files to ignore in analysis",
    )
    max_diff_size: int = Field(
        default=10000, description="Maximum diff size to analyze (lines)"
    )
    include_binary_files: bool = Field(
        default=False, description="Whether to include binary files in analysis"
    )


class UserConfig(BaseModel):
    """User-specific configuration."""

    name: Optional[str] = Field(default=None, description="User's full name")
    email: Optional[str] = Field(default=None, description="User's email address")
    preferred_provider: Optional[str] = Field(
        default=None, description="Preferred AI provider"
    )
    templates_dir: Optional[Path] = Field(
        default=None, description="User's templates directory"
    )

    class Config:
        json_encoders = {Path: str}


class TeamConfig(BaseModel):
    """Team-shared configuration."""

    name: str = Field(..., description="Team name")
    templates_dir: Optional[Path] = Field(
        default=None, description="Team's templates directory"
    )
    conventions: Dict[str, str] = Field(
        default_factory=dict,
        description="Team conventions (e.g., commit format, PR format)",
    )
    required_fields: List[str] = Field(
        default_factory=list, description="Required fields in generated content"
    )

    class Config:
        json_encoders = {Path: str}


class ProjectConfig(BaseModel):
    """Project-specific configuration."""

    name: str = Field(..., description="Project name")
    repository_url: Optional[str] = Field(default=None, description="Repository URL")
    templates_dir: Optional[Path] = Field(
        default=None, description="Project's templates directory"
    )
    custom_variables: Dict[str, Any] = Field(
        default_factory=dict, description="Project-specific template variables"
    )

    class Config:
        json_encoders = {Path: str}


class GitAIConfig(BaseModel):
    """Main GitAI configuration model with all sections."""

    # Core sections
    providers: Dict[str, ProviderConfig] = Field(
        default_factory=dict, description="AI provider configurations"
    )
    templates: TemplateConfig = Field(
        default_factory=TemplateConfig, description="Template configuration"
    )
    git: GitConfig = Field(
        default_factory=GitConfig, description="Git-related configuration"
    )

    # Context-specific sections (may not all be present)
    user: Optional[UserConfig] = Field(default=None, description="User configuration")
    team: Optional[TeamConfig] = Field(default=None, description="Team configuration")
    project: Optional[ProjectConfig] = Field(
        default=None, description="Project configuration"
    )

    # Provider-specific configs
    ollama: Optional[OllamaConfig] = Field(
        default=None, description="Ollama configuration"
    )
    openai: Optional[OpenAIConfig] = Field(
        default=None, description="OpenAI configuration"
    )
    anthropic: Optional[AnthropicConfig] = Field(
        default=None, description="Anthropic configuration"
    )
    lmstudio: Optional[LMStudioConfig] = Field(
        default=None, description="LMStudio configuration"
    )

    @model_validator(mode="after")  # type: ignore[misc]
    def validate_config(self) -> "GitAIConfig":
        """Validate the overall configuration."""
        providers = self.providers

        # Ensure at least one provider is enabled
        enabled_providers = [p for p in providers.values() if p.enabled]
        if not enabled_providers:
            raise ValueError("At least one provider must be enabled")

        # Validate provider-specific configs exist for enabled providers
        for provider_name, provider_config in providers.items():
            if provider_config.enabled:
                if provider_name == "ollama" and not self.ollama:
                    self.ollama = OllamaConfig()
                elif provider_name == "openai" and not self.openai:
                    self.openai = OpenAIConfig()
                elif provider_name == "anthropic" and not self.anthropic:
                    self.anthropic = AnthropicConfig()
                elif provider_name == "lmstudio" and not self.lmstudio:
                    self.lmstudio = LMStudioConfig()

        return self

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """Get configuration for a specific provider.

        Args:
            provider_name: Name of the provider

        Returns:
            Provider configuration dictionary
        """
        provider = self.providers.get(provider_name)
        if not provider:
            raise ValueError(f"Provider '{provider_name}' not configured")

        # Merge general config with provider-specific config
        config = provider.config.copy()

        if provider_name == "ollama" and self.ollama:
            config.update(self.ollama.dict())
        elif provider_name == "openai" and self.openai:
            config.update(self.openai.dict())
        elif provider_name == "anthropic" and self.anthropic:
            config.update(self.anthropic.dict())
        elif provider_name == "lmstudio" and self.lmstudio:
            config.update(self.lmstudio.dict())

        return config

    def get_enabled_providers(self) -> List[str]:
        """Get list of enabled provider names, sorted by priority (1 = highest)."""
        enabled = [
            (name, config.priority)
            for name, config in self.providers.items()
            if config.enabled
        ]
        return [name for name, _ in sorted(enabled, key=lambda x: x[1])]

    def get_template_search_paths(self) -> List[Path]:
        """Get all template search paths in order of precedence."""
        paths = []

        # Project templates have highest precedence
        if self.project and self.project.templates_dir:
            paths.append(self.project.templates_dir)

        # Then team templates
        if self.team and self.team.templates_dir:
            paths.append(self.team.templates_dir)

        # Then user templates
        if self.user and self.user.templates_dir:
            paths.append(self.user.templates_dir)

        # Finally configured search paths
        paths.extend(self.templates.search_paths)

        return paths

    def get_user_templates_dir(self) -> Optional[Path]:
        """Get user templates directory."""
        if self.user and self.user.templates_dir:
            return self.user.templates_dir
        return None

    def get_team_templates_dir(self) -> Optional[Path]:
        """Get team templates directory."""
        if self.team and self.team.templates_dir:
            return self.team.templates_dir
        return None

    def get_project_templates_dir(self) -> Optional[Path]:
        """Get project templates directory."""
        if self.project and self.project.templates_dir:
            return self.project.templates_dir
        return None


def create_default_config() -> GitAIConfig:
    """Create a default configuration."""
    return GitAIConfig(
        providers={"ollama": ProviderConfig(name="ollama", enabled=True, priority=1)},
        ollama=OllamaConfig(),
    )
