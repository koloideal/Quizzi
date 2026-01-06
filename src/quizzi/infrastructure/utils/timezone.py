from datetime import datetime
from zoneinfo import ZoneInfo

MSK_TZ = ZoneInfo("Europe/Moscow")


def now_msk() -> datetime:
    return datetime.now(MSK_TZ)


def now_msk_naive() -> datetime:
    """Возвращает текущее время в МСК без timezone info (для сохранения в БД)."""
    return datetime.now(MSK_TZ).replace(tzinfo=None)


def to_msk(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=MSK_TZ)
    return dt.astimezone(MSK_TZ)
