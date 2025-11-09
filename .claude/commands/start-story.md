# Start Story Command

## Configuration

```yaml
# GitAI Story Starter Configuration
project:
  name: "GitAI"
  description: "AI-powered commit and PR description generation"
  repository: "gen-pr-desc"

knowledge_base:
  docs:
    - "README.md"                      # Navigation hub
    - "docs/roadmap-refined.md"        # Epic breakdown with stories
    - "docs/architecture-overview.md"  # System design
    - "docs/source-tree.md"           # File organization
    - "docs/code-standards.md"        # Coding standards
    - "docs/project-overview.md"      # Context and vision

epics:
  1:
    name: "Foundation & Core Infrastructure"
    duration: "2 weeks"
    priority: "P0"
    key_docs:
      - "docs/source-tree.md"
      - "docs/architecture-overview.md"
      - "docs/code-standards.md"
    stories:
      - "Project setup & structure"
      - "Git analysis foundation"
      - "Provider interface & Ollama implementation"
      - "CLI framework setup"

  2:
    name: "Templates & Configuration System"
    duration: "1.5 weeks"
    priority: "P0"
    key_docs:
      - "docs/architecture-overview.md"
      - "docs/source-tree.md#configuration-structure-config"
    stories:
      - "Template engine implementation"
      - "Configuration hierarchy system"
      - "Default templates creation"
      - "Context builder implementation"

  3:
    name: "CLI Commands & User Experience"
    duration: "1.5 weeks"
    priority: "P0"
    key_docs:
      - "docs/architecture-overview.md#data-flow"
      - "docs/code-standards.md#error-handling"
    stories:
      - "Commit command implementation"
      - "PR command implementation"
      - "Config command implementation"
      - "Error handling & validation"

  4:
    name: "Testing & Quality Assurance"
    duration: "1 week"
    priority: "P0"
    key_docs:
      - "docs/code-standards.md#testing-standards"
      - "docs/source-tree.md#test-structure-tests"
    stories:
      - "Unit testing framework"
      - "Integration testing"
      - "Code quality & linting"

  5:
    name: "Polish & Extensibility"
    duration: "1 week"
    priority: "P1"
    key_docs:
      - "docs/architecture-overview.md#extensibility-points"
    stories:
      - "Additional provider implementation"
      - "Advanced template features"
      - "Performance & optimization"
      - "Documentation & distribution"

  6:
    name: "Pilot & Feedback"
    duration: "2 weeks"
    priority: "P1"
    key_docs:
      - "docs/project-overview.md#team-adoption"
    stories:
      - "Team onboarding"
      - "Feedback collection & analysis"
      - "Iteration based on feedback"

workflow:
  steps:
    1: "Read docs/project-overview.md for context"
    2: "Check docs/roadmap-refined.md for story details"
    3: "Follow docs/source-tree.md for file placement"
    4: "Apply docs/code-standards.md for implementation"
    5: "Reference docs/architecture-overview.md for component design"

success_criteria:
  setup_time: "< 5 minutes for new users"
  performance: "< 30 seconds per generation"
  test_coverage: "> 80%"
  reliability: "> 95%"
  adoption: "3+ teams using successfully"
```

## Command Template

Hi Claude! I'm ready to start implementing a GitAI story.

**Context:**
- Project: {{project.name}} - {{project.description}}
- Epic: [SELECT_EPIC_NUMBER] - {{epics.[EPIC_NUMBER].name}}
- Duration: {{epics.[EPIC_NUMBER].duration}}
- Priority: {{epics.[EPIC_NUMBER].priority}}

**Knowledge Base:**
All implementation details are available in these repository files:
{{#each knowledge_base.docs}}
- {{this}}
{{/each}}

**Epic Details:**
- Stories: {{epics.[EPIC_NUMBER].stories}}
- Key Documents: {{epics.[EPIC_NUMBER].key_docs}}

**Workflow to Follow:**
{{#each workflow.steps}}
{{@key}}. {{this}}
{{/each}}

**Request:**
I want to implement a specific story from this epic. Please:
1. Read the relevant documentation files
2. Ask me which specific story I want to work on
3. Provide implementation guidance based on the architecture
4. Help me create the necessary files following the standards

Ready to start!

## Usage

1. **Select Epic**: Choose epic number (1-6) from the configuration above
2. **Replace Placeholders**: Update `[SELECT_EPIC_NUMBER]` and `[EPIC_NUMBER]` in the template
3. **Copy & Send**: Copy the filled template and send to Claude

## Example Usage

```markdown
Hi Claude! I'm ready to start implementing a GitAI story.

**Context:**
- Project: GitAI - AI-powered commit and PR description generation
- Epic: 1 - Foundation & Core Infrastructure
- Duration: 2 weeks
- Priority: P0

**Knowledge Base:**
All implementation details are available in these repository files:
- README.md
- docs/roadmap-refined.md
- docs/architecture-overview.md
- docs/source-tree.md
- docs/code-standards.md
- docs/project-overview.md

**Epic Details:**
- Stories: Project setup & structure, Git analysis foundation, Provider interface & Ollama implementation, CLI framework setup
- Key Documents: docs/source-tree.md, docs/architecture-overview.md, docs/code-standards.md

**Workflow to Follow:**
1. Read docs/project-overview.md for context
2. Check docs/roadmap-refined.md for story details
3. Follow docs/source-tree.md for file placement
4. Apply docs/code-standards.md for implementation
5. Reference docs/architecture-overview.md for component design

**Request:**
I want to implement a specific story from this epic. Please:
1. Read the relevant documentation files
2. Ask me which specific story I want to work on
3. Provide implementation guidance based on the architecture
4. Help me create the necessary files following the standards

Ready to start!
```
