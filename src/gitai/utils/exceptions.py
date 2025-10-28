"""Custom exception classes for GitAI."""


class GitAIError(Exception):
    """Base exception for GitAI errors."""

    pass


class GitAnalysisError(GitAIError):
    """Raised when git analysis fails."""

    pass


class NoStagedChangesError(GitAnalysisError):
    """Raised when no staged changes are found."""

    pass


class InvalidRepositoryError(GitAnalysisError):
    """Raised when the current directory is not a valid git repository."""

    pass


class GitOperationError(GitAnalysisError):
    """Raised when git operations fail."""

    pass


class TemplateError(GitAIError):
    """Base exception for template-related errors."""

    pass


class TemplateNotFoundError(TemplateError):
    """Raised when a template cannot be found."""

    pass


class TemplateRenderError(TemplateError):
    """Raised when template rendering fails."""

    pass


class TemplateValidationError(TemplateError):
    """Raised when template validation fails."""

    pass


class ProviderError(GitAIError):
    """Base exception for AI provider errors."""

    pass


class ProviderUnavailableError(ProviderError):
    """Raised when an AI provider is unavailable."""

    pass


class ProviderConfigError(ProviderError):
    """Raised when provider configuration is invalid."""

    pass


class GenerationTimeoutError(ProviderError):
    """Raised when content generation times out."""

    pass


class ConfigurationError(GitAIError):
    """Base exception for configuration errors."""

    pass


class InvalidConfigError(ConfigurationError):
    """Raised when configuration is invalid."""

    pass


class MissingConfigError(ConfigurationError):
    """Raised when required configuration is missing."""

    pass


class ConfigValidationError(ConfigurationError):
    """Raised when configuration validation fails."""

    pass
