from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    first_name: str
    username: str | None = None
    last_name: str | None = None
    group: int | None = None
    is_admin: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
