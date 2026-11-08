from tools._timers import timers


# Show remaining seconds for one named timer or all timers. Expired timers stay visible for
# one hour.
def check_timers(name: str | None = None) -> list[dict]:
    return timers.check(name)
