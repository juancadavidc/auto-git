"""Template management and rendering."""

from .context import (
    ContextBuilder,
    EnhancedDiffAnalysis,
    EnhancedFileChange,
    RepositoryInfo,
    UserInfo,
    create_context_builder,
)
from .manager import TemplateInfo, TemplateManager, create_template_manager

__all__ = [
    "TemplateManager",
    "TemplateInfo",
    "create_template_manager",
    "ContextBuilder",
    "RepositoryInfo",
    "UserInfo",
    "EnhancedFileChange",
    "EnhancedDiffAnalysis",
    "create_context_builder",
]
