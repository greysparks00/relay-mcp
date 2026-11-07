from tools._timers import timers


def set_timer(name: str, duration_seconds: int) -> dict:
    """Start a named countdown in seconds for this running server. Returns its UTC due time."""
    return timers.start(name, duration_seconds)
