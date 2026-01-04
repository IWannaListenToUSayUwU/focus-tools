from datetime import datetime, date
from sqlalchemy import String, Boolean, Date, DateTime, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db import Base


class TaskType(enum.Enum):
    DAILY = "daily"
    ONE_TIME = "one_time"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.DAILY, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=True)  # 一次性任務的到期日
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    completions: Mapped[list["Completion"]] = relationship(back_populates="task", cascade="all, delete-orphan")


class Completion(Base):
    __tablename__ = "completions"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)

    task: Mapped["Task"] = relationship(back_populates="completions")

    __table_args__ = (
        UniqueConstraint("task_id", "date", name="uq_task_date"),
    )
