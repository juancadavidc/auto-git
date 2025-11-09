"""Configuration system and management."""

from .manager import ConfigManager, create_config_manager
from .models import (
    GitAIConfig,
    GitConfig,
    OllamaConfig,
    OpenAIConfig,
    ProjectConfig,
    ProviderConfig,
    TeamConfig,
    TemplateConfig,
    UserConfig,
    create_default_config,
)

__all__ = [
    "GitAIConfig",
    "ProviderConfig",
    "TemplateConfig",
    "GitConfig",
    "UserConfig",
    "TeamConfig",
    "ProjectConfig",
    "OllamaConfig",
    "OpenAIConfig",
    "create_default_config",
    "ConfigManager",
    "create_config_manager",
]
