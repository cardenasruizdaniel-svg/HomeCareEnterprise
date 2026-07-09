from datetime import datetime
from zoneinfo import ZoneInfo

TZ="America/Bogota"

def ahora():
    return datetime.now(ZoneInfo(TZ))
