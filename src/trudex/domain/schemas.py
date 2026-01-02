from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int
    first_name: str
    username: str | None = None
    last_name: str | None = None
    name: str | None = None
    group: int | None = None
    is_admin: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Group:
    id: int
    number: int
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class Test:
    id: int
    title: str
    description: str | None = None
    for_group: int | None = None
    password: str | None = None
    expires_at: datetime | None = None
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


@dataclass
class TestAttempt:
    id: int
    user_id: int
    test_id: int
    started_at: datetime
    finished_at: datetime | None = None
    score: int = 0
    is_passed: bool = False


@dataclass
class UserAnswer:
    id: int
    attempt_id: int
    question_id: int
    selected_option_id: int | None = None
    text_answer: str | None = None
    is_correct: bool = False
