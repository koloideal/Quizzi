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


@dataclass
class Test:
    id: int
    title: str
    description: str | None = None
    for_group: int | None = None
    is_active: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Question:
    id: int
    test_id: int
    text: str
    position: int = 0
    question_type: str = "single"
    tg_file_id: str | None = None


@dataclass
class Option:
    id: int
    question_id: int
    text: str
    is_correct: bool = False
    explanation: str | None = None
