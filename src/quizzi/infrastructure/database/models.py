from datetime import datetime
from typing import final

from sqlalchemy import BigInteger, CheckConstraint, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from quizzi.domain.schemas import QuestionType


class Base(DeclarativeBase):
    pass

@final
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(32), index=True)
    first_name: Mapped[str] = mapped_column(String(64))
    last_name: Mapped[str | None] = mapped_column(String(64))
    name: Mapped[str | None] = mapped_column(String(128))
    group: Mapped[int | None] = mapped_column(CheckConstraint("group >= 1000 AND group <= 9999"), index=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    name_updated_at: Mapped[datetime | None] = mapped_column(default=None)
    group_updated_at: Mapped[datetime | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


@final
class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    number: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        CheckConstraint("number >= 1000 AND number <= 9999", name="check_group_number"),
    )


@final
class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    for_group: Mapped[int | None] = mapped_column(default=None)
    password: Mapped[str | None] = mapped_column(String(255), default=None)
    expires_at: Mapped[datetime | None] = mapped_column(default=None)
    attempts: Mapped[int | None] = mapped_column(Integer, default=None)
    is_active: Mapped[bool] = mapped_column(default=True)
    are_results_viewable: Mapped[bool] = mapped_column(default=False)
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
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), index=True)
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
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    text: Mapped[str] = mapped_column(String(255))
    is_correct: Mapped[bool] = mapped_column(default=False)
    explanation: Mapped[str | None] = mapped_column(Text)

    question: Mapped["Question"] = relationship(back_populates="options")


@final
class TestAttempt(Base):
    __tablename__ = "test_attempts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    test_id: Mapped[int] = mapped_column(ForeignKey("tests.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(default=None)
    score: Mapped[int] = mapped_column(Integer, default=0)
    is_passed: Mapped[bool] = mapped_column(default=False)
    
    user: Mapped["User"] = relationship()
    test: Mapped["Test"] = relationship()
    answers: Mapped[list["UserAnswer"]] = relationship(
        back_populates="attempt",
        cascade="all, delete-orphan"
    )


@final
class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    attempt_id: Mapped[int] = mapped_column(ForeignKey("test_attempts.id"), index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("questions.id"), index=True)
    selected_option_id: Mapped[int | None] = mapped_column(ForeignKey("options.id"), default=None)
    text_answer: Mapped[str | None] = mapped_column(Text, default=None)
    is_correct: Mapped[bool] = mapped_column(default=False)
    
    attempt: Mapped["TestAttempt"] = relationship(back_populates="answers")
    question: Mapped["Question"] = relationship()
    selected_option: Mapped["Option | None"] = relationship()

