from datetime import date, timedelta


WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def resolve_date(value: str, today: date) -> date:
    value = value.strip().casefold()
    if value in ("yesterday", "today", "tomorrow"):
        return today + timedelta(days={"yesterday": -1, "today": 0, "tomorrow": 1}[value])
    for index, weekday in enumerate(WEEKDAYS):
        if value == weekday.casefold():
            return today + timedelta(days=(index - today.weekday()) % 7)
    return date.fromisoformat(value)


# Offset a date by signed days or weeks, or give an end date for a signed day count. Use ISO
# dates, today, tomorrow, yesterday, or a weekday on or after today (server local time).
def date_math(start: str = "today", days: int = 0, weeks: int = 0, end: str | None = None) -> dict:
    today = date.today()
    first = resolve_date(start, today)
    if end is not None and (days or weeks):
        raise ValueError("Choose either an end date or a day/week offset.")
    last = resolve_date(end, today) if end is not None else first + timedelta(days=days, weeks=weeks)
    return {"start": first.isoformat(), "date": last.isoformat(),
            "weekday": WEEKDAYS[last.weekday()], "days": (last - first).days}
