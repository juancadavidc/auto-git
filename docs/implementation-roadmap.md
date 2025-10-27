# Implementation Roadmap - GitAI

## Overview

Simplified roadmap for implementing the Python version with focused scope: automated commit messages and PR descriptions with configurable templates per team.

## Roadmap Objectives

### Core Deliverables
- ✅ Functional CLI: `gitai commit` and `gitai pr`
- ✅ Template system with Jinja2
- ✅ AI provider (Ollama) integrated
- ✅ Per-team configuration
- ✅ Setup < 5 minutes per team

### Success Criteria
- **Functionality**: Feature parity with current bash script
- **Usability**: Intuitive CLI, clear messages
- **Extensibility**: Easy to add providers/templates
- **Adoption**: At least 2 teams using in pilot

## Implementation Phases

### 📦 Phase 1: Setup and Foundations (Week 1)
**Objective**: Establish Python structure and basic dependencies

#### Day 1-2: Project Setup
- [ ] **Project structure**
  ```bash
  mkdir -p src/gitai/{commands,core,templates,config,providers,utils}
  mkdir -p templates/{commit,pr}
  mkdir -p config/
  mkdir -p tests/{unit,integration}
  ```

- [ ] **pyproject.toml and dependencies**
  ```toml
  [project]
  name = "gitai"
  dependencies = [
      "click>=8.0",
      "GitPython>=3.1",
      "Jinja2>=3.1", 
      "PyYAML>=6.0",
      "requests>=2.28",
      "pydantic>=2.0"
  ]
  ```

- [ ] **Basic CLI entry point**
  ```python
  # src/gitai/cli.py
  import click
  
  @click.group()
  def main():
      """GitAI - AI-powered commit and PR generation"""
      pass
  
  @main.command()
  def commit():
      click.echo("Commit command - TODO")
  
  @main.command() 
  def pr():
      click.echo("PR command - TODO")
  ```

#### Day 3-4: Core Components Skeleton
- [ ] **Basic Git Analyzer**
  ```python
  # src/gitai/core/git_analyzer.py
  from git import Repo
  
  class GitAnalyzer:
      def get_staged_changes(self):
          # Basic implementation
          pass
  ```

- [ ] **Provider interface**
  ```python
  # src/gitai/providers/base.py
  from abc import ABC, abstractmethod
  
  class BaseProvider(ABC):
      @abstractmethod
      def generate(self, prompt: str, context: dict) -> str:
          pass
  ```

- [ ] **Configuration models**
  ```python
  # src/gitai/config/models.py
  from pydantic import BaseModel
  
  class AppConfig(BaseModel):
      default_provider: str = "ollama"
      # Basic config structure
  ```

#### Day 5: Testing Setup
- [ ] **Test framework setup** (pytest)
- [ ] **Basic unit tests** for components
- [ ] **Basic CI/CD** (GitHub Actions)
- [ ] **Pre-commit hooks**

---

### 🔧 Phase 2: Core Functionality (Week 2)
**Objective**: Implement basic generation functionality

#### Day 1-2: Git Analysis
- [ ] **Staged changes analysis**
  ```python
  def get_staged_changes(self) -> DiffAnalysis:
      # Parse git diff --staged
      # Categorize file changes
      # Extract meaningful context
  ```

- [ ] **Branch changes analysis**
  ```python
  def get_branch_changes(self, base='main') -> DiffAnalysis:
      # Parse git diff main...HEAD
      # Analyze commit history
      # Extract PR context
  ```

- [ ] **File change categorization**
  - New files, modifications, deletions
  - File type detection
  - Change magnitude (lines added/removed)

#### Day 3-4: Ollama Provider
- [ ] **Migrate logic from bash script**
  ```python
  class OllamaProvider(BaseProvider):
      def generate(self, prompt: str, context: dict) -> str:
          # HTTP calls to Ollama API
          # Error handling
          # Response parsing
  ```

- [ ] **Configuration integration**
  - Model selection
  - Temperature, context window
  - Base URL configuration

- [ ] **Error handling and retries**
  - Network errors
  - Model not available
  - Response validation

#### Day 5: Template Engine
- [ ] **Jinja2 integration**
  ```python
  class TemplateManager:
      def render_template(self, template: str, context: dict) -> str:
          # Jinja2 rendering
          # Variable validation
          # Error handling
  ```

- [ ] **Default templates**
  - Commit: conventional, descriptive, minimal
  - PR: GitHub, GitLab, standard

---

### 🎯 Phase 3: CLI Commands (Week 3) 
**Objective**: Functional CLI with polished UX

#### Day 1-2: Commit Command
- [ ] **Command implementation**
  ```python
  @main.command()
  @click.option('--template', help='Template to use')
  @click.option('--preview', is_flag=True, help='Preview only')
  def commit(template, preview):
      # Get staged changes
      # Generate commit message
      # Preview or apply
  ```

- [ ] **Integration flow**
  ```python
  def handle_commit(template, preview):
      analyzer = GitAnalyzer()
      changes = analyzer.get_staged_changes()
      
      config = load_config()
      provider = get_provider(config)
      
      template_content = load_template('commit', template)
      prompt = render_template(template_content, changes)
      
      message = provider.generate(prompt)
      
      if preview:
          click.echo(message)
      else:
          apply_commit_message(message)
  ```

#### Day 3-4: PR Command  
- [ ] **Command implementation**
  ```python
  @main.command()
  @click.option('--base', default='main', help='Base branch')
  @click.option('--output', help='Output file')
  def pr(base, output):
      # Get branch changes
      # Generate PR description
      # Output to file/stdout
  ```

- [ ] **PR generation flow**
  - Branch vs base analysis
  - Commit message aggregation
  - Template rendering
  - Output formatting

#### Day 5: Config Command
- [ ] **Team setup**
  ```python
  @main.command()
  @click.argument('action')  # init, show, edit
  def config(action):
      # Team configuration management
      # Template path setup
      # Provider configuration
  ```

---

### 🚀 Phase 4: Polish and Extension (Week 4)
**Objective**: UX polish and extensibility

#### Day 1-2: Configuration System
- [ ] **YAML configuration hierarchy**
  ```yaml
  # config/default.yaml (installation)
  providers:
    ollama:
      model: "llama3.1"
      base_url: "http://localhost:11434"
  
  templates:
    default_commit: "conventional"
    default_pr: "standard"
  ```

- [ ] **User global configuration**
  ```yaml
  # ~/.config/gitai/config.yaml
  default_provider: "ollama"
  current_team: "frontend"
  
  # ~/.config/gitai/teams/frontend.yaml
  extends: "default"
  templates:
    default_commit: "semantic"
  ```

- [ ] **Project-specific overrides**
  ```yaml
  # any-git-project/gitai.yaml (optional)
  provider:
    model: "gpt-4"  # Override for this project
  ```

- [ ] **Configuration validation**
  - Pydantic models
  - Required field validation
  - Path existence checks

#### Day 3-4: Advanced Template System
- [ ] **Template discovery**
  - Multiple template paths
  - Team-specific templates
  - Fallback logic

- [ ] **Variable validation**
  - Required variables detection
  - Context validation
  - Helpful error messages

- [ ] **Template inheritance**
  ```jinja2
  {# templates/commit/team-specific.txt #}
  {% extends "conventional.txt" %}
  {% block footer %}
  Team: {{ team_name }}
  {% endblock %}
  ```

#### Day 5: Additional Provider
- [ ] **OpenAI provider** (optional)
  ```python
  class OpenAIProvider(BaseProvider):
      def generate(self, prompt: str, context: dict) -> str:
          # OpenAI API integration
          # API key management
          # Rate limiting
  ```

- [ ] **Provider selection logic**
  - Configuration-based selection
  - Fallback providers
  - Health checks

---

## Testing and Quality

### Unit Tests (Continuous)
```python
# tests/unit/test_git_analyzer.py
def test_staged_changes_parsing():
    # Mock git repo
    # Test diff parsing
    # Verify DiffAnalysis output

# tests/unit/test_template_manager.py  
def test_template_rendering():
    # Test Jinja2 integration
    # Variable injection
    # Error cases
```

### Integration Tests (Week 4)
```python
# tests/integration/test_commit_flow.py
def test_end_to_end_commit():
    # Setup test repo with staged changes
    # Run commit command
    # Verify generated message
```

### Manual Testing (Continuous)
- [ ] Test with real repos
- [ ] Different types of changes
- [ ] Error scenarios
- [ ] Performance with large diffs

## Deployment and Adoption

### Distribution
- [ ] **Global installation** (primary)
  ```bash
  # One-time global setup
  git clone <repo>
  cd gitai
  pip install -e .
  ```

- [ ] **User onboarding script**
  ```bash
  # Per-user setup (creates ~/.config/gitai/)
  gitai config init --global
  gitai config team frontend  # Optional team setup
  ```

- [ ] **PyPI package** (optional, for future)

### Team Onboarding
- [ ] **Global tool documentation**
  - How to install once, use anywhere
  - Configuration hierarchy explanation
  - Project-specific overrides guide

- [ ] **Team setup examples**
  - Frontend team config
  - Backend team config
  - Custom templates per team

- [ ] **Project integration guide**
  - Optional gitai.yaml
  - Git hooks integration
  - CI/CD usage examples

### Pilot Testing
- [ ] **Select 2 teams** for initial pilot
- [ ] **Gather feedback** on UX and functionality
- [ ] **Iterate** based on real usage
- [ ] **Document learnings**

## Success Metrics

### Functional Metrics
- [ ] **Feature parity**: Same output quality as bash version
- [ ] **Performance**: < 30 seconds per generation
- [ ] **Reliability**: > 95% success rate
- [ ] **Setup time**: < 5 minutes for new team

### Code Quality Metrics
- [ ] **Test coverage**: > 80%
- [ ] **Type coverage**: > 90% with mypy
- [ ] **Linting**: Clean flake8/black
- [ ] **Documentation**: All public APIs documented

### Adoption Metrics
- [ ] **Teams onboarded**: 2+ teams successfully using
- [ ] **Daily usage**: 10+ generations per day
- [ ] **Feedback score**: 4/5 average satisfaction
- [ ] **Contribution**: 1+ external contribution

## Risk Mitigation

### Technical Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| GitPython complexity | Medium | Medium | Start simple, iterate |
| Jinja2 template errors | Low | Low | Good validation, tests |
| Provider API changes | Low | Medium | Abstract interface |
| Performance issues | Low | Medium | Benchmarking, optimization |

### Adoption Risks
| Risk | Probability | Impact | Mitigation |
|------|-------------|---------|------------|
| Setup complexity | Medium | High | Simple install script |
| Team resistance | Medium | High | Good documentation, demos |
| Configuration confusion | Medium | Medium | Clear examples, validation |

## Timeline Summary

```
Week │ Focus               │ Key Deliverable
─────┼────────────────────┼─────────────────────────────
  1  │ Setup & Foundation │ Project structure, CLI skeleton
  2  │ Core Functionality │ Git analysis, Ollama provider  
  3  │ CLI Commands       │ Working commit/pr commands
  4  │ Polish & Extension │ Config system, additional features
```

### Final Deliverables
- ✅ Working CLI: `gitai commit/pr`
- ✅ Template system with team customization
- ✅ Configuration management
- ✅ Documentation and examples
- ✅ 2 teams using successfully
- ✅ Extensible architecture for future features

---

**Document**: Implementation Roadmap v2.0 (GitAI)  
**Last updated**: 2024-10-24  
**Focus**: Focused scope, practical implementation