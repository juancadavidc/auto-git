# GitAI - AI-Powered Git Automation

AI-driven commit message and PR description generation with customizable templates and team configurations.

## 🚀 Quick Start

```bash
# Install GitAI
git clone <repo-url>
cd gitai && pip install -e .

# Setup configuration
gitai config --global

# Generate commit messages
git add .
gitai commit --preview           # Preview first
gitai commit                     # Apply to git
gitai commit -t minimal          # Use different template
gitai commit --preview --agentic # Agentic mode: LLM inspects diffs via tools

# Generate PR descriptions
gitai pr --base main            # Generate PR description
gitai pr --base main -o pr.md   # Save to file
gitai pr --base main -t gitlab  # Use GitLab template

# View available templates
gitai templates --list           # List commit templates
gitai templates --list --type pr # List PR templates
```

## ✨ Key Features

- **🤖 Multiple AI Providers**: OpenAI (GPT), Anthropic (Claude), Ollama, LMStudio (local)
- **🔄 Agentic Mode**: LLM iteratively inspects diffs via tool-calling before generating commit messages (Ollama, OpenAI, LMStudio)
- **📝 Smart Templates**: Conventional commits, GitHub/GitLab PR formats, **fully customizable with Jinja2**
- **⚙️ Team Configuration**: Shared templates, conventions, multi-tier config
- **🔍 Git Analysis**: Intelligent change detection and context building
- **📊 Observability**: Optional Langfuse integration for tracing LLM calls and tool executions
- **🛡️ Robust CLI**: Comprehensive validation, helpful errors, verbose logging
- **🎨 Easy Customization**: Create your own templates with rich variables (files, changes, types, etc.)

## 🤖 AI Provider Setup

### OpenAI (GPT-3.5, GPT-4)
```bash
export OPENAI_API_KEY="sk-your-openai-key"
gitai config --set-provider openai       # Set as default provider
gitai commit --preview                   # Use default provider
gitai pr --base main

# Or use directly without setting as default
gitai commit --preview -p openai
gitai pr --base main -p openai
```

### Anthropic (Claude)
```bash
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"
gitai config --set-provider anthropic    # Set as default provider
gitai commit --preview                   # Use default provider
gitai pr --base main

# Or use directly without setting as default
gitai commit --preview -p anthropic
gitai pr --base main -p anthropic
```

### Ollama (Local)
```bash
# Start Ollama with a model
ollama pull qwen2.5:7b
ollama serve

# Set as default provider (default after gitai config --global)
gitai config --set-provider ollama
gitai commit --preview
gitai pr --base main
```

### LMStudio (Local with GUI)
```bash
# 1. Download and open LMStudio (https://lmstudio.ai)
# 2. Download a model through the GUI
# 3. Start the local server (default port: 1234)

# Set as default provider
gitai config --set-provider lmstudio
gitai commit --preview
gitai pr --base main

# Or use directly without setting as default
gitai commit --preview -p lmstudio
gitai pr --base main -p lmstudio
```

### Configuration Files
```bash
# Copy example configurations
cp example-configs/openai-config.yaml ~/.config/gitai/config.yaml
cp example-configs/anthropic-config.yaml ~/.config/gitai/config.yaml
cp example-configs/multi-provider-config.yaml ~/.config/gitai/config.yaml
cp example-configs/agentic-config.yaml ~/.config/gitai/config.yaml  # Agentic + Langfuse

# Edit with your API keys
nano ~/.config/gitai/config.yaml
```

## 🔄 Agentic Mode

Agentic mode uses tool-calling to let the LLM iteratively inspect diffs before generating commit messages. Instead of sending the entire diff in one shot, the model calls tools to explore changes strategically.

### How It Works

1. The LLM receives the rendered template and calls `list_changed_files()` to see an overview of all changes
2. Based on the overview, it selectively calls `get_file_diff(file_path)` for the most relevant files
3. Optionally calls `get_change_summary()` for statistics
4. When it has enough context, it generates the final commit message

### Supported Providers

Agentic mode uses the OpenAI-compatible `/v1/chat/completions` endpoint with tool calling:
- **Ollama** - Requires a model with tool support (e.g., `qwen2.5:7b`, `llama3.1`)
- **OpenAI** - GPT-3.5-turbo, GPT-4, etc.
- **LMStudio** - Any model with tool-calling support
- **Anthropic** - Not supported (falls back to single-shot automatically)

### Configuration

```yaml
# In ~/.config/gitai/config.yaml
agentic:
  enabled: false        # Default agentic mode (overridden by --agentic flag)
  max_iterations: 10    # Max tool-calling iterations before forcing response
  max_diff_lines: 200   # Truncate large diffs (first half + last half)
```

### Observability with Langfuse

Enable Langfuse to trace every LLM call and tool execution in agentic mode:

```yaml
langfuse:
  enabled: true
  public_key: "pk-lf-..."
  secret_key: "sk-lf-..."
  host: "https://cloud.langfuse.com"  # or self-hosted
```

Install the optional dependency:
```bash
pip install -e ".[observability]"
```

## 📋 Implementation Status

### ✅ Completed Epics
| Epic | Status | Features |
|------|--------|----------|
| **Epic 1: Foundation** | ✅ **Complete** | Project setup, Git analysis, Provider interfaces, CLI framework |
| **Epic 2: Templates** | ✅ **Complete** | Template engine, Configuration hierarchy, Default templates |
| **Epic 3: CLI Commands** | ✅ **Complete** | Commit/PR/Config commands, Provider switching, Error handling |

### 🚧 Remaining Epics
| Epic | Priority | Key Documents |
|------|----------|---------------|
| **Epic 4: Testing** | P0 | [Code Standards](docs/code-standards.md#testing-standards) → [Source Tree](docs/source-tree.md#test-structure-tests) |
| **Epic 5: Polish** | P1 | [Architecture](docs/architecture-overview.md#extensibility-points) |
| **Epic 6: Pilot** | P1 | [Project Overview](docs/project-overview.md#team-adoption) |

### 🏗️ Architecture Reference
- **[Architecture Overview](docs/architecture-overview.md)** - System design, components, data flow
- **[Source Tree](docs/source-tree.md)** - File organization, directory structure
- **[Code Standards](docs/code-standards.md)** - Coding conventions, testing, tools

### 📈 Planning Documents
- **[Refined Roadmap](docs/roadmap-refined.md)** - Epic breakdown with timeline
- **[Project Overview](docs/project-overview.md)** - Features, use cases, vision
- **[Enterprise Plan](docs/enterprise-adoption-plan.md)** - Team adoption strategy

## 🚀 Development Workflow

### Starting a Story
1. Read **[Project Overview](docs/project-overview.md)** for context
2. Check **[Refined Roadmap](docs/roadmap-refined.md)** for story details
3. Follow **[Source Tree](docs/source-tree.md)** for file placement
4. Apply **[Code Standards](docs/code-standards.md)** for implementation
5. Reference **[Architecture Overview](docs/architecture-overview.md)** for component design

## 📝 Templates Guide

### What are Templates?

Templates control how GitAI formats commit messages and PR descriptions. They use the Jinja2 templating language and have access to rich git context (files changed, lines added/removed, change types, etc.).

### Available Templates

**Commit Templates** (`-t` flag):
- `conventional` (default) - Conventional Commits format (feat/fix/chore)
- `descriptive` - Detailed, descriptive messages
- `minimal` - Short, concise messages

**PR Templates** (`-t` flag):
- `github` (default) - GitHub-style PR descriptions with checklists
- `gitlab` - GitLab merge request format
- `standard` - Generic PR description format

### Using Templates

```bash
# View available templates
gitai templates --list                   # List commit templates
gitai templates --list --type pr         # List PR templates

# Show template content
gitai templates --show conventional      # View commit template
gitai templates --show github --type pr  # View PR template

# Use specific template
gitai commit -t conventional --preview   # Conventional commits (default)
gitai commit -t minimal --preview        # Short messages
gitai commit -t descriptive --preview    # Detailed messages

gitai pr --base main -t github          # GitHub PR format (default)
gitai pr --base main -t gitlab          # GitLab MR format
```

### Creating Custom Templates

Templates are Jinja2 files (`.j2`) stored in:
- **User templates**: `~/.config/gitai/templates/`
- **Team templates**: `./.gitai/templates/` (in project root)
- **Project templates**: `./.gitai-local/templates/` (git-ignored)

#### Template Structure

```
~/.config/gitai/templates/
├── commit/
│   └── my-custom.j2        # Your custom commit template
└── pr/
    └── my-custom.j2        # Your custom PR template
```

#### Example: Custom Commit Template

Create `~/.config/gitai/templates/commit/emoji.j2`:

```jinja
{# Emoji commit message template #}
{# description: Generates commit messages with emojis #}
{# variables: changes, repository, user #}

{%- if changes.is_feature %}✨ feat{% elif changes.is_fix %}🐛 fix{% elif changes.is_docs %}📚 docs{% elif changes.is_test %}✅ test{% else %}🔧 chore{% endif %}{% if changes.scope %}({{ changes.scope }}){% endif %}: {{ changes.summary }}

{%- if changes.body %}

{{ changes.body }}
{%- endif %}

📝 Files changed: {{ changes.affected_files|length }}
{%- if changes.lines_added %}
➕ Added: {{ changes.lines_added }} lines
{%- endif %}
{%- if changes.lines_deleted %}
➖ Removed: {{ changes.lines_deleted }} lines
{%- endif %}
```

Use it:
```bash
gitai commit -t emoji --preview
```

#### Example: Custom PR Template

Create `~/.config/gitai/templates/pr/detailed.j2`:

```jinja
{# Detailed PR template with impact analysis #}
{# description: Comprehensive PR description with detailed sections #}
{# variables: changes, repository, user, base_branch, head_branch #}

## 🎯 Objective

{{ changes.summary }}

## 📋 Changes Overview

**Branch**: `{{ head_branch }}` → `{{ base_branch }}`
**Files Changed**: {{ changes.affected_files|length }}
**Impact**: +{{ changes.lines_added }} -{{ changes.lines_deleted }} lines

### Modified Components
{%- for file in changes.modified_files %}
- **{{ file.path }}** (+{{ file.lines_added }} -{{ file.lines_deleted }})
  {%- if file.description %}
  - {{ file.description }}
  {%- endif %}
{%- endfor %}

{%- if changes.breaking_change %}

## ⚠️ Breaking Changes

{{ changes.breaking_change }}

**Migration Required**: Yes
{%- endif %}

## ✅ Testing Strategy

{%- if changes.test_files %}
**Test Coverage Updated**:
{%- for file in changes.test_files %}
- {{ file.path }}
{%- endfor %}
{%- else %}
- [ ] Unit tests added
- [ ] Integration tests updated
{%- endif %}
- [ ] Manual testing completed
- [ ] Edge cases validated

## 📚 Documentation

- [ ] README updated
- [ ] API docs updated
- [ ] Changelog entry added
- [ ] Migration guide (if breaking)

## 🔍 Review Focus

Please pay special attention to:
{%- if changes.is_refactor %}
- Code structure and organization changes
- Performance implications
{%- elif changes.is_feature %}
- New functionality and edge cases
- Integration with existing features
{%- elif changes.is_fix %}
- Root cause analysis
- Prevention of similar issues
{%- endif %}
```

Use it:
```bash
gitai pr --base main -t detailed
```

### Available Template Variables

Templates have access to these context variables:

**Common Variables**:
- `changes.summary` - AI-generated summary of changes
- `changes.body` - Optional detailed description
- `changes.scope` - Detected scope (file/module)
- `changes.affected_files` - List of all changed files
- `changes.added_files` - Newly created files
- `changes.modified_files` - Modified files
- `changes.deleted_files` - Deleted files
- `changes.test_files` - Test files modified
- `changes.lines_added` - Total lines added
- `changes.lines_deleted` - Total lines removed
- `changes.breaking_change` - Breaking change description (if any)

**Change Type Flags**:
- `changes.is_feature` - Is this a new feature?
- `changes.is_fix` - Is this a bug fix?
- `changes.is_refactor` - Is this a refactor?
- `changes.is_docs` - Is this a documentation change?
- `changes.is_test` - Is this a test change?

**File Information** (for each file in affected_files):
- `file.path` - File path
- `file.change_type` - "added", "modified", "deleted", "renamed"
- `file.lines_added` - Lines added in this file
- `file.lines_deleted` - Lines removed from this file
- `file.is_test` - Is this a test file?
- `file.is_config` - Is this a config file?
- `file.is_docs` - Is this a documentation file?
- `file.language` - Programming language

**Repository & User** (PR templates only):
- `repository.name` - Repository name
- `repository.branch` - Current branch
- `base_branch` - Target branch for PR
- `head_branch` - Source branch for PR
- `user.name` - Git user name
- `user.email` - Git user email

### Template Tips

1. **Use Jinja2 filters**: `{{ changes.summary|capitalize_first }}`
2. **Conditional sections**: `{% if changes.test_files %}...{% endif %}`
3. **Loop through files**: `{% for file in changes.modified_files %}...{% endfor %}`
4. **Macros for reusability**: Define functions within templates
5. **Extend base template**: Use `{% extends "../base.j2" %}` for consistency

## 💻 Command Reference

### Configuration Commands
```bash
gitai config --global                    # Initialize global configuration
gitai config --team <team-name>          # Setup team configuration
gitai config --show                      # Display current configuration
gitai config --show --verbose            # Show detailed configuration
gitai config --set-provider anthropic    # Set Anthropic as default provider
gitai config --set-provider openai       # Set OpenAI as default provider
gitai config --set-provider ollama       # Set Ollama as default provider
gitai config --set-provider lmstudio     # Set LMStudio as default provider
```

### Template Commands
```bash
gitai templates --list                   # List commit templates
gitai templates --list --type pr         # List PR templates
gitai templates --show conventional      # Show commit template content
gitai templates --show github --type pr  # Show PR template content
gitai templates --show minimal           # Show minimal commit template
gitai templates --show gitlab --type pr  # Show GitLab PR template

# See the "📝 Templates Guide" section above for:
# - How to create custom templates
# - Available template variables
# - Example custom templates
```

### Commit Generation
```bash
gitai commit --preview                   # Preview commit message
gitai commit                             # Generate and apply commit

# Templates (-t flag)
gitai commit -t conventional             # Conventional commits (default)
gitai commit -t descriptive              # Detailed commit messages
gitai commit -t minimal                  # Short, concise messages

# Providers (-p flag)
gitai commit -p openai                   # Use OpenAI
gitai commit -p anthropic                # Use Claude

# Agentic mode (-a flag)
gitai commit --preview --agentic         # LLM inspects diffs via tool-calling
gitai commit -a -p ollama --preview      # Agentic with specific provider
gitai commit -a -p openai --preview      # Works with OpenAI, Ollama, LMStudio

# Additional options
gitai commit --include-untracked         # Include untracked files
gitai commit -t emoji --preview          # Use custom template
```

### PR Generation
```bash
gitai pr --base main                     # Generate PR description
gitai pr --base develop -o pr.md         # Save to file

# Templates (-t flag)
gitai pr --base main -t github           # GitHub PR format (default)
gitai pr --base main -t gitlab           # GitLab MR format
gitai pr --base main -t standard         # Generic PR format

# Providers (-p flag)
gitai pr --base main -p anthropic        # Use Claude
gitai pr --base main -p openai           # Use OpenAI

# Combine options
gitai pr --base main -t detailed -o pr.md  # Custom template to file
```

### Development Commands
```bash
# Setup development environment
scripts/setup/install-dev.sh

# Code quality checks
scripts/development/format-code.sh
scripts/development/run-tests.sh
scripts/development/check-types.sh
```

## 📁 Quick Navigation

| Component | Implementation Guide | Tests |
|-----------|---------------------|-------|
| **Git Analysis** | [Architecture](docs/architecture-overview.md#3-git-analysis-coregit_analyzerpy) → [Source](docs/source-tree.md#source-code-structure-srcgitai) | [Test Structure](docs/source-tree.md#test-structure-tests) |
| **AI Providers** | [Architecture](docs/architecture-overview.md#4-ai-providers-providers) → [Standards](docs/code-standards.md#error-handling) | [Unit Tests](docs/code-standards.md#test-structure-aaa-pattern) |
| **Templates** | [Architecture](docs/architecture-overview.md#5-template-system-templates) → [Source](docs/source-tree.md#default-templates-structure-templates) | [Integration Tests](docs/code-standards.md#testing-standards) |
| **Configuration** | [Architecture](docs/architecture-overview.md#configuration-hierarchy) → [Source](docs/source-tree.md#configuration-structure-config) | [Coverage Requirements](docs/code-standards.md#test-coverage-requirements) |

## 🎯 Success Criteria

- ✅ **Setup**: < 5 minutes for new users *(Achieved with `gitai config --global`)*
- ✅ **Performance**: < 30 seconds per generation *(All providers responding quickly)*
- 🚧 **Quality**: > 80% test coverage, > 95% reliability *(Epic 4: Testing)*
- 🚧 **Adoption**: 3+ teams using successfully *(Epic 6: Pilot)*

## 🚀 Current Status

### ✅ **Ready for Production Use**
- **Full CLI Interface**: All commands functional with comprehensive validation
- **Multi-Provider Support**: OpenAI, Anthropic (Claude), Ollama, LMStudio with easy switching
- **Template System**: Conventional commits, GitHub/GitLab PR formats
- **Configuration Management**: User/team/project hierarchy with fallbacks
- **Error Handling**: Helpful error messages with suggestions

### 🔧 **Working Features**
```bash
# Core functionality (fully tested and working)
gitai config --global                    # ✅ Configuration setup
gitai commit --preview                   # ✅ Commit generation
gitai commit --preview --agentic         # ✅ Agentic commit generation
gitai pr --base main                     # ✅ PR generation
gitai templates --list                   # ✅ Template management

# Provider management (fully functional)
gitai config --set-provider anthropic    # ✅ Set default provider
gitai config --set-provider openai       # ✅ Switch providers easily
gitai commit -p openai                   # ✅ Override default per command
gitai commit -p anthropic                # ✅ Claude integration
gitai commit -p ollama                   # ✅ Local Ollama
gitai commit -p lmstudio                 # ✅ Local LMStudio

# Agentic mode (tool-calling loop)
gitai commit --preview -a                # ✅ Ollama agentic mode
gitai commit --preview -a -p openai      # ✅ OpenAI agentic mode
gitai commit --preview -a -p lmstudio    # ✅ LMStudio agentic mode
```

## 🔧 Troubleshooting

### Common Issues

**"No staged changes found"**
```bash
git add .                                # Stage your changes first
gitai commit --preview
```

**"Provider 'openai' not configured"**
```bash
export OPENAI_API_KEY="your-key"        # Set API key
# or configure in ~/.config/gitai/config.yaml
```

**"Template 'custom' not found"**
```bash
gitai templates --list                   # See available templates
gitai templates --show conventional      # View template content
```

**"Not in a git repository"**
```bash
git init                                 # Initialize git repo
# or navigate to existing git repository
```

**"Branch 'feature' does not exist"**
```bash
git branch -a                            # List all branches
gitai pr --base main                     # Use existing branch
```

## 📖 Documentation

- **Users**: [Project Overview](docs/project-overview.md)
- **Developers**: [Architecture Overview](docs/architecture-overview.md) + [Code Standards](docs/code-standards.md)
- **Contributors**: [Source Tree](docs/source-tree.md) + [Refined Roadmap](docs/roadmap-refined.md)
- **Teams**: [Enterprise Plan](docs/enterprise-adoption-plan.md)

---

**Status**: 🚀 **Epic 1-3 Complete** → Core functionality ready for use!
**Next**: Epic 4 (Testing & Quality Assurance) → Epic 5 (Polish) → Epic 6 (Team Pilot)
