"""Commit command implementation."""

from pathlib import Path
from typing import Optional
import subprocess

from gitai.core.git_analyzer import GitAnalyzer
from gitai.providers.factory import provider_factory
from gitai.providers.base import GenerationRequest
from gitai.config.manager import create_config_manager
from gitai.templates.manager import create_template_manager
from gitai.templates.context import build_commit_context
from gitai.utils.exceptions import GitAIError, NoStagedChangesError, InvalidRepositoryError
from gitai.utils.logger import setup_logger, log_with_context
from gitai.utils.validation import (
    validate_git_repository,
    validate_template_name,
    validate_provider_name,
    validate_has_staged_changes,
    create_helpful_error_message,
)


def handle_commit(
    template: str,
    provider: str,
    preview: bool,
    include_untracked: bool,
    verbose: bool = False,
    config_path: Optional[Path] = None,
) -> Optional[str]:
    """Handle commit command execution.

    Args:
        template: Template name to use
        provider: AI provider name
        preview: Whether to preview without applying
        include_untracked: Include untracked files
        verbose: Enable verbose logging
        config_path: Optional config file path

    Returns:
        Generated commit message if preview, None if applied

    Raises:
        GitAIError: If commit generation fails
    """
    logger = setup_logger(__name__)

    try:
        # 1. Validate inputs and environment
        log_with_context(logger, "info", "Validating commit command inputs")
        
        # Validate we're in a git repository
        git_root = validate_git_repository()
        log_with_context(logger, "debug", "Git repository validated", git_root=str(git_root))
        
        # Validate template name
        template = validate_template_name(template)
        
        # Validate provider name
        provider = validate_provider_name(provider)
        
        # Check for staged changes (unless including untracked)
        if not include_untracked:
            validate_has_staged_changes()
        
        # 2. Load configuration
        log_with_context(logger, "info", "Loading configuration")
        config_manager = create_config_manager()
        config = config_manager.load_config()

        # 3. Analyze staged changes
        log_with_context(
            logger,
            "info",
            "Analyzing staged changes",
            template=template,
            provider=provider,
        )

        analyzer = GitAnalyzer()
        diff_analysis = analyzer.get_staged_changes(include_untracked=include_untracked)

        # 4. Setup template manager and render template
        template_manager = create_template_manager(
            user_templates_dir=config.get_user_templates_dir(),
            team_templates_dir=config.get_team_templates_dir(),
            project_templates_dir=config.get_project_templates_dir(),
        )

        # Build context for template
        template_context = build_commit_context(diff_analysis, config)

        # Check if template exists, fallback to conventional if not found
        try:
            template_manager.validate_template(template, "commit")
        except Exception:
            logger.warning(f"Template '{template}' not found, falling back to 'conventional'")
            template = "conventional"

        # Render template to create prompt
        try:
            rendered_template = template_manager.render_template(
                template, "commit", template_context
            )
        except Exception as e:
            # Fallback to basic prompt if template fails
            logger.warning(f"Template rendering failed: {e}, using basic prompt")
            rendered_template = _build_fallback_prompt(template, diff_analysis)

        # 5. Create AI provider with config
        try:
            provider_config = config.get_provider_config(provider)
        except (ValueError, KeyError):
            # Fallback to default configuration
            logger.warning(f"Provider '{provider}' not configured, using defaults")
            if provider == "openai":
                provider_config = {
                    "api_key": None,  # Will check environment
                    "model": "gpt-3.5-turbo",
                    "timeout": 30,
                }
            elif provider == "anthropic":
                provider_config = {
                    "api_key": None,  # Will check environment
                    "model": "claude-3-haiku-20240307",
                    "timeout": 30,
                }
            else:  # ollama fallback
                provider_config = {
                    "base_url": "http://localhost:11434",
                    "model": "qwen2.5:7b",
                    "timeout": 30,
                }

        ai_provider = provider_factory.create_provider(provider, provider_config)

        # 6. Generate commit message
        request = GenerationRequest(
            prompt=rendered_template,
            context=template_context,
        )

        response = ai_provider.generate(request)
        commit_message = response.content.strip()

        log_with_context(
            logger,
            "info",
            "Commit message generated",
            message_length=len(commit_message),
            model_used=response.model_used,
        )

        # 7. Apply or preview
        if preview:
            return _format_preview(commit_message, template, provider)
        else:
            return _apply_commit(commit_message, logger)

    except (GitAIError, NoStagedChangesError, InvalidRepositoryError):
        # Re-raise our own exceptions as-is
        raise
    except Exception as e:
        # Wrap unexpected errors with helpful context
        error_message = create_helpful_error_message(e, "Commit generation failed")
        raise GitAIError(error_message) from e


def _build_fallback_prompt(template: str, diff_analysis) -> str:
    """Build fallback prompt when template system fails.

    Args:
        template: Template name
        diff_analysis: Git diff analysis

    Returns:
        Formatted prompt for AI generation
    """
    base_prompt = f"""Generate a commit message using the '{template}' style for the following changes.

Files changed: {len(diff_analysis.files_changed)}
Lines added: {diff_analysis.total_additions}
Lines removed: {diff_analysis.total_deletions}

Change summary: {diff_analysis.change_summary}

Make it clear, concise, and descriptive."""

    if template == "conventional":
        base_prompt += """

Use conventional commit format: type(scope): description
Where type is one of: feat, fix, docs, style, refactor, test, chore"""

    elif template == "minimal":
        base_prompt += """

Keep it under 50 characters and use present tense."""

    return base_prompt


def _format_preview(commit_message: str, template: str, provider: str) -> str:
    """Format commit message for preview display.

    Args:
        commit_message: Generated commit message
        template: Template used
        provider: AI provider used

    Returns:
        Formatted preview string
    """
    return f"""Generated Commit Message (template: {template}, provider: {provider}):

{commit_message}

Run without --preview to apply this commit message."""


def _apply_commit(commit_message: str, logger) -> Optional[str]:
    """Apply commit message to git repository.

    Args:
        commit_message: Message to commit
        logger: Logger instance

    Returns:
        None if successful, error message if failed
    """
    try:
        # Validate we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            check=True,
        )
        
        # Apply the commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_message],
            capture_output=True,
            text=True,
            check=True,
        )

        log_with_context(logger, "info", "Commit applied successfully")
        print(f"Commit applied successfully!")
        print(f"Message: {commit_message}")
        
        return None

    except subprocess.CalledProcessError as e:
        if "nothing to commit" in e.stderr:
            raise GitAIError("Nothing to commit. Use 'git add' to stage files first.")
        elif "not a git repository" in e.stderr:
            raise InvalidRepositoryError("Not in a git repository")
        else:
            raise GitAIError(f"Git commit failed: {e.stderr.strip()}")
    except Exception as e:
        raise GitAIError(f"Failed to apply commit: {e}")
