# Architecture Design - GitAI

## Overview

Simple yet extensible Python architecture for automating commit messages and PR descriptions. Designed with SOLID principles to facilitate contributions and future extensibility.

## Design Principles

### 1. Simplicity First
- **Single purpose**: Commit messages and PR descriptions
- **Minimal dependencies**: Only essentials
- **Intuitive CLI**: Clear and direct commands
- **Fast setup**: < 5 minutes per team

### 2. Controlled Extensibility
- **Open for extension**: AI providers, templates, outputs
- **Closed for modification**: Stable core logic
- **Plugin architecture**: Additional features without core complexity
- **Clear interfaces**: Well-defined contracts

### 3. Developer Experience
- **Contributor friendly**: Idiomatic Python
- **Well documented**: Clear APIs, examples
- **Testable**: Unit and integration tests
- **Debuggable**: Clear error messages, logging

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface                          │
│                    (Click/Typer)                           │
├─────────────────────────────────────────────────────────────┤
│                 Command Handlers                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Commit    │ │      PR     │ │   Config    │          │
│  │  Command    │ │   Command   │ │  Command    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                     Core Engine                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │     Git     │ │  Message    │ │     PR      │          │
│  │  Analyzer   │ │ Generator   │ │ Generator   │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│               Template & Configuration                      │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │  Template   │ │   Config    │ │  Context    │          │
│  │  Manager    │ │  Manager    │ │  Builder    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
├─────────────────────────────────────────────────────────────┤
│                   Provider Layer                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │   Ollama    │ │   OpenAI    │ │   Future    │          │
│  │  Provider   │ │  Provider   │ │  Providers  │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

### Installation Directory (Global Tool)
```
gitai/
├── src/gitai/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point
│   ├── commands/                 # Command implementations
│   │   ├── __init__.py
│   │   ├── commit.py
│   │   ├── pr.py
│   │   └── config.py
│   ├── core/                     # Core business logic
│   │   ├── __init__.py
│   │   ├── git_analyzer.py       # Git operations
│   │   ├── message_generator.py  # Commit message logic
│   │   ├── pr_generator.py       # PR description logic
│   │   └── context_builder.py    # Context preparation
│   ├── templates/                # Template management
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── renderer.py
│   ├── config/                   # Configuration system
│   │   ├── __init__.py
│   │   ├── manager.py
│   │   └── models.py             # Pydantic models
│   ├── providers/                # AI provider implementations
│   │   ├── __init__.py
│   │   ├── base.py               # Base provider interface
│   │   ├── ollama.py
│   │   └── openai.py
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── logger.py
│       └── exceptions.py
├── templates/                    # Default templates
│   ├── commit/
│   │   ├── conventional.txt
│   │   ├── descriptive.txt
│   │   └── minimal.txt
│   └── pr/
│       ├── github.md
│       ├── gitlab.md
│       └── standard.md
├── config/
│   └── default.yaml              # Base configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/
└── pyproject.toml
```

### User Configuration (Created at Runtime)
```
~/.config/gitai/
├── config.yaml            # User global preferences
└── teams/                 # Team-specific configurations
    ├── frontend.yaml
    ├── backend.yaml
    └── devops.yaml
```

### Project-Specific (Optional, Per Git Repo)
```
~/projects/any-git-project/
├── .git/
├── gitai.yaml               # Project-specific overrides
└── templates/               # Project-specific templates
    ├── commit/
    │   └── project-style.txt
    └── pr/
        └── project-pr.md
```

## Detailed Components

### 1. CLI Interface

```python
# src/gitai/cli.py
import click
from .commands import commit, pr, config

@click.group()
@click.version_option()
def main():
    """GitAI - AI-powered commit and PR generation"""
    pass

@main.command()
@click.option('--template', help='Template to use')
@click.option('--provider', help='AI provider')
@click.option('--preview', is_flag=True, help='Preview without applying')
def commit(template, provider, preview):
    """Generate commit message from staged changes"""
    commit.handle_commit(template, provider, preview)

@main.command()
@click.option('--base', default='main', help='Base branch')
@click.option('--template', help='Template to use')
@click.option('--output', help='Output file')
def pr(base, template, output):
    """Generate PR description from branch changes"""
    pr.handle_pr(base, template, output)
```

### 2. Git Analyzer

```python
# src/gitai/core/git_analyzer.py
from dataclasses import dataclass
from typing import List, Optional
from git import Repo
from pathlib import Path

@dataclass
class FileChange:
    path: str
    change_type: str  # A, M, D, R
    lines_added: int
    lines_removed: int
    content_preview: str

@dataclass
class DiffAnalysis:
    files_changed: List[FileChange]
    total_additions: int
    total_deletions: int
    change_summary: str
    commit_context: dict

class GitAnalyzer:
    def __init__(self, repo_path: Optional[Path] = None):
        self.repo = Repo(repo_path or Path.cwd())

    def get_staged_changes(self) -> DiffAnalysis:
        """Analyze staged changes for commit message generation"""
        staged_diff = self.repo.git.diff('--staged', '--name-status')
        # Implementation...

    def get_branch_changes(self, base_branch: str = 'main') -> DiffAnalysis:
        """Analyze branch changes vs base for PR description"""
        branch_diff = self.repo.git.diff(f'{base_branch}...HEAD', '--name-status')
        # Implementation...

    def get_commit_context(self) -> dict:
        """Get current repo context"""
        return {
            'branch': self.repo.active_branch.name,
            'author': self.repo.config_reader().get_value('user', 'name'),
            'email': self.repo.config_reader().get_value('user', 'email'),
            'repo_name': Path(self.repo.working_dir).name
        }
```

### 3. Provider Interface

```python
# src/gitai/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseProvider(ABC):
    """Base interface for AI providers"""

    @abstractmethod
    def generate(self, prompt: str, context: Dict[str, Any]) -> str:
        """Generate content using AI provider"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate provider configuration"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Check if provider is available"""
        pass

# src/gitai/providers/ollama.py
import requests
from .base import BaseProvider

class OllamaProvider(BaseProvider):
    def __init__(self, config: dict):
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = config.get('model', 'llama3.1')
        self.temperature = config.get('temperature', 0.4)

    def generate(self, prompt: str, context: dict) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                'model': self.model,
                'prompt': prompt,
                'temperature': self.temperature,
                'stream': False
            }
        )
        return response.json()['response']

    def validate_config(self, config: dict) -> bool:
        required_fields = ['model']
        return all(field in config for field in required_fields)

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
```

### 4. Template System

```python
# src/gitai/templates/manager.py
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from typing import Dict, Any

class TemplateManager:
    def __init__(self, template_paths: List[Path]):
        self.template_paths = template_paths
        self.env = Environment(
            loader=FileSystemLoader([str(p) for p in template_paths])
        )

    def get_template(self, template_name: str, template_type: str) -> str:
        """Load template by name and type (commit/pr)"""
        template_file = f"{template_type}/{template_name}.txt"

        # Try team-specific first, then default
        for path in self.template_paths:
            template_path = path / template_file
            if template_path.exists():
                return template_path.read_text()

        raise FileNotFoundError(f"Template not found: {template_file}")

    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template with context data"""
        template = self.env.from_string(template_content)
        return template.render(**context)

    def list_templates(self, template_type: str) -> List[str]:
        """List available templates of given type"""
        templates = []
        for path in self.template_paths:
            type_dir = path / template_type
            if type_dir.exists():
                templates.extend([
                    f.stem for f in type_dir.glob('*.txt')
                    if f.is_file()
                ])
        return sorted(set(templates))
```

### 5. Configuration System

```python
# src/gitai/config/models.py
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Dict, Any, Optional, List

class ProviderConfig(BaseModel):
    name: str
    base_url: Optional[str] = None
    model: str
    temperature: float = 0.4
    api_key_env: Optional[str] = None

class TemplateConfig(BaseModel):
    default_commit: str = "conventional"
    default_pr: str = "standard"
    paths: List[Path] = Field(default_factory=list)

class TeamConfig(BaseModel):
    name: str
    provider: ProviderConfig
    templates: TemplateConfig
    git_config: Dict[str, Any] = Field(default_factory=dict)

class AppConfig(BaseModel):
    providers: Dict[str, ProviderConfig]
    templates: TemplateConfig
    default_provider: str
    team: Optional[TeamConfig] = None

# src/gitai/config/manager.py
import yaml
from pathlib import Path
from .models import AppConfig

class ConfigManager:
    def __init__(self, working_dir: Optional[Path] = None):
        self.working_dir = working_dir or Path.cwd()
        self.user_config_dir = Path.home() / ".config" / "gitai"
        self.install_config_dir = self._get_install_config_dir()

    def load_config(self, team_name: Optional[str] = None) -> AppConfig:
        """Load configuration with hierarchy: project > user > default"""
        config = self._load_default_config()

        # Apply user global config
        user_config_path = self.user_config_dir / "config.yaml"
        if user_config_path.exists():
            user_config = self._load_yaml(user_config_path)
            config = self._merge_configs(config, user_config)

        # Apply team config if specified
        if team_name:
            team_config_path = self.user_config_dir / "teams" / f"{team_name}.yaml"
            if team_config_path.exists():
                team_config = self._load_yaml(team_config_path)
                config = self._merge_configs(config, team_config)

        # Apply project-specific config (highest priority)
        project_config_path = self.working_dir / "gitai.yaml"
        if project_config_path.exists():
            project_config = self._load_yaml(project_config_path)
            config = self._merge_configs(config, project_config)

        return AppConfig(**config)

    def _load_default_config(self) -> dict:
        """Load default configuration from installation"""
        default_path = self.install_config_dir / "default.yaml"
        return self._load_yaml(default_path)

    def _get_install_config_dir(self) -> Path:
        """Get installation config directory"""
        # This would be the config/ dir in the installed package
        import gitai
        return Path(gitai.__file__).parent.parent / "config"

    def _load_yaml(self, path: Path) -> dict:
        with open(path) as f:
            return yaml.safe_load(f)

    def _merge_configs(self, base: dict, override: dict) -> dict:
        """Deep merge configuration dictionaries"""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
```

## Data Flow

### Commit Message Generation
```
1. CLI: gitai commit
2. GitAnalyzer: get_staged_changes()
3. ContextBuilder: build context from diff + config
4. TemplateManager: load commit template
5. Provider: generate with template + context
6. Output: preview or apply to commit
```

### PR Description Generation
```
1. CLI: gitai pr --base main
2. GitAnalyzer: get_branch_changes(base)
3. ContextBuilder: build context from diff + commits
4. TemplateManager: load PR template
5. Provider: generate with template + context
6. Output: file or stdout
```

## Extensibility

### Adding New Provider
```python
# src/gitai/providers/anthropic.py
from .base import BaseProvider

class AnthropicProvider(BaseProvider):
    def generate(self, prompt: str, context: dict) -> str:
        # Implementation
        pass
```

### Adding New Template
```
# templates/commit/semantic.txt
{{ change_type }}({{ scope }}): {{ description }}

{{ detailed_description }}

{% if breaking_changes %}
BREAKING CHANGE: {{ breaking_changes }}
{% endif %}
```

### Adding Command
```python
# src/gitai/commands/review.py
@click.command()
def review():
    """Review branch against main"""
    # Future functionality
```

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_git_analyzer.py
def test_staged_changes_analysis():
    analyzer = GitAnalyzer(test_repo_path)
    changes = analyzer.get_staged_changes()
    assert changes.files_changed
    assert changes.total_additions >= 0
```

### Integration Tests
```python
# tests/integration/test_end_to_end.py
def test_commit_generation_flow():
    # Setup test repo with staged changes
    # Run command
    # Verify output
```

## Performance Considerations

### Optimizations
- **Lazy loading**: Load providers only when needed
- **Caching**: Cache template parsing, config loading
- **Streaming**: Stream large diffs for analysis
- **Timeouts**: Reasonable timeouts for AI providers

### Resource Management
- **Memory**: Efficient diff processing for large changes
- **Network**: Retry logic for AI API calls
- **Disk**: Minimal file I/O, efficient template loading

---

**Document**: Architecture Design v2.0 (GitAI)
**Last updated**: 2024-10-24
**Focus**: Simple, extensible, contributor-friendly
