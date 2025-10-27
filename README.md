# GitAI - AI-Powered Git Automation

AI-driven commit message and PR description generation with customizable templates and team configurations.

## Quick Start
```bash
git clone <repo-url>
cd gitai && pip install -e .
gitai commit    # Generate commit from staged changes
gitai pr        # Generate PR description from branch
```

## 📋 Implementation Guide

### For Development Teams
| Epic | Stories | Key Documents |
|------|---------|---------------|
| **Epic 1: Foundation** | Project setup, Git analysis, Provider interface, CLI skeleton | [Source Tree](docs/source-tree.md) → [Architecture](docs/architecture-overview.md) → [Code Standards](docs/code-standards.md) |
| **Epic 2: Templates** | Template engine, Configuration hierarchy, Default templates | [Architecture](docs/architecture-overview.md) → [Source Tree](docs/source-tree.md#configuration-structure-config) |
| **Epic 3: CLI Commands** | Commit/PR/Config commands, Error handling | [Architecture](docs/architecture-overview.md#data-flow) → [Code Standards](docs/code-standards.md#error-handling) |
| **Epic 4: Testing** | Unit tests, Integration tests, Quality checks | [Code Standards](docs/code-standards.md#testing-standards) → [Source Tree](docs/source-tree.md#test-structure-tests) |
| **Epic 5: Polish** | Additional providers, Advanced features | [Architecture](docs/architecture-overview.md#extensibility-points) |
| **Epic 6: Pilot** | Team onboarding, Feedback collection | [Project Overview](docs/project-overview.md#team-adoption) |

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

### Key Commands
```bash
# Setup development
scripts/setup/install-dev.sh

# Code quality
scripts/development/format-code.sh
scripts/development/run-tests.sh
scripts/development/check-types.sh

# Usage
gitai commit --preview           # Preview commit message
gitai pr --base main --output pr.md  # Generate PR description
gitai config init --global      # Setup user configuration
```

## 📁 Quick Navigation

| Component | Implementation Guide | Tests |
|-----------|---------------------|-------|
| **Git Analysis** | [Architecture](docs/architecture-overview.md#3-git-analysis-coregit_analyzerpy) → [Source](docs/source-tree.md#source-code-structure-srcgitai) | [Test Structure](docs/source-tree.md#test-structure-tests) |
| **AI Providers** | [Architecture](docs/architecture-overview.md#4-ai-providers-providers) → [Standards](docs/code-standards.md#error-handling) | [Unit Tests](docs/code-standards.md#test-structure-aaa-pattern) |
| **Templates** | [Architecture](docs/architecture-overview.md#5-template-system-templates) → [Source](docs/source-tree.md#default-templates-structure-templates) | [Integration Tests](docs/code-standards.md#testing-standards) |
| **Configuration** | [Architecture](docs/architecture-overview.md#configuration-hierarchy) → [Source](docs/source-tree.md#configuration-structure-config) | [Coverage Requirements](docs/code-standards.md#test-coverage-requirements) |

## 🎯 Success Criteria
- **Setup**: < 5 minutes for new users
- **Performance**: < 30 seconds per generation  
- **Quality**: > 80% test coverage, > 95% reliability
- **Adoption**: 3+ teams using successfully

## 📖 Documentation
- **Users**: [Project Overview](docs/project-overview.md)
- **Developers**: [Architecture Overview](docs/architecture-overview.md) + [Code Standards](docs/code-standards.md)
- **Contributors**: [Source Tree](docs/source-tree.md) + [Refined Roadmap](docs/roadmap-refined.md)
- **Teams**: [Enterprise Plan](docs/enterprise-adoption-plan.md)

---

**Status**: 📋 Planning Complete → 🚧 Implementation Ready  
**Next**: Begin Epic 1 (Foundation & Core Infrastructure)