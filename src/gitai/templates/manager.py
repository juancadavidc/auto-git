"""Template management and rendering system."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast

import jinja2
from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from ..utils.exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateValidationError,
)


@dataclass
class TemplateInfo:
    """Information about a template."""

    name: str
    path: Path
    category: str  # 'commit' or 'pr'
    description: str
    variables: List[str]


class TemplateManager:
    """Manages template discovery, loading, and rendering with Jinja2."""

    def __init__(self, search_paths: List[Union[str, Path]]):
        """Initialize the template manager.

        Args:
            search_paths: List of directories to search for templates, in order of precedence
        """
        self.search_paths = [Path(p) for p in search_paths]
        self._env = self._create_environment()
        self._template_cache: Dict[str, Template] = {}
        self._template_info_cache: Dict[str, TemplateInfo] = {}

    def _create_environment(self) -> Environment:
        """Create Jinja2 environment with proper configuration."""
        # Create loaders for each search path
        loaders = []
        for path in self.search_paths:
            if path.exists() and path.is_dir():
                loaders.append(FileSystemLoader(str(path)))

        if not loaders:
            # Create a dummy loader if no valid paths exist
            loaders = [FileSystemLoader(".")]

        # Use ChoiceLoader to search paths in order
        loader = jinja2.ChoiceLoader(loaders)

        env = Environment(
            loader=loader,
            autoescape=False,  # We're generating text, not HTML
            trim_blocks=True,
            lstrip_blocks=True,
            undefined=jinja2.StrictUndefined,  # Fail on undefined variables
        )

        # Add custom filters
        env.filters["wordwrap"] = self._wordwrap_filter
        env.filters["capitalize_first"] = self._capitalize_first_filter

        return env

    def _wordwrap_filter(self, text: str, width: int = 72) -> str:
        """Custom word wrap filter for commit messages."""
        import textwrap

        return "\n".join(textwrap.wrap(text, width=width))

    def _capitalize_first_filter(self, text: str) -> str:
        """Capitalize first letter while preserving the rest."""
        if not text:
            return text
        return text[0].upper() + text[1:]

    def discover_templates(self) -> Dict[str, List[TemplateInfo]]:
        """Discover all available templates.

        Returns:
            Dictionary mapping categories ('commit', 'pr') to lists of template info
        """
        templates: Dict[str, List[TemplateInfo]] = {"commit": [], "pr": []}

        for search_path in self.search_paths:
            if not search_path.exists():
                continue

            # Look for commit templates
            commit_dir = search_path / "commit"
            if commit_dir.exists():
                templates["commit"].extend(
                    self._discover_in_directory(commit_dir, "commit")
                )

            # Look for PR templates
            pr_dir = search_path / "pr"
            if pr_dir.exists():
                templates["pr"].extend(self._discover_in_directory(pr_dir, "pr"))

        return templates

    def _discover_in_directory(
        self, directory: Path, category: str
    ) -> List[TemplateInfo]:
        """Discover templates in a specific directory."""
        templates = []

        for file_path in directory.glob("*.j2"):
            try:
                template_info = self._extract_template_info(file_path, category)
                templates.append(template_info)
            except Exception as e:
                # Log warning but continue discovery
                print(f"Warning: Failed to process template {file_path}: {e}")

        return templates

    def _extract_template_info(self, file_path: Path, category: str) -> TemplateInfo:
        """Extract metadata from a template file."""
        name = file_path.stem  # Remove .j2 extension

        try:
            content = file_path.read_text(encoding="utf-8")

            # Extract description from comment at top of file
            description = "No description available"
            variables = []

            lines = content.split("\n")
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line.startswith("{#") and "description:" in line:
                    description = (
                        line.split("description:", 1)[1].strip().rstrip("#}").strip()
                    )
                elif line.startswith("{#") and "variables:" in line:
                    var_text = (
                        line.split("variables:", 1)[1].strip().rstrip("#}").strip()
                    )
                    variables = [v.strip() for v in var_text.split(",") if v.strip()]

            # Extract variables from template content
            if not variables:
                variables = self._extract_variables_from_content(content)

            return TemplateInfo(
                name=name,
                path=file_path,
                category=category,
                description=description,
                variables=variables,
            )
        except Exception as e:
            raise TemplateValidationError(
                f"Failed to extract info from {file_path}: {e}"
            )

    def _extract_variables_from_content(self, content: str) -> List[str]:
        """Extract variable names from template content."""
        import re

        # Find all {{ variable }} patterns
        pattern = r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}"
        variables = set(re.findall(pattern, content))

        # Find all {% if variable %} patterns
        pattern = r"\{\%\s*if\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\%\}"
        variables.update(re.findall(pattern, content))

        return sorted(list(variables))

    def get_template(self, template_name: str, category: str) -> Template:
        """Get a template by name and category.

        Args:
            template_name: Name of the template (without .j2 extension)
            category: Template category ('commit' or 'pr')

        Returns:
            Compiled Jinja2 template

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateError: If template has syntax errors
        """
        cache_key = f"{category}/{template_name}"

        if cache_key in self._template_cache:
            return self._template_cache[cache_key]

        # Try to load template
        template_path = f"{category}/{template_name}.j2"

        try:
            template = self._env.get_template(template_path)
            self._template_cache[cache_key] = template
            return template
        except TemplateNotFound:
            raise TemplateNotFoundError(
                f"Template '{template_name}' not found in category '{category}'"
            )
        except jinja2.TemplateSyntaxError as e:
            raise TemplateError(f"Template syntax error in '{template_name}': {e}")

    def render_template(
        self, template_name: str, category: str, context: Dict[str, Any]
    ) -> str:
        """Render a template with the given context.

        Args:
            template_name: Name of the template
            category: Template category ('commit' or 'pr')
            context: Template variables

        Returns:
            Rendered template content

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateError: If rendering fails
        """
        try:
            template = self.get_template(template_name, category)
            return cast(str, template.render(**context))
        except jinja2.UndefinedError as e:
            raise TemplateError(
                f"Undefined variable in template '{template_name}': {e}"
            )
        except Exception as e:
            raise TemplateError(f"Failed to render template '{template_name}': {e}")

    def validate_template(
        self,
        template_name: str,
        category: str,
        required_variables: Optional[List[str]] = None,
    ) -> bool:
        """Validate that a template exists and has required variables.

        Args:
            template_name: Name of the template
            category: Template category
            required_variables: List of variables that must be present

        Returns:
            True if template is valid

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateValidationError: If template is invalid
        """
        # Validate template exists and can be loaded
        self.get_template(template_name, category)

        if required_variables:
            # Get template info to check variables
            templates = self.discover_templates()
            template_info = None

            for info in templates.get(category, []):
                if info.name == template_name:
                    template_info = info
                    break

            if template_info:
                missing_vars = set(required_variables) - set(template_info.variables)
                if missing_vars:
                    raise TemplateValidationError(
                        f"Template '{template_name}' missing required variables: {missing_vars}"
                    )

        return True

    def list_templates(self, category: Optional[str] = None) -> List[TemplateInfo]:
        """List available templates.

        Args:
            category: Optional category filter ('commit' or 'pr')

        Returns:
            List of template information
        """
        templates = self.discover_templates()

        if category:
            return templates.get(category, [])

        # Return all templates
        all_templates = []
        for template_list in templates.values():
            all_templates.extend(template_list)

        return all_templates


def create_template_manager(
    user_templates_dir: Optional[Path] = None,
    team_templates_dir: Optional[Path] = None,
    project_templates_dir: Optional[Path] = None,
) -> TemplateManager:
    """Create a template manager with standard search paths.

    Args:
        user_templates_dir: User-specific templates directory
        team_templates_dir: Team-shared templates directory
        project_templates_dir: Project-specific templates directory

    Returns:
        Configured template manager
    """
    search_paths: List[Union[str, Path]] = []

    # Add paths in precedence order (project > team > user > default)
    if project_templates_dir:
        search_paths.append(project_templates_dir)

    if team_templates_dir:
        search_paths.append(team_templates_dir)

    if user_templates_dir:
        search_paths.append(user_templates_dir)

    # Add default templates (bundled with package)
    default_templates = Path(__file__).parent / "defaults"
    search_paths.append(default_templates)

    return TemplateManager(search_paths)
