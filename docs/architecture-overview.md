# Architecture Overview - GitAI

## System Overview

GitAI is a Python-based CLI tool that automates the generation of commit messages and pull request descriptions using AI. The architecture follows a modular, layered design that separates concerns and enables extensibility.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
│                   (CLI Commands)                            │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Command Layer                              │
│     Commit Command  │  PR Command  │  Config Command       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Business Logic Layer                       │
│   Git Analyzer  │  Generators  │  Context Builder          │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                 Infrastructure Layer                        │
│  Templates  │  Configuration  │  AI Providers  │  Utils    │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. CLI Interface (`cli.py`)
**Responsibility**: Command-line interface and user interaction

```python
# Main entry point
@click.group()
def main():
    """GitAI - AI-powered commit and PR generation"""

@main.command()
def commit():
    """Generate commit message from staged changes"""

@main.command()
def pr():
    """Generate PR description from branch changes"""
```

**Key Features**:
- Click-based command structure
- Option parsing and validation
- Error handling and user feedback
- Help system integration

### 2. Command Handlers (`commands/`)
**Responsibility**: Execute specific CLI commands with business logic coordination

#### Commit Command (`commands/commit.py`)
```python
def handle_commit(template: str, provider: str, preview: bool):
    # 1. Load configuration
    # 2. Analyze staged changes
    # 3. Build context
    # 4. Render template
    # 5. Generate with AI
    # 6. Apply or preview
```

#### PR Command (`commands/pr.py`)
```python
def handle_pr(base: str, template: str, output: str):
    # 1. Load configuration
    # 2. Analyze branch changes
    # 3. Build context
    # 4. Render template
    # 5. Generate with AI
    # 6. Output result
```

### 3. Git Analysis (`core/git_analyzer.py`)
**Responsibility**: Extract meaningful information from git repository

```python
class GitAnalyzer:
    def get_staged_changes(self) -> DiffAnalysis
    def get_branch_changes(self, base: str) -> DiffAnalysis
    def get_commit_context(self) -> dict
```

**Data Models**:
```python
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
```

### 4. AI Providers (`providers/`)
**Responsibility**: Interface with various AI services for content generation

#### Base Provider Interface
```python
class BaseProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: dict) -> str

    @abstractmethod
    def validate_config(self, config: dict) -> bool

    @abstractmethod
    def health_check(self) -> bool
```

#### Ollama Provider (`providers/ollama.py`)
```python
class OllamaProvider(BaseProvider):
    def __init__(self, config: dict):
        self.base_url = config.get('base_url')
        self.model = config.get('model')

    def generate(self, prompt: str, context: dict) -> str:
        # HTTP request to Ollama API
        # Error handling and retry logic
        # Response parsing and validation
```

### 5. Template System (`templates/`)
**Responsibility**: Template discovery, loading, and rendering

#### Template Manager (`templates/manager.py`)
```python
class TemplateManager:
    def get_template(self, name: str, type: str) -> str
    def list_templates(self, type: str) -> List[str]
    def validate_template(self, content: str) -> bool
```

#### Template Renderer (`templates/renderer.py`)
```python
class TemplateRenderer:
    def render(self, template: str, context: dict) -> str
    def validate_variables(self, template: str, context: dict) -> bool
```

### 6. Configuration System (`config/`)
**Responsibility**: Hierarchical configuration management

#### Configuration Manager (`config/manager.py`)
```python
class ConfigManager:
    def load_config(self, team: str = None) -> AppConfig
    def save_config(self, config: AppConfig) -> None
    def get_template_paths(self) -> List[Path]
```

**Configuration Hierarchy**:
1. **Default**: Installed package defaults
2. **User Global**: `~/.config/gitai/config.yaml`
3. **Team**: `~/.config/gitai/teams/{team}.yaml`
4. **Project**: `{project}/.gitai/config.yaml`

## Data Flow

### Commit Generation Flow
```
1. CLI: gitai commit --template conventional
   │
2. Command Handler: commands/commit.py
   │  ├─ Load configuration (config hierarchy)
   │  ├─ Get staged changes (GitAnalyzer)
   │  ├─ Build context (ContextBuilder)
   │  ├─ Load template (TemplateManager)
   │  ├─ Render template (TemplateRenderer)
   │  ├─ Generate message (AI Provider)
   │  └─ Apply or preview (Git operations)
   │
3. Output: Commit applied or preview shown
```

### PR Generation Flow
```
1. CLI: gitai pr --base main --output pr.md
   │
2. Command Handler: commands/pr.py
   │  ├─ Load configuration (config hierarchy)
   │  ├─ Get branch changes (GitAnalyzer)
   │  ├─ Build context (ContextBuilder)
   │  ├─ Load template (TemplateManager)
   │  ├─ Render template (TemplateRenderer)
   │  ├─ Generate description (AI Provider)
   │  └─ Write to file or stdout
   │
3. Output: PR description file created
```

## Component Interactions

### Configuration Loading
```
ConfigManager
├─ Loads default.yaml from package
├─ Merges ~/.config/gitai/config.yaml
├─ Merges ~/.config/gitai/teams/{team}.yaml
├─ Merges {project}/.gitai/config.yaml
└─ Returns merged AppConfig object
```

### Template Resolution
```
TemplateManager
├─ Searches project templates: {project}/.gitai/templates/
├─ Searches user templates: ~/.config/gitai/templates/
├─ Searches team templates: ~/.config/gitai/teams/{team}/templates/
├─ Searches default templates: package/templates/
└─ Returns first match found
```

### Provider Selection
```
ProviderFactory
├─ Gets provider name from config
├─ Validates provider configuration
├─ Performs health check
├─ Falls back to alternative if needed
└─ Returns configured provider instance
```

## Error Handling Strategy

### Exception Hierarchy
```python
GitAIError (Base)
├─ GitAnalysisError
│  ├─ NoStagedChangesError
│  ├─ InvalidRepositoryError
│  └─ GitOperationError
├─ TemplateError
│  ├─ TemplateNotFoundError
│  ├─ TemplateRenderError
│  └─ TemplateValidationError
├─ ProviderError
│  ├─ ProviderUnavailableError
│  ├─ ProviderConfigError
│  └─ GenerationTimeoutError
└─ ConfigurationError
   ├─ InvalidConfigError
   ├─ MissingConfigError
   └─ ConfigValidationError
```

### Error Recovery
- **Graceful degradation**: Fall back to simpler templates
- **Provider fallback**: Try alternative AI providers
- **User guidance**: Clear error messages with suggestions
- **Logging**: Detailed logs for debugging

## Security Architecture

### Input Validation
- **Path validation**: Prevent directory traversal
- **Template sanitization**: Safe Jinja2 rendering
- **Configuration validation**: Pydantic models
- **Git operation safety**: Validate repository state

### Secret Management
- **Environment variables**: API keys stored securely
- **No hardcoded secrets**: Configuration-based secrets
- **Secure defaults**: Safe default configurations
- **Access control**: File permission management

## Performance Considerations

### Optimization Strategies
- **Lazy loading**: Load components only when needed
- **Caching**: Cache parsed templates and configurations
- **Streaming**: Handle large diffs efficiently
- **Timeouts**: Reasonable timeouts for all operations

### Resource Management
- **Memory efficiency**: Process large repositories incrementally
- **Network optimization**: Retry logic with exponential backoff
- **File I/O**: Minimal disk operations, efficient reading
- **Concurrency**: Async operations where beneficial

## Testing Architecture

### Test Strategy
```
Unit Tests (80%+ coverage)
├─ Component isolation with mocks
├─ Edge case handling
├─ Error condition testing
└─ Performance benchmarks

Integration Tests
├─ End-to-end workflows
├─ Component interaction testing
├─ Configuration hierarchy testing
└─ Real git repository testing

System Tests
├─ CLI command testing
├─ User workflow simulation
├─ Error scenario testing
└─ Performance validation
```

### Test Infrastructure
- **Fixtures**: Sample repositories, configurations, templates
- **Mocking**: AI provider responses, git operations
- **Factories**: Test data generation
- **Assertions**: Custom assertions for domain objects

## Extensibility Points

### Adding New Providers
```python
# 1. Implement BaseProvider interface
class CustomProvider(BaseProvider):
    def generate(self, prompt: str, context: dict) -> str:
        # Custom implementation

# 2. Register in provider factory
# 3. Add configuration schema
# 4. Add tests
```

### Adding New Commands
```python
# 1. Create command handler
@main.command()
def review():
    """Review branch changes"""

# 2. Implement business logic
# 3. Add templates if needed
# 4. Add configuration options
```

### Adding New Template Features
```python
# 1. Extend TemplateRenderer
# 2. Add new Jinja2 filters/functions
# 3. Update template validation
# 4. Add documentation
```

## Deployment Architecture

### Installation Model
- **Global installation**: Single install, use anywhere
- **User configuration**: Per-user settings and templates
- **Project overrides**: Optional project-specific config
- **Zero setup**: Works immediately in any git repository

### Distribution Strategy
- **PyPI package**: Standard Python distribution
- **Git installation**: Development and latest features
- **Docker image**: Containerized deployment option
- **Binary distribution**: Standalone executables (future)

## Monitoring and Observability

### Logging Strategy
- **Structured logging**: JSON format for parsing
- **Log levels**: Debug, Info, Warning, Error, Critical
- **Context preservation**: Include relevant context in logs
- **Performance metrics**: Operation timing and resource usage

### Metrics Collection (Future)
- **Usage metrics**: Command frequency, template usage
- **Performance metrics**: Generation time, success rate
- **Error tracking**: Error types and frequency
- **User feedback**: Satisfaction and improvement suggestions

---

**Document**: Architecture Overview v1.0 (GitAI)
**Last updated**: 2024-10-24
**Focus**: System design and component interactions
