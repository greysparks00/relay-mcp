# Named countdowns shared by clients of this running Relay process.

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import ceil
from threading import Lock
from time import monotonic


@dataclass(frozen=True)
class Timer:
    name: str
    deadline: float
    due_at: datetime

    def status(self, now: float) -> dict:
        remaining = max(0, ceil(self.deadline - now))
        return {"name": self.name, "state": "running" if remaining else "expired",
                "remaining_seconds": remaining, "due_at": self.due_at.isoformat()}


class Timers:
    def __init__(self):
        self._items: dict[str, Timer] = {}
        self._lock = Lock()

    def _prune(self, now: float) -> None:
        # Keep elapsed timers available to a polling voice client for one hour.
        for key in [key for key, timer in self._items.items() if now - timer.deadline >= 3600]:
            del self._items[key]

    def start(self, name: str, seconds: int) -> dict:
        name = name.strip()
        if not 1 <= len(name) <= 100 or not 1 <= seconds <= 365 * 86400:
            raise ValueError("Use a name of 1–100 characters and a duration of 1 second to 365 days.")
        key = name.casefold()
        with self._lock:
            now = monotonic()
            self._prune(now)
            if key in self._items and self._items[key].deadline > now:
                raise ValueError("A timer with that name is already running.")
            if key not in self._items and len(self._items) >= 100:
                raise ValueError("Cancel a timer before adding another.")
            timer = Timer(name, now + seconds, datetime.now(UTC) + timedelta(seconds=seconds))
            self._items[key] = timer
            return timer.status(now)

    def check(self, name: str | None) -> list[dict]:
        with self._lock:
            now = monotonic()
            self._prune(now)
            if name is not None:
                item = self._items.get(name.strip().casefold())
                return [item.status(now)] if item else []
            return [timer.status(now) for timer in sorted(self._items.values(), key=lambda t: t.deadline)]

    def cancel(self, name: str) -> dict:
        with self._lock:
            now = monotonic()
            self._prune(now)
            timer = self._items.pop(name.strip().casefold(), None)
            if timer is None:
                return {"name": name.strip(), "state": "not_found"}
            result = timer.status(now)
            if result["state"] == "running":
                result["state"] = "cancelled"
            return result


timers = Timers()
