from tools._store import save


def save_handoff(topic: str, summary: str) -> str:
    """Save a Relay conversation checkpoint with decisions, open questions and next steps. Replaces the prior summary for this topic."""
    key = save("handoff", topic, summary)
    return f"Saved handoff for {key}."
