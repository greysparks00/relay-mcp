from datetime import UTC, datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def convert_timezone(local_datetime: str, from_zone: str, to_zone: str,
                     occurrence: Literal["earlier", "later"] | None = None) -> dict:
    """Convert a local ISO date and time between IANA zones such as America/Chicago and Europe/London. Choose an occurrence for repeated times."""
    if "T" not in local_datetime and " " not in local_datetime:
        raise ValueError("Include both the date and the time.")
    local = datetime.fromisoformat(local_datetime)
    if local.tzinfo is not None:
        raise ValueError("Supply the local time without an offset and specify its source zone.")
    try:
        source, target = ZoneInfo(from_zone), ZoneInfo(to_zone)
    except (ZoneInfoNotFoundError, ValueError) as error:
        raise ValueError("Use an IANA time zone name, such as America/Chicago.") from error
    instants = set()
    for fold in (0, 1):
        instant = local.replace(tzinfo=source, fold=fold).astimezone(UTC)
        if instant.astimezone(source).replace(tzinfo=None) == local:
            instants.add(instant)
    if not instants:
        raise ValueError("This local time does not exist because the clock moves forward.")
    if len(instants) == 2 and occurrence is None:
        raise ValueError("This local time occurs twice. Specify earlier or later.")
    instant = max(instants) if occurrence == "later" else min(instants)
    return {"source_time": instant.astimezone(source).isoformat(), "source_zone": from_zone,
            "target_time": instant.astimezone(target).isoformat(), "target_zone": to_zone}
