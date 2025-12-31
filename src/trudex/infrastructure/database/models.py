from datetime import datetime
from enum import Enum
from typing import final

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


@final
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(32))
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    group: Mapped[int | None] = mapped_column(CheckConstraint("group >= 1000 AND group <= 9999"))
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


class QuestionType(str, Enum):
    SINGLE = "single"
    MULTIPLE = "multiple"
    INPUT = "input"


@final
class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    for_group: Mapped[int | None] = mapped_column(default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    questions: Mapped[list["Question"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="Question.position"
    )


@final
class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"))
    text: Mapped[str] = mapped_column(Text)
    position: Mapped[int] = mapped_column(Integer, default=0)
    question_type: Mapped[QuestionType] = mapped_column(default=QuestionType.SINGLE)
    tg_file_id: Mapped[str | None] = mapped_column(String(255))

    test: Mapped["Test"] = relationship(back_populates="questions")
    options: Mapped[list["Option"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan"
    )


@final
class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"))
    text: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(default=False)
    explanation: Mapped[str | None] = mapped_column(Text)

    question: Mapped["Question"] = relationship(back_populates="options")
