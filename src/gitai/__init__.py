"""GitAI - AI-powered commit and PR description generation.

GitAI automates the creation of commit messages and pull request descriptions
using AI analysis of git changes and customizable templates.
"""

__version__ = "0.1.0"
__author__ = "GitAI Contributors"
__email__ = "contributors@gitai.dev"

# Lazy imports to avoid requiring dependencies at package level
__all__ = [
    "GitAnalyzer",
    "BaseProvider",
    "OllamaProvider",
]


def __getattr__(name: str):
    """Lazy import of modules to avoid dependency issues."""
    if name == "GitAnalyzer":
        from gitai.core.git_analyzer import GitAnalyzer

        return GitAnalyzer
    elif name == "BaseProvider":
        from gitai.providers.base import BaseProvider

        return BaseProvider
    elif name == "OllamaProvider":
        from gitai.providers.ollama import OllamaProvider

        return OllamaProvider
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
