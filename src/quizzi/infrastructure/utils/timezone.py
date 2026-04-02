from datetime import datetime, timedelta, timezone

MSK_TZ = timezone(timedelta(hours=3))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def to_msk(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MSK_TZ)
