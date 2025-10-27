# Source Tree Structure - GitAI

## Overview

This document defines the complete source tree structure for GitAI, including development, testing, configuration, and documentation directories. The structure follows Python best practices and supports the modular architecture design.

## Project Root Structure

```
gitai/
├── .github/                     # GitHub workflows and templates
│   ├── workflows/
│   │   ├── ci.yml              # Continuous integration
│   │   ├── release.yml         # Release automation
│   │   └── docs.yml            # Documentation deployment
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   ├── feature_request.md
│   │   └── question.md
│   └── pull_request_template.md
├── docs/                        # Documentation
├── src/                         # Source code
├── templates/                   # Default templates
├── config/                      # Default configurations
├── tests/                       # Test suite
├── scripts/                     # Development and utility scripts
├── examples/                    # Usage examples
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── LICENSE
├── CONTRIBUTING.md
└── CHANGELOG.md
```

## Source Code Structure (`src/gitai/`)

```
src/gitai/
├── __init__.py                  # Package initialization
├── cli.py                       # CLI entry point and main commands
├── commands/                    # Command implementations
│   ├── __init__.py
│   ├── commit.py               # gitai commit command
│   ├── pr.py                   # gitai pr command
│   ├── config.py               # gitai config command
│   └── templates.py            # gitai templates command
├── core/                        # Core business logic
│   ├── __init__.py
│   ├── git_analyzer.py         # Git operations and diff analysis
│   ├── message_generator.py    # Commit message generation logic
│   ├── pr_generator.py         # PR description generation logic
│   └── context_builder.py      # Context preparation for templates
├── templates/                   # Template management
│   ├── __init__.py
│   ├── manager.py              # Template discovery and loading
│   ├── renderer.py             # Jinja2 template rendering
│   └── validator.py            # Template validation
├── config/                      # Configuration system
│   ├── __init__.py
│   ├── manager.py              # Configuration loading and merging
│   ├── models.py               # Pydantic configuration models
│   └── defaults.py             # Default configuration values
├── providers/                   # AI provider implementations
│   ├── __init__.py
│   ├── base.py                 # Base provider interface
│   ├── ollama.py               # Ollama provider implementation
│   ├── openai.py               # OpenAI provider implementation
│   └── factory.py              # Provider factory and selection
└── utils/                       # Utilities and helpers
    ├── __init__.py
    ├── logger.py               # Logging configuration
    ├── exceptions.py           # Custom exception classes
    ├── file_utils.py           # File operations utilities
    └── validation.py           # Input validation helpers
```

## Default Templates Structure (`templates/`)

```
templates/
├── commit/                      # Commit message templates
│   ├── conventional.txt        # Conventional commits format
│   ├── descriptive.txt         # Detailed descriptive format
│   ├── minimal.txt             # Minimal single-line format
│   ├── semantic.txt            # Semantic versioning format
│   └── team-specific/          # Team-specific templates
│       ├── frontend.txt
│       ├── backend.txt
│       └── devops.txt
├── pr/                          # Pull request templates
│   ├── github.md               # GitHub PR format
│   ├── gitlab.md               # GitLab MR format
│   ├── standard.md             # Standard PR format
│   ├── detailed.md             # Detailed PR with sections
│   └── team-specific/          # Team-specific PR templates
│       ├── frontend.md
│       ├── backend.md
│       └── devops.md
├── common/                      # Shared template components
│   ├── headers.txt             # Common headers
│   ├── footers.txt             # Common footers
│   └── variables.txt           # Available variables documentation
└── examples/                    # Example template implementations
    ├── custom-commit.txt
    ├── custom-pr.md
    └── inheritance-example.txt
```

## Configuration Structure (`config/`)

```
config/
├── default.yaml                 # Base default configuration
├── providers/                   # Provider-specific configurations
│   ├── ollama.yaml
│   ├── openai.yaml
│   └── anthropic.yaml
├── teams/                       # Team configuration examples
│   ├── frontend-example.yaml
│   ├── backend-example.yaml
│   └── devops-example.yaml
└── schema/                      # Configuration schema definitions
    ├── app-config.json
    ├── team-config.json
    └── provider-config.json
```

## Test Structure (`tests/`)

```
tests/
├── conftest.py                  # Pytest configuration and fixtures
├── unit/                        # Unit tests
│   ├── __init__.py
│   ├── commands/
│   │   ├── test_commit.py
│   │   ├── test_pr.py
│   │   └── test_config.py
│   ├── core/
│   │   ├── test_git_analyzer.py
│   │   ├── test_message_generator.py
│   │   ├── test_pr_generator.py
│   │   └── test_context_builder.py
│   ├── templates/
│   │   ├── test_manager.py
│   │   ├── test_renderer.py
│   │   └── test_validator.py
│   ├── config/
│   │   ├── test_manager.py
│   │   └── test_models.py
│   ├── providers/
│   │   ├── test_base.py
│   │   ├── test_ollama.py
│   │   ├── test_openai.py
│   │   └── test_factory.py
│   └── utils/
│       ├── test_logger.py
│       ├── test_file_utils.py
│       └── test_validation.py
├── integration/                 # Integration tests
│   ├── __init__.py
│   ├── test_commit_flow.py     # End-to-end commit generation
│   ├── test_pr_flow.py         # End-to-end PR generation
│   ├── test_config_hierarchy.py # Configuration loading
│   └── test_template_inheritance.py # Template system
├── fixtures/                    # Test data and fixtures
│   ├── repos/                  # Sample git repositories
│   │   ├── simple-repo/
│   │   ├── complex-repo/
│   │   └── empty-repo/
│   ├── templates/              # Test templates
│   │   ├── valid/
│   │   └── invalid/
│   ├── configs/                # Test configurations
│   │   ├── valid/
│   │   └── invalid/
│   └── responses/              # Mock API responses
│       ├── ollama/
│       └── openai/
├── performance/                 # Performance tests
│   ├── test_large_repo.py
│   ├── test_memory_usage.py
│   └── benchmarks.py
└── e2e/                        # End-to-end tests
    ├── test_cli_commands.py
    ├── test_user_workflows.py
    └── test_error_scenarios.py
```

## Documentation Structure (`docs/`)

```
docs/
├── api/                         # API documentation
│   ├── cli.md                  # CLI reference
│   ├── core.md                 # Core modules
│   ├── providers.md            # Provider interfaces
│   └── templates.md            # Template system
├── guides/                      # User guides
│   ├── installation.md
│   ├── quick-start.md
│   ├── configuration.md
│   ├── templates.md
│   └── troubleshooting.md
├── development/                 # Developer documentation
│   ├── contributing.md
│   ├── architecture.md
│   ├── testing.md
│   └── release-process.md
├── examples/                    # Usage examples
│   ├── basic-usage.md
│   ├── custom-templates.md
│   ├── team-configuration.md
│   └── advanced-usage.md
├── planning/                    # Project planning documents
│   ├── roadmap-refined.md
│   ├── architecture-design.md
│   ├── enterprise-adoption-plan.md
│   ├── implementation-roadmap.md
│   ├── code-standards.md
│   ├── source-tree.md
│   └── project-overview.md
└── assets/                      # Documentation assets
    ├── images/
    ├── diagrams/
    └── videos/
```

## Development Scripts (`scripts/`)

```
scripts/
├── setup/                       # Setup and installation scripts
│   ├── install-dev.sh          # Development environment setup
│   ├── install-pre-commit.sh   # Pre-commit hooks setup
│   └── verify-installation.py  # Installation verification
├── development/                 # Development utilities
│   ├── format-code.sh          # Code formatting
│   ├── run-tests.sh            # Test execution
│   ├── check-types.sh          # Type checking
│   └── generate-docs.py        # Documentation generation
├── build/                       # Build and release scripts
│   ├── build-package.sh        # Package building
│   ├── test-release.sh         # Release testing
│   └── publish.py              # Publishing automation
└── utils/                       # Utility scripts
    ├── clean.sh                # Clean build artifacts
    ├── update-deps.py          # Dependency updates
    └── generate-changelog.py   # Changelog generation
```

## Examples Structure (`examples/`)

```
examples/
├── basic/                       # Basic usage examples
│   ├── simple-commit.py
│   ├── simple-pr.py
│   └── basic-config.yaml
├── advanced/                    # Advanced usage examples
│   ├── custom-provider.py
│   ├── template-inheritance/
│   │   ├── base.txt
│   │   └── custom.txt
│   └── complex-config.yaml
├── team-setups/                 # Real team configuration examples
│   ├── frontend-team/
│   │   ├── config.yaml
│   │   ├── templates/
│   │   └── README.md
│   ├── backend-team/
│   │   ├── config.yaml
│   │   ├── templates/
│   │   └── README.md
│   └── devops-team/
│       ├── config.yaml
│       ├── templates/
│       └── README.md
└── integrations/                # Integration examples
    ├── github-actions/
    ├── gitlab-ci/
    └── pre-commit-hook/
```

## File Patterns and Conventions

### Python Files
- **Modules**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Configuration Files
- **YAML**: `.yaml` extension preferred over `.yml`
- **JSON**: For schema definitions
- **Environment**: `.env` files for environment-specific config

### Template Files
- **Commit templates**: `.txt` extension
- **PR templates**: `.md` extension
- **Partials**: `_partial.txt` or `_partial.md`

### Test Files
- **Test modules**: `test_*.py`
- **Test classes**: `Test*`
- **Test functions**: `test_*`
- **Fixtures**: `conftest.py`

## Directory Permissions and Access

### Read-Only Directories
- `config/` - Default configurations (runtime read-only)
- `templates/` - Default templates (runtime read-only)

### Read-Write Directories (Runtime)
- User configuration: `~/.config/gitai/`
- User templates: `~/.config/gitai/templates/`
- Project overrides: `<project>/.gitai/`

### Development-Only Directories
- `tests/` - Not included in distribution
- `scripts/` - Development utilities only
- `docs/development/` - Developer-specific docs

## Distribution Structure

### Source Distribution
```
gitai-0.1.0/
├── src/gitai/          # Source code
├── templates/          # Default templates
├── config/            # Default configuration
├── README.md
├── LICENSE
├── pyproject.toml
└── CHANGELOG.md
```

### Wheel Distribution
```
gitai-0.1.0-py3-none-any.whl
└── gitai/
    ├── __init__.py
    ├── cli.py
    ├── commands/
    ├── core/
    ├── templates/
    ├── config/
    ├── providers/
    └── utils/
```

## Runtime Directory Structure

### User Configuration Directory
```
~/.config/gitai/
├── config.yaml         # User global configuration
├── teams/              # Team-specific configurations
│   ├── frontend.yaml
│   └── backend.yaml
├── templates/          # User custom templates
│   ├── commit/
│   └── pr/
└── cache/              # Runtime cache
    ├── parsed_templates/
    └── provider_health/
```

### Project Directory Structure
```
<project-root>/
├── .git/
├── .gitai/             # Optional project-specific config
│   ├── config.yaml     # Project overrides
│   └── templates/      # Project-specific templates
│       ├── commit/
│       └── pr/
└── ... (project files)
```

## Security Considerations

### File Permissions
- Configuration files: `644` (readable by owner and group)
- Template files: `644` (readable by owner and group)
- Scripts: `755` (executable by owner, readable by others)
- Cache directories: `755` (accessible by owner only)

### Path Validation
- All template paths validated against base directory
- No symbolic link following outside base paths
- Input sanitization for all file operations

---

**Document**: Source Tree Structure v1.0 (GitAI)  
**Last updated**: 2024-10-24  
**Focus**: Complete project organization and file structure