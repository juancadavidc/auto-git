"""Configuration system and management."""

from .models import (
    GitAIConfig,
    ProviderConfig,
    TemplateConfig,
    GitConfig,
    UserConfig,
    TeamConfig,
    ProjectConfig,
    OllamaConfig,
    OpenAIConfig,
    create_default_config,
)
from .manager import ConfigManager, create_config_manager

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
