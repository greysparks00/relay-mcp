from datetime import datetime


# Get the current date and time.
def get_current_datetime() -> str:
    return datetime.now().astimezone().isoformat()
