from tools._timers import timers


def cancel_timer(name: str) -> dict:
    """Remove a named countdown and report whether it was cancelled, already expired, or missing."""
    return timers.cancel(name)
