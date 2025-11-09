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
