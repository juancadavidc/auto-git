"""Template management and rendering."""

from .manager import TemplateManager, TemplateInfo, create_template_manager
from .context import (
    ContextBuilder,
    RepositoryInfo,
    UserInfo,
    EnhancedFileChange,
    EnhancedDiffAnalysis,
    create_context_builder,
)

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
