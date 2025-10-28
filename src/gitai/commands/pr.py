"""PR command implementation."""

from pathlib import Path
from typing import Optional

from gitai.core.git_analyzer import GitAnalyzer
from gitai.providers.factory import provider_factory
from gitai.providers.base import GenerationRequest
from gitai.config.manager import create_config_manager
from gitai.templates.manager import create_template_manager
from gitai.templates.context import build_pr_context
from gitai.utils.exceptions import GitAIError, InvalidRepositoryError
from gitai.utils.logger import setup_logger, log_with_context
from gitai.utils.validation import (
    validate_git_repository,
    validate_template_name,
    validate_provider_name,
    validate_branch_has_changes,
    validate_output_file,
    create_helpful_error_message,
)


def handle_pr(
    base_branch: str,
    template: str,
    provider: str,
    output_file: Optional[Path],
    verbose: bool = False,
    config_path: Optional[Path] = None,
) -> Optional[str]:
    """Handle PR command execution.

    Args:
        base_branch: Base branch to compare against
        template: Template name to use
        provider: AI provider name
        output_file: Optional output file path
        verbose: Enable verbose logging
        config_path: Optional config file path

    Returns:
        Generated PR description if no output file, None if written to file

    Raises:
        GitAIError: If PR generation fails
    """
    logger = setup_logger(__name__)

    try:
        # 1. Validate inputs and environment
        log_with_context(logger, "info", "Validating PR command inputs")
        
        # Validate we're in a git repository
        git_root = validate_git_repository()
        log_with_context(logger, "debug", "Git repository validated", git_root=str(git_root))
        
        # Validate template name
        template = validate_template_name(template)
        
        # Validate provider name
        provider = validate_provider_name(provider)
        
        # Validate output file if provided
        if output_file:
            output_file = validate_output_file(output_file)
        
        # Validate branch has changes (this also validates base branch exists)
        validate_branch_has_changes(base_branch)
        
        # 2. Load configuration
        log_with_context(logger, "info", "Loading configuration")
        config_manager = create_config_manager()
        config = config_manager.load_config()

        # 3. Analyze branch changes
        log_with_context(
            logger,
            "info",
            "Analyzing branch changes",
            base_branch=base_branch,
            template=template,
            provider=provider,
        )

        analyzer = GitAnalyzer()
        diff_analysis = analyzer.get_branch_changes(base_branch=base_branch)

        if not diff_analysis.files_changed:
            raise GitAIError(
                f"No changes found between current branch and '{base_branch}'"
            )

        # 4. Setup template manager and render template
        template_manager = create_template_manager(
            user_templates_dir=config.get_user_templates_dir(),
            team_templates_dir=config.get_team_templates_dir(),
            project_templates_dir=config.get_project_templates_dir(),
        )

        # Build context for template
        template_context = build_pr_context(diff_analysis, config, base_branch)

        # Check if template exists, fallback to github if not found
        try:
            template_manager.validate_template(template, "pr")
        except Exception:
            logger.warning(f"Template '{template}' not found, falling back to 'github'")
            template = "github"

        # Render template to create prompt
        try:
            rendered_template = template_manager.render_template(
                template, "pr", template_context
            )
        except Exception as e:
            # Fallback to basic prompt if template fails
            logger.warning(f"Template rendering failed: {e}, using basic prompt")
            rendered_template = _build_fallback_pr_prompt(template, diff_analysis)

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

        # 6. Generate PR description
        request = GenerationRequest(
            prompt=rendered_template,
            context=template_context,
        )

        response = ai_provider.generate(request)
        pr_description = response.content.strip()

        log_with_context(
            logger,
            "info",
            "PR description generated",
            description_length=len(pr_description),
            model_used=response.model_used,
        )

        # 7. Output result
        if output_file:
            try:
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(pr_description, encoding="utf-8")
                log_with_context(
                    logger, "info", "PR description saved", output_file=str(output_file)
                )
                return None
            except Exception as e:
                raise GitAIError(f"Failed to write to {output_file}: {e}")
        else:
            return _format_pr_output(pr_description, template, provider, base_branch)

    except (GitAIError, InvalidRepositoryError):
        # Re-raise our own exceptions as-is
        raise
    except Exception as e:
        # Wrap unexpected errors with helpful context
        error_message = create_helpful_error_message(e, "PR generation failed")
        raise GitAIError(error_message) from e


def _build_fallback_pr_prompt(template: str, diff_analysis) -> str:
    """Build fallback prompt when template system fails.

    Args:
        template: Template name
        diff_analysis: Git diff analysis

    Returns:
        Formatted prompt for AI generation
    """
    base_prompt = f"""Generate a pull request description using the '{template}' style for the following changes.

Files changed: {len(diff_analysis.files_changed)}
Lines added: {diff_analysis.total_additions}
Lines removed: {diff_analysis.total_deletions}

Change summary: {diff_analysis.change_summary}

Make it clear, informative, and well-structured."""

    if template == "github":
        base_prompt += """

Use GitHub PR format with:
## Summary, ## Changes, ## Testing sections"""

    elif template == "gitlab":
        base_prompt += """

Use GitLab MR format with:
## Summary, ## Changes Made, ## Testing Done, ## Documentation sections"""

    elif template == "detailed":
        base_prompt += """

Include comprehensive sections:
- Executive summary
- Detailed breakdown of changes
- Technical considerations
- Testing approach
- Breaking changes (if any)"""

    return base_prompt


def _format_pr_output(pr_description: str, template: str, provider: str, base_branch: str) -> str:
    """Format PR description for output display.

    Args:
        pr_description: Generated PR description
        template: Template used
        provider: AI provider used
        base_branch: Base branch used for comparison

    Returns:
        Formatted output string
    """
    return f"""Generated PR Description (template: {template}, provider: {provider}, base: {base_branch}):

{pr_description}

Save to file with: gitai pr --base {base_branch} --output pr.md"""
