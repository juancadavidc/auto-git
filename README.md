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

# Generate PR descriptions
gitai pr --base main            # Generate PR description
gitai pr --base main -o pr.md   # Save to file
```

## ✨ Key Features

- **🤖 Multiple AI Providers**: OpenAI (GPT), Anthropic (Claude), Ollama, LMStudio (local)
- **📝 Smart Templates**: Conventional commits, GitHub/GitLab PR formats
- **⚙️ Team Configuration**: Shared templates, conventions, multi-tier config
- **🔍 Git Analysis**: Intelligent change detection and context building
- **🛡️ Robust CLI**: Comprehensive validation, helpful errors, verbose logging

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

# Edit with your API keys
nano ~/.config/gitai/config.yaml
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
gitai templates --show conventional      # Show template content
gitai templates --show github --type pr  # Show PR template content
```

### Commit Generation
```bash
gitai commit --preview                   # Preview commit message
gitai commit                             # Generate and apply commit
gitai commit -t descriptive              # Use specific template
gitai commit -p openai                   # Use specific provider
gitai commit --include-untracked         # Include untracked files
```

### PR Generation
```bash
gitai pr --base main                     # Generate PR description
gitai pr --base develop -o pr.md         # Save to file
gitai pr -t gitlab                       # Use GitLab template
gitai pr -p anthropic                    # Use Claude provider
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
gitai pr --base main                     # ✅ PR generation
gitai templates --list                   # ✅ Template management

# Provider management (fully functional)
gitai config --set-provider anthropic    # ✅ Set default provider
gitai config --set-provider openai       # ✅ Switch providers easily
gitai commit -p openai                   # ✅ Override default per command
gitai commit -p anthropic                # ✅ Claude integration
gitai commit -p ollama                   # ✅ Local Ollama
gitai commit -p lmstudio                 # ✅ Local LMStudio
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
