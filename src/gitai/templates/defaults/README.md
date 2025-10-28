# Default Templates

This directory contains the default templates shipped with GitAI.

## Template Structure

All templates use Jinja2 syntax and can extend the base template for common functionality.

### Base Template (`base.j2`)

Provides common macros and variables:

- `format_file_list(files, max_files=5)` - Format a list of files with truncation
- `format_change_summary(changes)` - Format summary like "3 added, 2 modified"
- `get_change_type(changes)` - Get conventional commit type (feat, fix, etc.)

### Available Variables

All templates have access to these variables:

#### `changes` (DiffAnalysis object)
- `summary`: Brief summary of changes
- `body`: Detailed description
- `rationale`: Why the change was made
- `scope`: Scope of changes (for conventional commits)
- `breaking_change`: Breaking change description
- `is_feature`: Boolean if this is a new feature
- `is_fix`: Boolean if this is a bug fix
- `is_refactor`: Boolean if this is refactoring
- `is_docs`: Boolean if this is documentation
- `is_test`: Boolean if this is test-related
- `affected_files`: List of all changed files
- `added_files`: List of newly added files
- `modified_files`: List of modified files
- `deleted_files`: List of deleted files
- `test_files`: List of test files that were changed
- `lines_added`: Number of lines added
- `lines_deleted`: Number of lines deleted
- `related_issues`: List of related issue numbers

#### `repository` (Repository info)
- `name`: Repository name
- `url`: Repository URL
- `branch`: Current branch
- `remote`: Remote name (usually 'origin')

#### `user` (User info)
- `name`: User's full name
- `email`: User's email address

#### Template-specific variables
- **PR templates**: `base_branch`, `head_branch`
- **Commit templates**: Additional git metadata

## Commit Templates

### `conventional.j2`
Generates commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification.

**Format**: `type(scope): description`

**Example**:
```
feat(auth): add OAuth2 authentication

Files: src/auth.py, tests/test_auth.py
```

### `descriptive.j2`
Generates detailed, descriptive commit messages with file lists and change statistics.

**Example**:
```
Add OAuth2 authentication support

Implements OAuth2 flow for user authentication with Google and GitHub providers.
Includes token refresh and user profile fetching.

Why: Replace basic auth with more secure OAuth2 standard

Modified files:
  - src/auth.py (added)
  - src/oauth.py (added)
  - tests/test_auth.py (modified)

Changes: +156 -23 lines
```

### `minimal.j2`
Generates short, concise commit messages for simple changes.

**Example**:
```
Add OAuth2 authentication (src/auth.py, tests/test_auth.py)
```

## PR Templates

### `github.j2`
GitHub-optimized pull request template with checkboxes and emoji sections.

**Features**:
- Summary section
- Categorized file changes with emojis
- Breaking changes warning
- Testing checklist
- Review checklist
- Change statistics

### `gitlab.j2`
GitLab merge request template with collapsible sections and MR-specific language.

**Features**:
- "What does this MR do?" section
- Related issues linking
- Local validation steps
- Collapsible file change details
- Merge readiness checklist

### `standard.j2`
Generic pull request template that works on any platform.

**Features**:
- Clean, professional format
- Type of change checkboxes
- File change summary
- Testing notes
- Breaking change warnings

## Custom Templates

To create custom templates:

1. Create a `.j2` file in your templates directory
2. Add template metadata in comments:
   ```jinja2
   {# description: Your template description #}
   {# variables: var1, var2, var3 #}
   ```
3. Optionally extend the base template:
   ```jinja2
   {% extends "base.j2" %}
   {% block content %}
   Your template content here
   {% endblock %}
   ```

## Template Inheritance

Templates can inherit from other templates using Jinja2's inheritance system:

```jinja2
{% extends "base.j2" %}

{% block content %}
{{ super() }}  {# Include parent content #}
Additional content here
{% endblock %}
```

## Filters Available

- `wordwrap(width=72)`: Wrap text to specified width
- `capitalize_first`: Capitalize first letter only
- Standard Jinja2 filters: `upper`, `lower`, `title`, `length`, etc.

## Configuration

Set default templates in your configuration:

```yaml
templates:
  default_commit_template: "conventional"
  default_pr_template: "github"
```