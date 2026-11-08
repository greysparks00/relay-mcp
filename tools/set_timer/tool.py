from tools._timers import timers


# Start a named countdown in seconds for this running server. Returns its UTC due time.
def set_timer(name: str, duration_seconds: int) -> dict:
    return timers.start(name, duration_seconds)
