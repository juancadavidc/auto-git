# Code Standards - GitAI

## Overview

This document defines the coding standards, conventions, and best practices for the GitAI project. These standards ensure code consistency, maintainability, and ease of contribution.

## Python Standards

### Language Version
- **Python 3.9+**: Minimum supported version
- **Type Hints**: Required for all public functions and methods
- **f-strings**: Preferred for string formatting

### Code Formatting

#### Black Configuration
```toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.mypy_cache
  | \.pytest_cache
  | build
  | dist
)/
'''
```

#### Import Sorting (isort)
```toml
[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["gitai"]
```

### Naming Conventions

#### Classes
```python
# ✅ Good
class GitAnalyzer:
class TemplateManager:
class BaseProvider:

# ❌ Bad
class git_analyzer:
class templatemanager:
```

#### Functions and Variables
```python
# ✅ Good
def get_staged_changes() -> DiffAnalysis:
def render_template(template: str, context: dict) -> str:
staged_files = []
config_manager = ConfigManager()

# ❌ Bad
def getStagedChanges():
def renderTemplate():
stagedFiles = []
configManager = ConfigManager()
```

#### Constants
```python
# ✅ Good
DEFAULT_PROVIDER = "ollama"
MAX_RETRY_ATTEMPTS = 3
TEMPLATE_EXTENSIONS = [".txt", ".md"]

# ❌ Bad
default_provider = "ollama"
maxRetryAttempts = 3
```

#### Files and Modules
```python
# ✅ Good
git_analyzer.py
template_manager.py
config_models.py

# ❌ Bad
GitAnalyzer.py
templateManager.py
configModels.py
```

### Type Annotations

#### Required Annotations
```python
# ✅ Good - All public functions typed
def get_staged_changes(self, include_untracked: bool = False) -> DiffAnalysis:
    """Analyze staged changes for commit message generation."""
    pass

def render_template(self, template: str, context: Dict[str, Any]) -> str:
    """Render template with provided context."""
    pass

# ❌ Bad - Missing type hints
def get_staged_changes(self, include_untracked=False):
    pass
```

#### Complex Types
```python
from typing import Dict, List, Optional, Union, Protocol
from pathlib import Path

# ✅ Good
def load_config(
    config_paths: List[Path],
    overrides: Optional[Dict[str, Any]] = None
) -> AppConfig:
    pass

# Use Protocol for structural typing
class ProviderProtocol(Protocol):
    def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        ...
```

### Error Handling

#### Custom Exceptions
```python
# src/gitai/utils/exceptions.py
class GitAIError(Exception):
    """Base exception for GitAI errors."""
    pass

class GitAnalysisError(GitAIError):
    """Raised when git analysis fails."""
    pass

class TemplateRenderError(GitAIError):
    """Raised when template rendering fails."""
    pass

class ProviderError(GitAIError):
    """Raised when AI provider fails."""
    pass
```

#### Error Handling Pattern
```python
# ✅ Good - Specific exceptions with context
try:
    changes = analyzer.get_staged_changes()
except GitError as e:
    raise GitAnalysisError(f"Failed to analyze staged changes: {e}") from e

# ✅ Good - Resource cleanup
def generate_message(self, prompt: str) -> str:
    try:
        response = requests.post(self.api_url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["response"]
    except requests.RequestException as e:
        logger.error(f"Provider request failed: {e}")
        raise ProviderError(f"Failed to generate message: {e}") from e

# ❌ Bad - Bare except
try:
    changes = analyzer.get_staged_changes()
except:
    pass
```

### Logging

#### Logger Configuration
```python
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Use structured logging
logger.info(
    "Template rendered successfully",
    extra={
        "template_name": template_name,
        "context_keys": list(context.keys()),
        "render_time_ms": render_time * 1000
    }
)
```

#### Log Levels
- **DEBUG**: Detailed diagnostic information
- **INFO**: General operational messages
- **WARNING**: Potentially problematic situations
- **ERROR**: Error events that don't prevent operation
- **CRITICAL**: Serious errors that may abort operation

## Documentation Standards

### Docstrings (Google Style)
```python
def get_branch_changes(
    self, 
    base_branch: str = "main",
    include_context: bool = True
) -> DiffAnalysis:
    """Analyze changes between current branch and base branch.
    
    Args:
        base_branch: The base branch to compare against. Defaults to "main".
        include_context: Whether to include additional context. Defaults to True.
        
    Returns:
        DiffAnalysis object containing change information.
        
    Raises:
        GitAnalysisError: If git operations fail.
        ValueError: If base_branch doesn't exist.
        
    Example:
        >>> analyzer = GitAnalyzer()
        >>> changes = analyzer.get_branch_changes("develop")
        >>> print(f"Files changed: {len(changes.files_changed)}")
    """
    pass
```

### Code Comments
```python
# ✅ Good - Explain why, not what
def _sanitize_file_path(self, path: str) -> str:
    # Remove potential security risks from file paths
    # This prevents directory traversal attacks in template loading
    return str(Path(path).resolve().relative_to(self.base_path))

# ✅ Good - Complex logic explanation
def _merge_configs(self, base: dict, override: dict) -> dict:
    """Deep merge configuration dictionaries.
    
    Note: This preserves nested dictionaries while allowing
    complete override of list values for cleaner config management.
    """
    pass

# ❌ Bad - Obvious comments
x = x + 1  # Increment x
return result  # Return the result
```

## Testing Standards

### Test Organization
```
tests/
├── unit/                    # Unit tests
│   ├── core/
│   │   ├── test_git_analyzer.py
│   │   └── test_context_builder.py
│   ├── providers/
│   │   ├── test_base_provider.py
│   │   └── test_ollama_provider.py
│   └── templates/
│       └── test_template_manager.py
├── integration/             # Integration tests
│   ├── test_commit_flow.py
│   └── test_pr_flow.py
├── fixtures/                # Test data
│   ├── repos/              # Sample git repositories
│   ├── templates/          # Sample templates
│   └── configs/            # Sample configurations
└── conftest.py             # Pytest configuration
```

### Test Naming
```python
# ✅ Good - Descriptive test names
def test_staged_changes_analysis_with_multiple_files():
def test_template_rendering_with_missing_variables_raises_error():
def test_config_loading_hierarchy_project_overrides_user():

# ❌ Bad - Unclear test names
def test_git():
def test_template():
def test_config():
```

### Test Structure (AAA Pattern)
```python
def test_ollama_provider_generates_message_successfully():
    # Arrange
    config = {"model": "llama3.1", "base_url": "http://localhost:11434"}
    provider = OllamaProvider(config)
    prompt = "Generate a commit message"
    context = {"files_changed": 3, "lines_added": 50}
    
    # Act
    with requests_mock.Mocker() as m:
        m.post(f"{config['base_url']}/api/generate", json={"response": "feat: add new feature"})
        result = provider.generate(prompt, context)
    
    # Assert
    assert result == "feat: add new feature"
    assert m.call_count == 1
```

### Test Coverage Requirements
- **Unit Tests**: >80% line coverage
- **Integration Tests**: Cover main user workflows
- **Critical Paths**: 100% coverage for core functionality

## Configuration Standards

### pyproject.toml Structure
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "gitai"
version = "0.1.0"
description = "AI-powered commit and PR generation"
dependencies = [
    "click>=8.0",
    "GitPython>=3.1.30",
    "Jinja2>=3.1.0",
    "PyYAML>=6.0",
    "requests>=2.28.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=22.0.0",
    "isort>=5.0.0",
    "mypy>=1.0.0",
    "flake8>=5.0.0",
    "requests-mock>=1.9.0",
]

[project.scripts]
gitai = "gitai.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src/gitai --cov-report=html --cov-report=term-missing"

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true
```

## Git Standards

### Commit Message Format
```
type(scope): description

body (optional)

footer (optional)
```

#### Types
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Build process or auxiliary tool changes

#### Examples
```
feat(templates): add support for template inheritance

Implement Jinja2 template inheritance allowing teams to
extend base templates with custom sections.

Closes #123
```

### Branch Naming
```
# Feature branches
feature/template-inheritance
feature/openai-provider

# Bug fixes
fix/config-loading-error
fix/template-rendering-issue

# Documentation
docs/api-documentation
docs/user-guide

# Refactoring
refactor/provider-interface
refactor/error-handling
```

## Code Review Guidelines

### Review Checklist
- [ ] Code follows naming conventions
- [ ] Type hints are present and accurate
- [ ] Error handling is appropriate
- [ ] Tests are included and meaningful
- [ ] Documentation is updated if needed
- [ ] No hardcoded values or secrets
- [ ] Performance considerations addressed
- [ ] Security implications considered

### Review Comments Format
```
# ✅ Good - Constructive feedback
Consider using pathlib.Path instead of os.path for better cross-platform compatibility.

# ✅ Good - Explanation with suggestion
This could raise a KeyError if the template doesn't exist. 
Suggest using dict.get() with a default value or proper exception handling.

# ❌ Bad - Non-constructive
This is wrong.
Fix this.
```

## Security Standards

### Sensitive Data
- **No hardcoded secrets**: Use environment variables
- **Input validation**: Sanitize all user inputs
- **Path validation**: Prevent directory traversal
- **API keys**: Store in secure configuration, never in code

### Example Secure Patterns
```python
# ✅ Good - Environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ConfigurationError("OPENAI_API_KEY environment variable required")

# ✅ Good - Path validation
def _validate_template_path(self, path: str) -> Path:
    resolved_path = Path(path).resolve()
    if not resolved_path.is_relative_to(self.template_base):
        raise SecurityError(f"Template path outside allowed directory: {path}")
    return resolved_path
```

## Performance Standards

### Guidelines
- **Lazy loading**: Load resources only when needed
- **Caching**: Cache expensive operations (template parsing, config loading)
- **Timeouts**: All network operations must have timeouts
- **Resource cleanup**: Use context managers for file operations

### Performance Targets
- **Startup time**: <2 seconds for CLI commands
- **Generation time**: <30 seconds for typical operations
- **Memory usage**: <100MB for normal operations
- **Large repositories**: Handle repos with >10k files

## Tooling Configuration

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/flake8
    rev: 5.0.4
    hooks:
      - id: flake8
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
```

### VS Code Settings
```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

---

**Document**: Code Standards v1.0 (GitAI)  
**Last updated**: 2024-10-24  
**Focus**: Consistency, maintainability, and contributor experience