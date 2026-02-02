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
            "You are a helpful assistant that generates clear, concise pull request "
            "descriptions based on git changes. Follow the template format provided "
            "exactly and focus on the actual changes made."
        ),
    }
    return prompts.get(command_type, prompts["commit"])


def get_agentic_system_prompt(command_type: str) -> str:
    """Get system prompt for agentic mode with tool-calling.

    Args:
        command_type: Either 'commit' or 'pr'

    Returns:
        System prompt string that guides the model to use tools.
    """
    prompts = {
        "commit": (
            "You are an expert at analyzing git changes and generating clear, "
            "concise commit messages. You have tools to inspect staged changes.\n\n"
            "IMPORTANT: Always respond in English, regardless of the language "
            "of the code or file contents.\n\n"
            "WORKFLOW:\n"
            "1. Call list_changed_files() to see all changed files and their "
            "line counts.\n"
            "2. Call get_file_diff(file_path) for files you need to inspect:\n"
            "   - Prioritize: source code > configuration > tests\n"
            "   - Focus on files with more changes first\n"
            "   - Skip lock files, generated files, and trivial changes\n"
            "3. Optionally call get_change_summary() for overall statistics.\n"
            "4. When you have enough context, respond with ONLY the commit "
            "message text.\n\n"
            "RULES:\n"
            "- Follow the template format provided in the user message.\n"
            "- Do NOT explain your reasoning in the final response.\n"
            "- Do NOT wrap the commit message in markdown code blocks.\n"
            "- Do NOT wrap the commit message in JSON. Return ONLY plain text.\n"
            "- Always respond in English.\n"
            "- Be concise and focus on what changed and why."
        ),
        "pr": (
            "You are an expert at analyzing git changes and generating clear, "
            "concise pull request descriptions. You have tools to inspect "
            "branch changes.\n\n"
            "IMPORTANT: Always respond in English, regardless of the language "
            "of the code or file contents.\n\n"
            "WORKFLOW:\n"
            "1. Call list_changed_files() to see all changed files and their "
            "line counts.\n"
            "2. Call get_file_diff(file_path) for files you need to inspect.\n"
            "3. Call get_change_summary() for overall statistics.\n"
            "4. Generate the PR description following the template format.\n\n"
            "RULES:\n"
            "- Follow the template format provided exactly.\n"
            "- Do NOT explain your reasoning in the final response.\n"
            "- Always respond in English.\n"
            "- Be thorough but concise."
        ),
    }
    return prompts.get(command_type, prompts["commit"])
