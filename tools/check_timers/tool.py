from tools._timers import timers


def check_timers(name: str | None = None) -> list[dict]:
    """Show remaining seconds for one named timer or all timers. Expired timers stay visible for one hour."""
    return timers.check(name)
