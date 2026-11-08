from tools._timers import timers


# Remove a named countdown and report whether it was cancelled, already expired, or missing.
def cancel_timer(name: str) -> dict:
    return timers.cancel(name)
