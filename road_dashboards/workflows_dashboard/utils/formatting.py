def format_workflow_name(workflow_name: str) -> str:
    """Format workflow name for display."""
    prefix = workflow_name.replace("_workflow", "")
    words = prefix.split("_")

    if len(words) == 1:
        return prefix.upper()

    return " ".join(word.title() for word in words)
