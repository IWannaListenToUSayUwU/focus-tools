from datetime import datetime, date, time
from sqlalchemy import String, Boolean, Date, DateTime, Time, ForeignKey, UniqueConstraint, Enum, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum
from typing import Optional

from app.db import Base


class TaskType(enum.Enum):
    DAILY = "daily"
    ONE_TIME = "one_time"


class TimeType(enum.Enum):
    FLEXIBLE = "flexible"    # 🔄 彈性習慣 - 時間不限
    TIMED = "timed"          # ⏰ 定時任務 - 必須在特定時間完成
    DURATION = "duration"    # 📅 時段任務 - 在時間範圍內完成


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    task_type: Mapped[TaskType] = mapped_column(Enum(TaskType), default=TaskType.DAILY, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # 一次性任務的到期日
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    
    # 時間相關欄位
    time_type: Mapped[TimeType] = mapped_column(Enum(TimeType), default=TimeType.FLEXIBLE, nullable=False)
    scheduled_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)  # 定時任務的時間點
    time_range_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)  # 時段任務開始時間
    time_range_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)  # 時段任務結束時間
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 預估完成時間（分鐘）

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
