from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Completion


def calculate_streak(db: Session, task_id: int, today: date) -> int:
    """
    計算某任務從今天往回的連續完成天數。
    規則：
    - 若今天沒完成，streak = 0
    - 若今天有完成，往回數連續有完成紀錄的天數
    """
    stmt = select(Completion.date).where(Completion.task_id == task_id).order_by(Completion.date.desc())
    rows = db.execute(stmt).scalars().all()

    if not rows:
        return 0

    completed_dates = set(rows)

    if today not in completed_dates:
        return 0

    streak = 0
    check_date = today
    while check_date in completed_dates:
        streak += 1
        check_date -= timedelta(days=1)

    return streak
