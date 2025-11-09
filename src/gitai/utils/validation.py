"""Input validation utilities for GitAI commands."""

import re
import subprocess
from pathlib import Path
from typing import List, Optional

from .exceptions import GitAIError, InvalidRepositoryError


def validate_git_repository(path: Optional[Path] = None) -> Path:
    """Validate that we're in a git repository.

    Args:
        path: Optional path to check (defaults to current directory)

    Returns:
        Path to git repository root

    Raises:
        InvalidRepositoryError: If not in a git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
            cwd=path,
        )
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        raise InvalidRepositoryError(
            "Not in a git repository. Run 'git init' or navigate to a git repository."
        )
    except FileNotFoundError:
        raise InvalidRepositoryError("Git is not installed or not available in PATH.")


def validate_branch_exists(branch_name: str, path: Optional[Path] = None) -> bool:
    """Validate that a git branch exists.

    Args:
        branch_name: Name of the branch to check
        path: Optional path to git repository

    Returns:
        True if branch exists

    Raises:
        GitAIError: If branch doesn't exist or git operation fails
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{branch_name}"],
            capture_output=True,
            text=True,
            cwd=path,
        )

        if result.returncode == 0:
            return True

        # Try remote branches
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/remotes/origin/{branch_name}"],
            capture_output=True,
            text=True,
            cwd=path,
        )

        if result.returncode == 0:
            return True

        raise GitAIError(f"Branch '{branch_name}' does not exist")

    except subprocess.CalledProcessError as e:
        raise GitAIError(f"Failed to validate branch '{branch_name}': {e}")


def validate_template_name(template_name: str) -> str:
    """Validate template name format.

    Args:
        template_name: Template name to validate

    Returns:
        Validated template name

    Raises:
        GitAIError: If template name is invalid
    """
    if not template_name:
        raise GitAIError("Template name cannot be empty")

    if not template_name.strip():
        raise GitAIError("Template name cannot be only whitespace")

    # Template names should be alphanumeric with hyphens and underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", template_name):
        raise GitAIError(
            "Template name can only contain letters, numbers, hyphens, and underscores"
        )

    if len(template_name) > 50:
        raise GitAIError("Template name must be 50 characters or less")

    return template_name.strip()


def validate_provider_name(provider_name: str) -> str:
    """Validate AI provider name.

    Args:
        provider_name: Provider name to validate

    Returns:
        Validated provider name

    Raises:
        GitAIError: If provider name is invalid
    """
    if not provider_name:
        raise GitAIError("Provider name cannot be empty")

    provider_name = provider_name.strip().lower()

    # Get actual available providers from factory
    try:
        from gitai.providers.factory import provider_factory

        valid_providers = set(provider_factory.get_available_providers())
    except ImportError:
        # Fallback if import fails
        valid_providers = {"ollama", "openai", "anthropic"}

    if provider_name not in valid_providers:
        raise GitAIError(
            f"Unknown provider '{provider_name}'. Valid providers: {', '.join(sorted(valid_providers))}"
        )

    return provider_name


def validate_team_name(team_name: str) -> str:
    """Validate team name format.

    Args:
        team_name: Team name to validate

    Returns:
        Validated team name

    Raises:
        GitAIError: If team name is invalid
    """
    if not team_name:
        raise GitAIError("Team name cannot be empty")

    team_name = team_name.strip()

    if not team_name:
        raise GitAIError("Team name cannot be only whitespace")

    # Team names should be alphanumeric with hyphens and underscores
    if not re.match(r"^[a-zA-Z0-9_-]+$", team_name):
        raise GitAIError(
            "Team name can only contain letters, numbers, hyphens, and underscores"
        )

    if len(team_name) > 30:
        raise GitAIError("Team name must be 30 characters or less")

    # Reserved names
    reserved_names = {"config", "default", "system", "admin", "root"}
    if team_name.lower() in reserved_names:
        raise GitAIError(f"'{team_name}' is a reserved name and cannot be used")

    return team_name


def validate_output_file(file_path: Path) -> Path:
    """Validate output file path.

    Args:
        file_path: Output file path to validate

    Returns:
        Validated file path

    Raises:
        GitAIError: If file path is invalid
    """
    try:
        # Resolve path to catch issues early
        resolved_path = file_path.resolve()

        # Check if parent directory exists or can be created
        parent_dir = resolved_path.parent
        if not parent_dir.exists():
            try:
                parent_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError:
                raise GitAIError(
                    f"Permission denied: Cannot create directory {parent_dir}"
                )
            except OSError as e:
                raise GitAIError(f"Cannot create directory {parent_dir}: {e}")

        # Check if we can write to the directory
        if not parent_dir.is_dir():
            raise GitAIError(f"Parent path {parent_dir} is not a directory")

        # Check write permissions
        try:
            test_file = parent_dir / f".gitai_write_test_{hash(str(resolved_path))}"
            test_file.touch()
            test_file.unlink()
        except PermissionError:
            raise GitAIError(f"Permission denied: Cannot write to {parent_dir}")
        except OSError as e:
            raise GitAIError(f"Cannot write to {parent_dir}: {e}")

        return resolved_path

    except Exception as e:
        if isinstance(e, GitAIError):
            raise
        raise GitAIError(f"Invalid output file path '{file_path}': {e}")


def validate_has_staged_changes() -> bool:
    """Validate that there are staged changes for commit.

    Returns:
        True if there are staged changes

    Raises:
        GitAIError: If no staged changes found
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )

        if not result.stdout.strip():
            raise GitAIError(
                "No staged changes found. Use 'git add <files>' to stage changes before generating a commit message."
            )

        return True

    except subprocess.CalledProcessError as e:
        raise GitAIError(f"Failed to check staged changes: {e}")


def validate_branch_has_changes(base_branch: str) -> bool:
    """Validate that current branch has changes compared to base branch.

    Args:
        base_branch: Base branch to compare against

    Returns:
        True if there are changes

    Raises:
        GitAIError: If no changes found
    """
    try:
        # First validate base branch exists
        validate_branch_exists(base_branch)

        # Check for changes
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )

        if not result.stdout.strip():
            raise GitAIError(
                f"No changes found between current branch and '{base_branch}'. "
                f"Make sure you're on a different branch with commits."
            )

        return True

    except subprocess.CalledProcessError as e:
        raise GitAIError(f"Failed to check branch changes: {e}")


def suggest_similar_templates(
    template_name: str, available_templates: List[str]
) -> List[str]:
    """Suggest similar template names when a template is not found.

    Args:
        template_name: Template name that wasn't found
        available_templates: List of available template names

    Returns:
        List of similar template names
    """
    suggestions = []
    template_lower = template_name.lower()

    # Exact substring matches
    for template in available_templates:
        if template_lower in template.lower() or template.lower() in template_lower:
            suggestions.append(template)

    # If no substring matches, try prefix/suffix matches
    if not suggestions:
        for template in available_templates:
            template_lower_full = template.lower()
            if (
                template_lower.startswith(template_lower_full[:3])
                or template_lower.endswith(template_lower_full[-3:])
                or template_lower_full.startswith(template_lower[:3])
                or template_lower_full.endswith(template_lower[-3:])
            ):
                suggestions.append(template)

    return suggestions[:3]  # Return max 3 suggestions


def create_helpful_error_message(error: Exception, context: str = "") -> str:
    """Create a helpful error message with suggestions.

    Args:
        error: The original error
        context: Additional context about what was being attempted

    Returns:
        Enhanced error message with suggestions
    """
    base_message = str(error)

    if context:
        base_message = f"{context}: {base_message}"

    suggestions = []

    if isinstance(error, InvalidRepositoryError):
        suggestions.extend(
            [
                "• Navigate to a git repository: cd /path/to/your/repo",
                "• Initialize a new git repository: git init",
                "• Check git installation: git --version",
            ]
        )

    elif "No staged changes" in base_message:
        suggestions.extend(
            [
                "• Stage files for commit: git add <files>",
                "• Stage all changes: git add .",
                "• Check current status: git status",
            ]
        )

    elif "Template" in base_message and "not found" in base_message:
        suggestions.extend(
            [
                "• List available templates: gitai templates --list",
                "• Show template content: gitai templates --show <name>",
                "• Use default template: gitai commit (uses 'conventional')",
            ]
        )

    elif "Branch" in base_message and "does not exist" in base_message:
        suggestions.extend(
            [
                "• List available branches: git branch -a",
                "• Use default base branch: gitai pr (uses 'main')",
                "• Create the branch: git checkout -b <branch-name>",
            ]
        )

    elif "Provider" in base_message:
        suggestions.extend(
            [
                "• List supported providers: gitai config --show",
                "• Use default provider: gitai commit (uses 'ollama')",
                "• Check provider configuration: gitai config --show",
            ]
        )

    if suggestions:
        base_message += "\n\nSuggestions:\n" + "\n".join(suggestions)

    return base_message
