"""Configuration management with 3-tier hierarchy."""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import yaml
from pydantic import ValidationError

from .models import GitAIConfig, create_default_config
from ..utils.exceptions import (
    ConfigurationError,
    InvalidConfigError,
    MissingConfigError,
)


class ConfigManager:
    """Manages configuration loading, merging, and validation with 3-tier hierarchy.

    Configuration hierarchy (highest to lowest precedence):
    1. Project-level (.gitai/config.yaml in git root)
    2. Team-level (team-specific directory)
    3. User-level (~/.config/gitai/config.yaml)
    4. Default configuration
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        team_config_dir: Optional[Path] = None,
        user_config_dir: Optional[Path] = None,
    ):
        """Initialize the configuration manager.

        Args:
            project_root: Root directory of the git repository
            team_config_dir: Directory containing team configuration
            user_config_dir: Directory containing user configuration
        """
        self.project_root = project_root or self._find_git_root()
        self.team_config_dir = team_config_dir
        self.user_config_dir = user_config_dir or self._get_default_user_config_dir()

        self._config_cache: Optional[GitAIConfig] = None

    def _find_git_root(self) -> Optional[Path]:
        """Find the git repository root directory."""
        current = Path.cwd()

        while current != current.parent:
            if (current / ".git").exists():
                return current
            current = current.parent

        return None

    def _get_default_user_config_dir(self) -> Path:
        """Get the default user configuration directory."""
        if os.name == "nt":  # Windows
            config_home = Path(
                os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")
            )
        else:  # Unix-like
            config_home = Path(
                os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            )

        return config_home / "gitai"

    def get_config_paths(self) -> Dict[str, Optional[Path]]:
        """Get all configuration file paths.

        Returns:
            Dictionary mapping config levels to their file paths
        """
        paths = {}

        # Project config
        if self.project_root:
            paths["project"] = self.project_root / ".gitai" / "config.yaml"
        else:
            paths["project"] = None

        # Team config
        if self.team_config_dir:
            paths["team"] = self.team_config_dir / "config.yaml"
        else:
            paths["team"] = None

        # User config
        paths["user"] = self.user_config_dir / "config.yaml"

        return paths

    def load_config(self, force_reload: bool = False) -> GitAIConfig:
        """Load and merge configuration from all sources.

        Args:
            force_reload: Force reloading even if cached

        Returns:
            Merged configuration

        Raises:
            ConfigurationError: If configuration loading/merging fails
        """
        if self._config_cache and not force_reload:
            return self._config_cache

        try:
            # Start with default configuration
            config_data = create_default_config().dict()

            # Load and merge configurations in order (lowest to highest precedence)
            config_paths = self.get_config_paths()

            # User config
            if config_paths["user"] and config_paths["user"].exists():
                user_config = self._load_yaml_file(config_paths["user"])
                config_data = self._merge_configs(config_data, user_config)

            # Team config
            if config_paths["team"] and config_paths["team"].exists():
                team_config = self._load_yaml_file(config_paths["team"])
                config_data = self._merge_configs(config_data, team_config)

            # Project config (highest precedence)
            if config_paths["project"] and config_paths["project"].exists():
                project_config = self._load_yaml_file(config_paths["project"])
                config_data = self._merge_configs(config_data, project_config)

            # Validate and create final configuration
            self._config_cache = GitAIConfig(**config_data)
            return self._config_cache

        except ValidationError as e:
            raise InvalidConfigError(f"Configuration validation failed: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _load_yaml_file(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from a YAML file.

        Args:
            file_path: Path to the YAML file

        Returns:
            Configuration dictionary

        Raises:
            InvalidConfigError: If YAML is invalid
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)
                return content or {}
        except yaml.YAMLError as e:
            raise InvalidConfigError(f"Invalid YAML in {file_path}: {e}")
        except FileNotFoundError:
            return {}
        except Exception as e:
            raise ConfigurationError(f"Failed to read {file_path}: {e}")

    def _merge_configs(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge two configuration dictionaries recursively.

        Args:
            base: Base configuration
            override: Configuration to merge on top

        Returns:
            Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                # Recursively merge nested dictionaries
                result[key] = self._merge_configs(result[key], value)
            else:
                # Override value
                result[key] = value

        return result

    def save_config(self, config: GitAIConfig, level: str = "user") -> None:
        """Save configuration to a specific level.

        Args:
            config: Configuration to save
            level: Configuration level ('user', 'team', or 'project')

        Raises:
            ConfigurationError: If saving fails
        """
        config_paths = self.get_config_paths()
        file_path = config_paths.get(level)

        if not file_path:
            raise ConfigurationError(f"Cannot determine path for {level} configuration")

        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to dictionary and remove None values
            config_dict = self._clean_config_dict(config.dict())

            # Write YAML file
            with open(file_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

            # Clear cache to force reload
            self._config_cache = None

        except Exception as e:
            raise ConfigurationError(f"Failed to save {level} configuration: {e}")

    def _clean_config_dict(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Remove None values and empty containers from config dictionary."""
        cleaned = {}

        for key, value in config_dict.items():
            if value is None:
                continue
            elif isinstance(value, dict):
                cleaned_dict = self._clean_config_dict(value)
                if cleaned_dict:  # Only include non-empty dicts
                    cleaned[key] = cleaned_dict
            elif isinstance(value, list):
                if value:  # Only include non-empty lists
                    cleaned[key] = value
            else:
                cleaned[key] = value

        return cleaned

    def init_user_config(
        self,
        name: Optional[str] = None,
        email: Optional[str] = None,
        provider: str = "ollama",
    ) -> GitAIConfig:
        """Initialize user configuration with basic settings.

        Args:
            name: User's full name
            email: User's email address
            provider: Preferred AI provider

        Returns:
            Created configuration
        """
        config = create_default_config()

        # Set user information
        if name or email:
            from .models import UserConfig

            config.user = UserConfig(
                name=name, email=email, preferred_provider=provider
            )

        # Ensure user config directory exists
        self.user_config_dir.mkdir(parents=True, exist_ok=True)

        # Save configuration
        self.save_config(config, "user")

        return config

    def init_team_config(
        self,
        team_name: str,
        templates_dir: Optional[Path] = None,
        conventions: Optional[Dict[str, str]] = None,
    ) -> GitAIConfig:
        """Initialize team configuration.

        Args:
            team_name: Name of the team
            templates_dir: Team templates directory
            conventions: Team conventions

        Returns:
            Created configuration
        """
        if not self.team_config_dir:
            raise ConfigurationError("Team config directory not specified")

        config = self.load_config()

        # Set team information
        from .models import TeamConfig

        config.team = TeamConfig(
            name=team_name,
            templates_dir=templates_dir,
            conventions=conventions or {},
        )

        # Ensure team config directory exists
        self.team_config_dir.mkdir(parents=True, exist_ok=True)

        # Save configuration
        self.save_config(config, "team")

        return config

    def init_project_config(
        self,
        project_name: str,
        repository_url: Optional[str] = None,
        templates_dir: Optional[Path] = None,
        custom_variables: Optional[Dict[str, Any]] = None,
    ) -> GitAIConfig:
        """Initialize project configuration.

        Args:
            project_name: Name of the project
            repository_url: Repository URL
            templates_dir: Project templates directory
            custom_variables: Project-specific variables

        Returns:
            Created configuration
        """
        if not self.project_root:
            raise ConfigurationError("Not in a git repository")

        config = self.load_config()

        # Set project information
        from .models import ProjectConfig

        config.project = ProjectConfig(
            name=project_name,
            repository_url=repository_url,
            templates_dir=templates_dir,
            custom_variables=custom_variables or {},
        )

        # Save configuration
        self.save_config(config, "project")

        return config

    def get_current_config_info(self) -> Dict[str, Any]:
        """Get information about the current configuration sources.

        Returns:
            Dictionary with configuration source information
        """
        config_paths = self.get_config_paths()
        config = self.load_config()

        info = {
            "paths": {
                level: str(path) if path else None
                for level, path in config_paths.items()
            },
            "exists": {
                level: path.exists() if path else False
                for level, path in config_paths.items()
            },
            "enabled_providers": config.get_enabled_providers(),
            "template_paths": [str(p) for p in config.get_template_search_paths()],
        }

        return info

    def validate_config(self, config_dict: Dict[str, Any]) -> List[str]:
        """Validate a configuration dictionary.

        Args:
            config_dict: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        try:
            GitAIConfig(**config_dict)
            return []
        except ValidationError as e:
            return [str(error) for error in e.errors()]


def create_config_manager(
    project_root: Optional[Path] = None, team_config_dir: Optional[Path] = None
) -> ConfigManager:
    """Create a configuration manager with automatic discovery.

    Args:
        project_root: Root directory of git repository (auto-detected if None)
        team_config_dir: Team configuration directory

    Returns:
        Configured ConfigManager instance
    """
    return ConfigManager(project_root=project_root, team_config_dir=team_config_dir)
