from secrets import choice


def pick_random(options: list[str]) -> str:
    """Pick one option uniformly from the supplied choices, for example dinner ideas."""
    choices = [value.strip() for value in options]
    if not choices or not all(choices):
        raise ValueError("Provide at least one option and omit blank choices.")
    return choice(choices)
