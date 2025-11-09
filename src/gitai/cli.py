"""GitAI CLI entry point and main commands."""

import sys
from pathlib import Path
from typing import Optional

import click

from gitai import __version__
from gitai.utils.exceptions import GitAIError
from gitai.utils.logger import setup_logger

# Global logger for CLI
logger = setup_logger(__name__)


@click.group()  # type: ignore[misc]
@click.version_option(version=__version__)  # type: ignore[misc]
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--config-path",
    type=click.Path(exists=True, path_type=Path),
    help="Path to configuration file",
)
@click.pass_context  # type: ignore[misc]
def main(ctx: click.Context, verbose: bool, config_path: Optional[Path]) -> None:
    """GitAI - AI-powered commit and PR description generation.

    GitAI automates the creation of commit messages and pull request descriptions
    using AI analysis of git changes and customizable templates.

    Examples:
        gitai commit --preview           # Preview commit message
        gitai pr --base main            # Generate PR description
        gitai config init               # Initialize configuration
    """
    # Ensure context object exists
    ctx.ensure_object(dict)

    # Store global options in context
    ctx.obj["verbose"] = verbose
    ctx.obj["config_path"] = config_path

    # Configure logging level
    if verbose:
        import logging

        logging.getLogger("gitai").setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")


@main.command()  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--template",
    "-t",
    default="conventional",
    help="Template to use for commit message (default: conventional)",
)
@click.option(  # type: ignore[misc]
    "--provider",
    "-p",
    default=None,
    help="AI provider to use (default: highest priority from config)",
)
@click.option(  # type: ignore[misc]
    "--preview", "-P", is_flag=True, help="Preview commit message without applying"
)
@click.option(  # type: ignore[misc]
    "--include-untracked", is_flag=True, help="Include untracked files in analysis"
)
@click.pass_context  # type: ignore[misc]
def commit(
    ctx: click.Context,
    template: str,
    provider: str,
    preview: bool,
    include_untracked: bool,
) -> None:
    """Generate commit message from staged changes.

    Analyzes git staged changes and generates an appropriate commit message
    using the specified template and AI provider.

    Examples:
        gitai commit                     # Generate and apply commit
        gitai commit --preview           # Show preview without committing
        gitai commit -t descriptive      # Use descriptive template
        gitai commit -p openai           # Use OpenAI provider
    """
    try:
        from gitai.commands.commit import handle_commit

        logger.info("Starting commit command")

        result = handle_commit(
            template=template,
            provider=provider,
            preview=preview,
            include_untracked=include_untracked,
            verbose=ctx.obj.get("verbose", False),
            config_path=ctx.obj.get("config_path"),
        )

        if result:
            click.echo(result)

    except GitAIError as e:
        logger.error(f"GitAI error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--base",
    "-b",
    default="main",
    help="Base branch to compare against (default: main)",
)
@click.option(  # type: ignore[misc]
    "--template",
    "-t",
    default="github",
    help="Template to use for PR description (default: github)",
)
@click.option(  # type: ignore[misc]
    "--provider",
    "-p",
    default=None,
    help="AI provider to use (default: highest priority from config)",
)
@click.option(  # type: ignore[misc]
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file for PR description (default: stdout)",
)
@click.pass_context  # type: ignore[misc]
def pr(
    ctx: click.Context, base: str, template: str, provider: str, output: Optional[Path]
) -> None:
    """Generate PR description from branch changes.

    Analyzes changes between the current branch and base branch to generate
    a comprehensive pull request description.

    Examples:
        gitai pr                         # Generate PR description
        gitai pr --base develop          # Compare against develop branch
        gitai pr -o pr.md               # Save to file
        gitai pr -t detailed            # Use detailed template
    """
    try:
        from gitai.commands.pr import handle_pr

        logger.info("Starting PR command")

        result = handle_pr(
            base_branch=base,
            template=template,
            provider=provider,
            output_file=output,
            verbose=ctx.obj.get("verbose", False),
            config_path=ctx.obj.get("config_path"),
        )

        if result and not output:
            click.echo(result)
        elif output:
            click.echo(f"PR description saved to {output}")

    except GitAIError as e:
        logger.error(f"GitAI error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--global", "global_config", is_flag=True, help="Initialize global configuration"
)
@click.option("--team", help="Initialize team configuration")  # type: ignore[misc]
@click.option("--show", is_flag=True, help="Show current configuration")  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--set-provider",
    type=click.Choice(["anthropic", "openai", "ollama", "lmstudio"]),
    help="Set the preferred AI provider",
)
@click.pass_context  # type: ignore[misc]
def config(
    ctx: click.Context,
    global_config: bool,
    team: Optional[str],
    show: bool,
    set_provider: Optional[str],
) -> None:
    """Manage GitAI configuration.

    Initialize user configuration, set up team configurations,
    or display current settings.

    Examples:
        gitai config --global                  # Setup global user config
        gitai config --team frontend           # Setup team config
        gitai config --show                    # Show current config
        gitai config --set-provider anthropic  # Set Anthropic as default provider
        gitai config --set-provider lmstudio   # Set LMStudio as default provider
    """
    try:
        from gitai.commands.config import handle_config

        logger.info("Starting config command")

        result = handle_config(
            init_global=global_config,
            team_name=team,
            show_config=show,
            set_provider=set_provider,
            verbose=ctx.obj.get("verbose", False),
            config_path=ctx.obj.get("config_path"),
        )

        if result:
            click.echo(result)

    except GitAIError as e:
        logger.error(f"GitAI error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


@main.command()  # type: ignore[misc]
@click.option("--list", "list_templates", is_flag=True, help="List available templates")  # type: ignore[misc]
@click.option("--show", help="Show template content")  # type: ignore[misc]
@click.option(  # type: ignore[misc]
    "--type",
    "template_type",
    type=click.Choice(["commit", "pr"]),
    default="commit",
    help="Template type (default: commit)",
)
@click.pass_context  # type: ignore[misc]
def templates(
    ctx: click.Context, list_templates: bool, show: Optional[str], template_type: str
) -> None:
    """Manage templates for commit messages and PR descriptions.

    List available templates or show template content.

    Examples:
        gitai templates --list           # List all commit templates
        gitai templates --list --type pr # List PR templates
        gitai templates --show conventional # Show conventional template
    """
    try:
        from gitai.commands.templates import handle_templates

        logger.info("Starting templates command")

        result = handle_templates(
            list_templates=list_templates,
            show_template=show,
            template_type=template_type,
            verbose=ctx.obj.get("verbose", False),
            config_path=ctx.obj.get("config_path"),
        )

        if result:
            click.echo(result)

    except GitAIError as e:
        logger.error(f"GitAI error: {e}")
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        click.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
