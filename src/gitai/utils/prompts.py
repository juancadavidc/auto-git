"""System prompts for AI providers."""


def get_system_prompt(command_type: str) -> str:
    """Get appropriate system prompt based on command type.

    Args:
        command_type: Either 'commit' or 'pr'

    Returns:
        System prompt string optimized for the command type
    """
    prompts = {
        "commit": (
            "You are a helpful assistant that generates clear, concise commit "
            "messages based on git changes. Follow the template format provided "
            "exactly and focus on the actual changes made."
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
    return prompts.get(command_type, prompts["commit"])
