# Project Overview - GitAI

## What is GitAI?

GitAI is a Python CLI tool that automates the creation of commit messages and pull request descriptions using AI. It analyzes your git changes and generates meaningful, consistent messages based on configurable templates.

## Quick Start

```bash
# Install globally (once)
git clone <repo-url>
cd gitai
pip install -e .

# Use anywhere
cd ~/any-git-project/
git add .
gitai commit                    # Generates commit message
gitai pr --base main           # Generates PR description
```

## Core Features

### 🤖 AI-Powered Generation
- Analyzes staged changes for commit messages
- Analyzes branch changes for PR descriptions  
- Uses local AI (Ollama) or cloud providers (OpenAI)
- Intelligent context extraction from code changes

### 📋 Template System
- Conventional commits, descriptive, minimal formats
- GitHub, GitLab, standard PR templates
- Team-specific customization
- Jinja2-based template inheritance

### ⚙️ Flexible Configuration
- Global user preferences
- Team-specific settings
- Project-specific overrides
- Zero-setup: works immediately in any git repo

### 🔧 Developer Experience
- Simple CLI: `gitai commit`, `gitai pr`
- Preview before applying
- Rich error messages
- Comprehensive documentation

## Why GitAI?

### Current Problems
- ⏰ **Time waste**: Writing commit messages and PR descriptions manually
- 📝 **Inconsistency**: Different formats and quality across teams
- 🔄 **Repetition**: Manually describing what git already knows
- 👥 **No standards**: Each developer writes differently

### GitAI Solutions
- 🤖 **Automation**: AI generates based on actual changes
- 📋 **Consistency**: Templates ensure standard formats
- ⚡ **Speed**: `gitai commit` replaces manual writing
- 🌱 **Extensible**: Easy to customize and extend

## Architecture at a Glance

```
CLI Commands → Business Logic → AI Providers
     ↓              ↓              ↓
Configuration ← Templates ← Git Analysis
```

### Key Components
- **Git Analyzer**: Extracts meaningful changes from git
- **Template System**: Jinja2-based customizable templates
- **AI Providers**: Ollama, OpenAI, extensible interface
- **Configuration**: Hierarchical config management
- **CLI**: Simple, intuitive command interface

## Use Cases

### Daily Development
```bash
# Working on a feature
git add src/auth.py tests/test_auth.py
gitai commit
# → "feat(auth): add JWT token validation with expiry handling"

# Ready for PR
gitai pr --base develop --output pr.md
# → Generates comprehensive PR description
```

### Team Workflows
```bash
# Team lead sets up templates
gitai config team frontend --template semantic

# Developers use team standards
gitai commit  # Uses team's semantic template
gitai pr      # Uses team's PR format
```

### Project-Specific Needs
```yaml
# project/.gitai/config.yaml
provider:
  model: "gpt-4"  # Override for this project
templates:
  default_commit: "detailed"
```

## Configuration Hierarchy

```
1. Default (package)     ← Base configuration
2. User Global (~/.config/gitai/)  ← Your preferences  
3. Team (~/.config/gitai/teams/)   ← Team standards
4. Project (.gitai/)               ← Project overrides
```

Higher numbers override lower numbers.

## Template Examples

### Commit Templates

**Conventional**:
```
{{ type }}({{ scope }}): {{ description }}

{{ details }}
```

**Descriptive**:
```
{{ summary }}

Changes:
{% for file in files_changed %}
- {{ file.path }}: {{ file.description }}
{% endfor %}
```

### PR Templates

**GitHub**:
```markdown
## Summary
{{ pr_summary }}

## Changes
{{ change_details }}

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
```

## Development Status

### ✅ Completed (Planning)
- Architecture design
- Implementation roadmap
- Code standards
- Project structure
- Enterprise adoption plan

### 🚧 In Progress (Implementation)
- Core git analysis
- Template system
- Ollama provider
- CLI commands

### 📋 Planned (Next 6 weeks)
- **Week 1-2**: Foundation & core infrastructure
- **Week 3**: Template & configuration system  
- **Week 4**: CLI commands & user experience
- **Week 5**: Testing & quality assurance
- **Week 6**: Polish & extensibility

## Team Adoption

### Setup Time: < 5 minutes
```bash
# 1. Global install (once)
pip install gitai

# 2. User setup (once)  
gitai config init

# 3. Team setup (optional)
gitai config team frontend

# 4. Use everywhere
# Works immediately in any git project
```

### Benefits
- **70% time reduction** in commit/PR creation
- **Consistent formatting** across teams
- **Better message quality** through AI analysis
- **Zero friction** - works in any git repository

## Technology Stack

### Core Technologies
- **Python 3.9+**: Main language
- **Click**: CLI framework
- **GitPython**: Git operations
- **Jinja2**: Template engine
- **Pydantic**: Configuration validation
- **PyYAML**: Configuration files

### AI Providers
- **Ollama**: Local AI (primary)
- **OpenAI**: Cloud AI (optional)
- **Extensible**: Easy to add new providers

### Development Tools
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **pre-commit**: Git hooks

## Success Metrics

### Technical
- **Setup time**: < 5 minutes average
- **Performance**: < 30 seconds per generation
- **Reliability**: > 95% success rate
- **Test coverage**: > 80%

### Adoption
- **Teams using**: Target 5+ teams in 2 months
- **Daily usage**: > 50 generations per day
- **Custom templates**: > 10 created by teams
- **Contributors**: > 3 external contributors

### Business Impact
- **Time saved**: 70% reduction in commit/PR time
- **Quality improvement**: Better, more consistent messages
- **Developer satisfaction**: Positive feedback in surveys

## Getting Started

### For Users
1. **Install**: `pip install gitai`
2. **Setup**: `gitai config init`
3. **Use**: `gitai commit` in any git project

### For Teams
1. **Install globally**: Share installation instructions
2. **Create team config**: Define templates and standards
3. **Train team**: Share usage examples
4. **Iterate**: Collect feedback and improve

### For Contributors
1. **Clone repository**: `git clone <repo>`
2. **Setup development**: `scripts/setup/install-dev.sh`
3. **Read docs**: Check `docs/development/`
4. **Start contributing**: Pick an issue and submit PR

## Future Vision

### Short Term (1-2 months)
- Stable core functionality
- 3+ teams actively using
- Basic template library
- Complete documentation

### Medium Term (3-6 months) 
- Multiple AI providers
- Advanced template features
- VS Code extension
- CI/CD integrations

### Long Term (6+ months)
- Branch review functionality
- Team analytics and insights
- Template marketplace
- Enterprise features

## Community

### Contributing
- **Code contributions**: Follow code standards and submit PRs
- **Template sharing**: Share useful templates with community
- **Documentation**: Help improve guides and examples
- **Feedback**: Report issues and suggest improvements

### Support
- **Documentation**: Comprehensive guides and API docs
- **Issues**: GitHub issues for bugs and feature requests
- **Discussions**: Community discussions for questions
- **Examples**: Real-world usage examples

## Conclusion

GitAI transforms the tedious task of writing commit messages and PR descriptions into an automated, consistent, and intelligent process. By combining AI analysis with flexible templates and simple configuration, it saves time while improving code documentation quality.

The tool is designed for immediate adoption with zero friction while providing deep customization for teams with specific needs. The modular architecture ensures it can grow and adapt as requirements evolve.

**Ready to start?** Try `gitai commit` in your next git repository!

---

**Document**: Project Overview v1.0 (GitAI)  
**Last updated**: 2024-10-24  
**Focus**: High-level introduction and value proposition