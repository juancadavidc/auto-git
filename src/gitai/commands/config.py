"""Config command implementation."""

from pathlib import Path
from typing import Any, Dict, Optional, cast

import yaml

from gitai.config.manager import ConfigManager, create_config_manager
from gitai.utils.exceptions import ConfigurationError, GitAIError
from gitai.utils.logger import log_with_context, setup_logger
from gitai.utils.validation import create_helpful_error_message, validate_team_name


def handle_config(
    init_global: bool,
    team_name: Optional[str],
    show_config: bool,
    set_provider: Optional[str] = None,
    verbose: bool = False,
    config_path: Optional[Path] = None,
) -> Optional[str]:
    """Handle config command execution.

    Args:
        init_global: Initialize global configuration
        team_name: Team name for team config
        show_config: Show current configuration
        set_provider: Set the preferred AI provider
        verbose: Enable verbose logging
        config_path: Optional config file path

    Returns:
        Configuration output or status message

    Raises:
        GitAIError: If config operation fails
    """
    try:
        # Validate inputs
        if team_name:
            team_name = validate_team_name(team_name)

        config_manager = create_config_manager()

        if show_config:
            return _show_current_config(config_manager, verbose)

        elif init_global:
            return _init_global_config(config_manager, verbose)

        elif team_name:
            return _init_team_config(config_manager, team_name, verbose)

        elif set_provider:
            return _set_provider(config_manager, set_provider, verbose)

        else:
            return """GitAI Configuration

Available commands:
  gitai config --global                  # Initialize global user config
  gitai config --team <name>             # Initialize team config
  gitai config --show                    # Show current configuration
  gitai config --set-provider <name>     # Set preferred AI provider

For more help: gitai config --help"""

    except (GitAIError, ConfigurationError):
        # Re-raise our own exceptions as-is
        raise
    except Exception as e:
        # Wrap unexpected errors with helpful context
        error_message = create_helpful_error_message(
            e, "Configuration operation failed"
        )
        raise GitAIError(error_message) from e


def _show_current_config(config_manager: ConfigManager, verbose: bool) -> str:
    """Show current configuration."""
    try:
        # Get configuration info
        config_info = config_manager.get_current_config_info()
        config = config_manager.load_config()

        # Build output
        output_lines = ["Current Configuration:"]
        output_lines.append("")

        # Configuration sources
        output_lines.append("Configuration Sources:")
        for level, path in config_info["paths"].items():
            exists_marker = "✓" if config_info["exists"][level] else "✗"
            output_lines.append(f"  {level:8} {exists_marker} {path or 'N/A'}")
        output_lines.append("")

        # Providers
        output_lines.append("Providers:")
        for provider_name in config_info["enabled_providers"]:
            try:
                provider_config_dict = config.get_provider_config(provider_name)
                output_lines.append(f"  {provider_name}:")
                for key, value in provider_config_dict.items():
                    output_lines.append(f"    {key}: {value}")
            except Exception as e:
                output_lines.append(f"  {provider_name}: Error loading config - {e}")
        output_lines.append("")

        # Templates
        output_lines.append("Templates:")
        output_lines.append(
            f"  Default commit: {config.templates.default_commit_template}"
        )
        output_lines.append(f"  Default PR: {config.templates.default_pr_template}")
        output_lines.append("")

        # Template search paths
        if verbose:
            output_lines.append("Template Search Paths:")
            for path in config_info["template_paths"]:
                output_lines.append(f"  {path}")
            output_lines.append("")

        # User info
        if config.user:
            output_lines.append("User Information:")
            if config.user.name:
                output_lines.append(f"  Name: {config.user.name}")
            if config.user.email:
                output_lines.append(f"  Email: {config.user.email}")
            if config.user.preferred_provider:
                output_lines.append(
                    f"  Preferred Provider: {config.user.preferred_provider}"
                )

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error loading configuration: {e}"


def _init_global_config(config_manager: ConfigManager, verbose: bool) -> str:
    """Initialize global configuration."""
    logger = setup_logger(__name__)

    log_with_context(logger, "info", "Initializing global config")

    try:
        # Check if config already exists
        config_paths = config_manager.get_config_paths()
        user_config_path = config_paths["user"]

        if user_config_path and user_config_path.exists():
            return f"Global configuration already exists at {user_config_path}"

        # Initialize with defaults
        config_manager.init_user_config()

        log_with_context(
            logger, "info", "Global config created", config_path=str(user_config_path)
        )

        return f"""Global configuration initialized successfully!

Configuration file: {user_config_path}

You can now:
1. Edit the configuration file to customize settings
2. Use 'gitai config --show' to view current configuration
3. Use 'gitai config --team <name>' to set up team configuration

Default provider: ollama (localhost:11434)
Default templates: conventional (commit), github (PR)"""

    except Exception as e:
        raise ConfigurationError(f"Failed to initialize global config: {e}")


def _init_team_config(
    config_manager: ConfigManager, team_name: str, verbose: bool
) -> str:
    """Initialize team configuration."""
    logger = setup_logger(__name__)

    log_with_context(logger, "info", "Initializing team config", team_name=team_name)

    try:
        # Set up team config directory
        team_config_dir = config_manager.user_config_dir / "teams" / team_name
        config_manager.team_config_dir = team_config_dir

        # Check if team config already exists
        team_config_path = team_config_dir / "config.yaml"
        if team_config_path.exists():
            return f"Team configuration for '{team_name}' already exists at {team_config_path}"

        # Initialize team configuration
        config_manager.init_team_config(team_name)

        # Create team templates directory
        templates_dir = team_config_dir / "templates"
        templates_dir.mkdir(parents=True, exist_ok=True)

        # Create sample team commit template
        commit_template_dir = templates_dir / "commit"
        commit_template_dir.mkdir(exist_ok=True)

        sample_template = f"""{'{# description: Team-specific conventional commit template #}'}
{'{# variables: type, scope, description, body #}'}
{{{{ type }}}}({{{{ scope or '{team_name}' }}}}): {{{{ description }}}}

{{% if body %}}
{{{{ body }}}}
{{% endif %}}

{{% if breaking_changes %}}
BREAKING CHANGE: {{{{ breaking_changes }}}}
{{% endif %}}"""

        (commit_template_dir / f"{team_name}.j2").write_text(sample_template)

        log_with_context(
            logger,
            "info",
            "Team config created",
            team_name=team_name,
            config_path=str(team_config_path),
        )

        return f"""Team configuration for '{team_name}' initialized successfully!

Configuration file: {team_config_path}
Templates directory: {templates_dir}

Created sample template: {commit_template_dir / f'{team_name}.j2'}

You can now:
1. Edit the team configuration file
2. Add custom templates to the templates directory
3. Share the team configuration with team members
4. Use templates with: gitai commit -t {team_name}

Team members should copy the team configuration to their local GitAI config."""

    except Exception as e:
        raise ConfigurationError(f"Failed to initialize team config: {e}")


def _set_provider(
    config_manager: ConfigManager, provider_name: str, verbose: bool
) -> str:
    """Set the preferred AI provider.

    Args:
        config_manager: Configuration manager instance
        provider_name: Name of the provider to set (anthropic, openai, ollama)
        verbose: Enable verbose logging

    Returns:
        Success message

    Raises:
        ConfigurationError: If setting provider fails
    """
    logger = setup_logger(__name__)

    log_with_context(logger, "info", "Setting provider", provider_name=provider_name)

    try:
        # Get config paths
        config_paths = config_manager.get_config_paths()
        user_config_path = config_paths["user"]

        if not user_config_path or not user_config_path.exists():
            return f"""Global configuration does not exist yet.

Please initialize it first with:
  gitai config --global

Then you can set the provider with:
  gitai config --set-provider {provider_name}"""

        # Load current configuration from YAML file directly
        with open(user_config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        # Update provider priorities
        if "providers" not in config_data:
            config_data["providers"] = {}

        # Get all provider names
        all_providers = ["anthropic", "openai", "ollama", "lmstudio"]

        # Set priorities: selected provider gets 1, others get higher numbers
        for i, provider in enumerate(all_providers):
            if provider == provider_name:
                priority = 1
            else:
                # Other providers get priority 2, 3, etc.
                priority = (
                    2 + all_providers.index(provider)
                    if provider != provider_name
                    else 2
                )

            if provider not in config_data["providers"]:
                config_data["providers"][provider] = {}

            config_data["providers"][provider]["name"] = provider
            config_data["providers"][provider]["enabled"] = True
            config_data["providers"][provider]["priority"] = priority

        # Reorder providers dict by priority
        config_data["providers"] = dict(
            sorted(
                config_data["providers"].items(),
                key=lambda item: cast(Dict[str, Any], item[1]).get("priority", 999),
            )
        )

        # Write back to file
        with open(user_config_path, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        log_with_context(
            logger,
            "info",
            "Provider set successfully",
            provider=provider_name,
            config_path=str(user_config_path),
        )

        return f"""Provider set to '{provider_name}' successfully!

Configuration file: {user_config_path}

Current provider priority:
  1. {provider_name} (primary)

Use 'gitai config --show' to view full configuration."""

    except Exception as e:
        raise ConfigurationError(f"Failed to set provider: {e}")
