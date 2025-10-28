"""Templates command implementation."""

from pathlib import Path
from typing import Optional

from gitai.utils.exceptions import GitAIError
from gitai.utils.logger import setup_logger, log_with_context
from gitai.utils.validation import (
    validate_template_name,
    create_helpful_error_message,
)


def handle_templates(
    list_templates: bool,
    show_template: Optional[str],
    template_type: str,
    verbose: bool = False,
    config_path: Optional[Path] = None,
) -> Optional[str]:
    """Handle templates command execution.

    Args:
        list_templates: List available templates
        show_template: Show specific template content
        template_type: Type of templates (commit or pr)
        verbose: Enable verbose logging
        config_path: Optional config file path

    Returns:
        Template information or content

    Raises:
        GitAIError: If template operation fails
    """
    logger = setup_logger(__name__)

    try:
        # Validate inputs
        if show_template:
            show_template = validate_template_name(show_template)
        
        if list_templates:
            return _list_available_templates(template_type, verbose)

        elif show_template:
            return _show_template_content(show_template, template_type, verbose)

        else:
            return f"""GitAI Templates

Available commands:
  gitai templates --list                    # List {template_type} templates
  gitai templates --list --type pr          # List PR templates
  gitai templates --show <name>             # Show template content
  gitai templates --show <name> --type pr   # Show PR template

For more help: gitai templates --help"""

    except GitAIError:
        # Re-raise our own exceptions as-is
        raise
    except Exception as e:
        # Wrap unexpected errors with helpful context
        error_message = create_helpful_error_message(e, "Template operation failed")
        raise GitAIError(error_message) from e


def _list_available_templates(template_type: str, verbose: bool) -> str:
    """List available templates."""
    logger = setup_logger(__name__)

    log_with_context(logger, "info", "Listing templates", template_type=template_type)

    # TODO: Implement actual template discovery
    if template_type == "commit":
        templates = {
            "conventional": "Conventional commits format (type(scope): description)",
            "descriptive": "Detailed descriptive format with body",
            "minimal": "Minimal single-line format",
            "semantic": "Semantic versioning format",
        }
    else:  # pr
        templates = {
            "github": "GitHub pull request format",
            "gitlab": "GitLab merge request format",
            "standard": "Standard PR format",
            "detailed": "Detailed PR with all sections",
        }

    result = f"Available {template_type} templates:\n\n"

    for name, description in templates.items():
        result += f"  {name:<15} {description}\n"

    result += f"\nUse 'gitai templates --show <name> --type {template_type}' to view template content"

    return result


def _show_template_content(
    template_name: str, template_type: str, verbose: bool
) -> str:
    """Show template content."""
    logger = setup_logger(__name__)

    log_with_context(
        logger,
        "info",
        "Showing template",
        template_name=template_name,
        template_type=template_type,
    )

    # TODO: Load actual templates from template system
    # For now, return mock template content

    if template_type == "commit":
        if template_name == "conventional":
            content = """{{ type }}({{ scope }}): {{ description }}

{% if body %}
{{ body }}
{% endif %}

{% if breaking_changes %}
BREAKING CHANGE: {{ breaking_changes }}
{% endif %}

Variables:
- type: feat, fix, docs, style, refactor, test, chore
- scope: component or file affected (optional)
- description: brief description in imperative mood
- body: longer description (optional)
- breaking_changes: breaking change description (optional)"""

        elif template_name == "descriptive":
            content = """{{ summary }}

Changes:
{% for file in files_changed %}
- {{ file.path }}: {{ file.description }}
{% endfor %}

{% if details %}
Details:
{{ details }}
{% endif %}

Variables:
- summary: brief summary of changes
- files_changed: list of changed files with descriptions
- details: additional details (optional)"""

        elif template_name == "minimal":
            content = """{{ action }} {{ component }}

Variables:
- action: what was done (add, fix, update, etc.)
- component: what was changed"""

        else:
            content = f"Template '{template_name}' not found"

    else:  # pr templates
        if template_name == "github":
            content = """## Summary
{{ summary }}

## Changes
{% for change in changes %}
- {{ change }}
{% endfor %}

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

{% if breaking_changes %}
## Breaking Changes
{{ breaking_changes }}
{% endif %}

Variables:
- summary: brief overview of the PR
- changes: list of key changes
- breaking_changes: any breaking changes (optional)"""

        elif template_name == "gitlab":
            content = """## Summary
{{ summary }}

## Changes Made
{% for change in changes %}
- {{ change }}
{% endfor %}

## Testing Done
{{ testing }}

## Documentation
{{ documentation }}

Variables:
- summary: what this MR accomplishes
- changes: detailed list of changes
- testing: testing performed
- documentation: documentation updates"""

        else:
            content = f"Template '{template_name}' not found"

    return f"Template: {template_name} ({template_type})\n\n{content}"
