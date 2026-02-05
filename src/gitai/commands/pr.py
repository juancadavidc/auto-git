"""PR command implementation."""

from pathlib import Path
from typing import Optional

from gitai.config.manager import create_config_manager
from gitai.core.git_analyzer import GitAnalyzer
from gitai.core.models import DiffAnalysis
from gitai.observability.langfuse_tracer import LangfuseTracer
from gitai.providers.base import GenerationRequest
from gitai.providers.factory import provider_factory
from gitai.templates.context import build_pr_context
from gitai.templates.manager import create_template_manager
from gitai.utils.exceptions import GitAIError, InvalidRepositoryError
from gitai.utils.logger import log_with_context, setup_logger
from gitai.utils.prompts import get_agentic_system_prompt, get_system_prompt
from gitai.utils.validation import (
    create_helpful_error_message,
    validate_branch_has_changes,
    validate_git_repository,
    validate_output_file,
    validate_provider_name,
    validate_template_name,
)


def handle_pr(
    base_branch: str,
    template: str,
    provider: Optional[str],
    output_file: Optional[Path],
    agentic: bool = False,
    verbose: bool = False,
    config_path: Optional[Path] = None,
) -> Optional[str]:
    """Handle PR command execution.

    Args:
        base_branch: Base branch to compare against
        template: Template name to use
        provider: AI provider name
        output_file: Optional output file path
        agentic: Use agentic mode with tool-calling
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
        log_with_context(
            logger, "debug", "Git repository validated", git_root=str(git_root)
        )

        # Validate template name
        template = validate_template_name(template)

        # Validate output file if provided
        if output_file:
            output_file = validate_output_file(output_file)

        # Validate branch has changes (this also validates base branch exists)
        validate_branch_has_changes(base_branch)

        # 2. Load configuration
        log_with_context(logger, "info", "Loading configuration")
        config_manager = create_config_manager()
        config = config_manager.load_config()

        # If no provider specified, use highest priority from config
        if provider is None:
            enabled_providers = config.get_enabled_providers()
            if not enabled_providers:
                raise GitAIError("No providers enabled in configuration")
            provider = enabled_providers[0]
            log_with_context(
                logger, "info", "Using default provider", provider=provider
            )

        # Validate provider name (after setting default)
        provider = validate_provider_name(provider)

        # 3. Analyze branch changes
        log_with_context(
            logger,
            "info",
            "Analyzing branch changes",
            base_branch=base_branch,
            template=template,
            provider=provider,
        )

        # Enable detailed diff for templates that need it
        include_detailed = template in ["detailed"]

        analyzer = GitAnalyzer()
        diff_analysis = analyzer.get_branch_changes(
            base_branch=base_branch, include_detailed_diff=include_detailed
        )

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
        if agentic and ai_provider.supports_tool_calling():
            # Agentic mode: LLM uses tools to inspect diffs iteratively
            from gitai.agentic.loop import AgenticLoop

            log_with_context(
                logger, "info", "Using agentic mode with tool-calling"
            )

            # Setup Langfuse tracer if configured
            tracer = None
            langfuse_config = config.langfuse
            if langfuse_config and langfuse_config.enabled:
                try:
                    from gitai.observability.langfuse_tracer import (
                        LangfuseAgenticTracer,
                    )

                    tracer = LangfuseAgenticTracer(langfuse_config.model_dump())
                except Exception as e:
                    logger.warning(f"Failed to initialize Langfuse tracer: {e}")

            # Get agentic config
            agentic_config = config.agentic
            max_iterations = (
                agentic_config.max_iterations if agentic_config else 10
            )

            # Use agentic template (instructions only, no diff content)
            try:
                agentic_template = template_manager.render_template(
                    "agentic", "pr", template_context
                )
            except Exception:
                # Fallback to minimal instructions if agentic template not found
                agentic_template = (
                    "Generate a GitHub-style PR description.\n"
                    "Use your tools to inspect the branch changes first.\n"
                    "Include sections: Summary, Changes, Testing."
                )

            loop = AgenticLoop(
                provider=ai_provider,
                diff_analysis=diff_analysis,
                max_iterations=max_iterations,
                tracer=tracer,
            )

            agentic_result = loop.run(
                system_prompt=get_agentic_system_prompt("pr"),
                user_prompt=agentic_template,
            )

            pr_description = agentic_result.content.strip()

            log_with_context(
                logger,
                "info",
                "PR description generated (agentic)",
                description_length=len(pr_description),
                model_used=agentic_result.model_used,
                iterations=agentic_result.iterations,
                tool_calls=len(agentic_result.tool_calls_made),
            )

        elif agentic and not ai_provider.supports_tool_calling():
            # Provider doesn't support tools — warn and fall back
            log_with_context(
                logger,
                "warning",
                "Provider does not support agentic mode, falling back to single-shot",
                provider=provider,
            )
            request = GenerationRequest(
                prompt=rendered_template,
                context=template_context,
                system_prompt=get_system_prompt("pr"),
            )
            response = ai_provider.generate(request)
            pr_description = response.content.strip()

            log_with_context(
                logger,
                "info",
                "PR description generated (fallback)",
                description_length=len(pr_description),
                model_used=response.model_used,
            )

        else:
            # Standard single-shot generation (with optional Langfuse tracing)
            request = GenerationRequest(
                prompt=rendered_template,
                context=template_context,
                system_prompt=get_system_prompt("pr"),
            )

            langfuse_config = config.get_langfuse_config()
            if langfuse_config:
                tracer = LangfuseTracer(langfuse_config)
                response = tracer.trace_generation(
                    provider=ai_provider,
                    request=request,
                    command="pr",
                    metadata={"template": template, "base_branch": base_branch},
                )
            else:
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


def _build_fallback_pr_prompt(template: str, diff_analysis: DiffAnalysis) -> str:
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


def _format_pr_output(
    pr_description: str, template: str, provider: str, base_branch: str
) -> str:
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
