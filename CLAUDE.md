# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

When the user ask you to do a preview of a commit message execute gitai commit --preview

## Development Commands

### Installation & Setup
```bash
# Setup development environment
scripts/setup.sh

# Manual install in development mode  
pip install -e ".[dev]"
```

### Code Quality & Testing
```bash
# Run all quality checks (as in CI)
flake8 src/ tests/
black --check src/ tests/
isort --check-only src/ tests/
mypy src/
pytest --cov=src/gitai --cov-report=xml

# Format code
black src/ tests/
isort src/ tests/

# Security checks
bandit -r src/
safety check

# Run tests with coverage (80% minimum required)
pytest
```

### CLI Testing
```bash
# Test main CLI commands
gitai --help
gitai config --global
gitai commit --preview
gitai pr --base main
gitai templates --list
```

## Architecture Overview

GitAI is a Python CLI tool for AI-powered commit message and PR description generation with the following core structure:

### Core Components

- **CLI (`src/gitai/cli.py`)** - Click-based command interface
- **Commands (`src/gitai/commands/`)** - Individual command implementations (commit, pr, config, templates)
- **Git Analysis (`src/gitai/core/git_analyzer.py`)** - Extracts meaningful change information from git repositories
- **AI Providers (`src/gitai/providers/`)** - Pluggable AI backends (OpenAI, Anthropic, Ollama, LMStudio)
- **Template System (`src/gitai/templates/`)** - Jinja2-based templating for formatting output
- **Configuration (`src/gitai/config/`)** - Hierarchical config management (user/team/project)

### Key Design Patterns

- **Provider Pattern**: AI providers implement `BaseProvider` interface for consistent API
- **Template Hierarchy**: User > Team > Project > Default template resolution
- **Configuration Layers**: Multi-tier configuration with environment variable support
- **Error Handling**: Custom exceptions with helpful error messages and suggestions

### Data Models

- **DiffAnalysis**: Represents analyzed git changes with metadata
- **FileChange**: Individual file modification details
- **ChangeType**: Enum for categorizing change types (feature, fix, docs, etc.)

## Configuration

- Global config: `~/.config/gitai/config.yaml`
- Team config: `.gitai/config.yaml` (committed)
- Project config: `.gitai-local/config.yaml` (git-ignored)

## Templates

- Built-in templates in `templates/` directory
- User templates: `~/.config/gitai/templates/`
- Team templates: `.gitai/templates/`
- Jinja2-based with rich context variables for git changes

## Dependencies

- Python 3.9+
- Core: click, GitPython, Jinja2, PyYAML, requests, pydantic
- Dev: pytest, black, isort, mypy, flake8, bandit
- Test coverage requirement: 80% minimum