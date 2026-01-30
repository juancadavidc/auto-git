"""System prompts for AI providers.

Loads structured YAML prompt files with hierarchical override support:
  1. Project-level: .gitai-local/prompts/{command}.yaml
  2. Team-level: .gitai/prompts/{command}.yaml
  3. User-level: ~/.config/gitai/prompts/{command}.yaml
  4. Default: bundled in src/gitai/templates/defaults/prompts/{command}.yaml
  5. Hardcoded fallback (if all YAML loading fails)
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# Hardcoded fallback prompts (backward compatibility if YAML loading fails)
_FALLBACK_PROMPTS = {
    "commit": (
        "You are an expert software engineer that writes precise, descriptive "
        "git commit messages. Your task is to analyze the provided code diff "
        "and generate a commit message that explains WHAT changed and WHY.\n\n"
        "Guidelines for excellent commit messages:\n"
        "1. ANALYZE the actual code changes - look at function names, variable names, "
        "logic changes, and patterns to understand the intent\n"
        "2. Write a SPECIFIC subject line that describes the actual change, not generic "
        "phrases like 'update code' or 'fix bug'\n"
        "3. Use the conventional commit format: type(scope): description\n"
        "4. The subject should be imperative mood, lowercase, no period at end\n"
        "5. Keep subject under 72 characters\n"
        "6. If the change is complex, add a body explaining the reasoning\n\n"
        "Examples of GOOD vs BAD commit messages:\n"
        "- BAD: 'fix(api): fix bug' -> GOOD: 'fix(api): handle null response in user lookup'\n"
        "- BAD: 'feat: add feature' -> GOOD: 'feat(auth): add JWT token refresh mechanism'\n"
        "- BAD: 'refactor: update code' -> GOOD: 'refactor(db): extract query builder into "
        "separate class'\n\n"
        "Analyze the diff carefully and write a commit message that a developer "
        "reading git log would find informative and useful."
    ),
    "pr": (
        "You are an expert code reviewer that generates insightful pull request "
        "descriptions. Your job is to:\n"
        "1. ANALYZE the changes to understand their purpose and impact\n"
        "2. CATEGORIZE the type of change (feature, bugfix, refactor, docs, etc.)\n"
        "3. SUMMARIZE what the changes accomplish in plain language\n"
        "4. IDENTIFY any breaking changes, security implications, or performance impacts\n"
        "5. INTELLIGENTLY fill out checklists based on actual changes (e.g., mark 'Tests added' "
        "if test files were modified, mark 'Documentation updated' if docs changed)\n\n"
        "Focus on WHY the changes were made and WHAT impact they have, not just listing "
        "the raw diffs. Use the template format provided but enhance it with your analysis."
    ),
}


def get_system_prompt(
    command_type: str,
    search_paths: Optional[List[Path]] = None,
) -> str:
    """Get appropriate system prompt based on command type.

    Searches for a YAML prompt file through the hierarchy, falling back
    to hardcoded prompts if no YAML is found or loading fails.

    Args:
        command_type: Either 'commit' or 'pr'
        search_paths: Optional list of directories to search (in priority order).
            If None, uses the default hierarchy.

    Returns:
        System prompt string optimized for the command type
    """
    if search_paths is None:
        search_paths = _get_default_prompt_search_paths()

    for search_dir in search_paths:
        yaml_path = search_dir / "prompts" / f"{command_type}.yaml"
        if yaml_path.exists():
            try:
                prompt_data = _load_prompt_yaml(yaml_path)
                formatted = _format_prompt_from_yaml(prompt_data)
                if formatted:
                    logger.debug("Loaded system prompt from %s", yaml_path)
                    return formatted
            except Exception as e:
                logger.warning(
                    "Failed to load prompt from %s: %s", yaml_path, e
                )
                continue

    logger.debug("Using fallback system prompt for '%s'", command_type)
    return _FALLBACK_PROMPTS.get(command_type, _FALLBACK_PROMPTS["commit"])


def _get_default_prompt_search_paths() -> List[Path]:
    """Get default search paths for prompt YAML files (highest to lowest priority)."""
    paths: List[Path] = []

    # Project-level overrides
    git_root = _find_git_root()
    if git_root:
        paths.append(git_root / ".gitai-local")
        paths.append(git_root / ".gitai")

    # User-level
    if os.name == "nt":
        config_home = Path(
            os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
        )
    else:
        config_home = Path(
            os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
        )
    paths.append(config_home / "gitai")

    # Default (bundled with package)
    paths.append(Path(__file__).parent.parent / "templates" / "defaults")

    return paths


def _find_git_root() -> Optional[Path]:
    """Find the git repository root directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return None


def _load_prompt_yaml(yaml_path: Path) -> Dict[str, Any]:
    """Load and parse a prompt YAML file."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected dict in {yaml_path}, got {type(data)}")
    return data


def _format_prompt_from_yaml(data: Dict[str, Any]) -> str:
    """Convert structured YAML prompt data into a formatted system prompt string.

    Supports sections: role, guidelines, type_rules, examples, anti_patterns, output_format.
    """
    parts: List[str] = []

    # Role
    if "role" in data:
        parts.append(data["role"].strip())

    # Guidelines
    if "guidelines" in data:
        parts.append("\nGuidelines:")
        for guideline in data["guidelines"]:
            parts.append(f"- {guideline}")

    # Type rules
    if "type_rules" in data:
        parts.append("\nConventional commit types:")
        for type_name, description in data["type_rules"].items():
            parts.append(f"- {type_name}: {description}")

    # Examples
    if "examples" in data:
        if "good" in data["examples"]:
            parts.append("\nExamples of GOOD commit messages:")
            for ex in data["examples"]["good"]:
                parts.append(f"  '{ex['subject']}' - {ex['why']}")
        if "bad" in data["examples"]:
            parts.append("\nExamples of BAD commit messages (NEVER do these):")
            for ex in data["examples"]["bad"]:
                parts.append(f"  '{ex['subject']}' - {ex['why']}")

    # Anti-patterns
    if "anti_patterns" in data:
        parts.append("\nAnti-patterns to avoid:")
        for pattern in data["anti_patterns"]:
            parts.append(f"- {pattern}")

    # Output format
    if "output_format" in data:
        parts.append(f"\n{data['output_format'].strip()}")

    return "\n".join(parts)
