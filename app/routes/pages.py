from datetime import date, timedelta
import calendar
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.db import get_db
from app.models import Task, Completion, TaskType
from app.services.streak import calculate_streak

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse(url="/today", status_code=302)


@router.get("/today", response_class=HTMLResponse)
async def today_page(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    
    # 每日任務：啟用的每日任務
    # 一次性任務：啟用且到期日是今天或之前的
    stmt = select(Task).where(
        Task.is_active == True,
        or_(
            Task.task_type == TaskType.DAILY,
            (Task.task_type == TaskType.ONE_TIME) & (Task.due_date <= today)
        )
    ).order_by(Task.task_type, Task.id)
    tasks = db.execute(stmt).scalars().all()
    
    completed_stmt = select(Completion.task_id).where(Completion.date == today)
    completed_task_ids = set(db.execute(completed_stmt).scalars().all())
    
    daily_tasks = []
    one_time_tasks = []
    
    for task in tasks:
        task_info = {
            "id": task.id,
            "name": task.name,
            "completed": task.id in completed_task_ids,
            "task_type": task.task_type.value,
        }
        
        if task.task_type == TaskType.DAILY:
            streak = calculate_streak(db, task.id, today)
            task_info["streak"] = streak
            daily_tasks.append(task_info)
        else:
            task_info["due_date"] = task.due_date
            one_time_tasks.append(task_info)
    
    return request.app.state.templates.TemplateResponse(
        "today.html",
        {"request": request, "daily_tasks": daily_tasks, "one_time_tasks": one_time_tasks, "today": today}
    )


@router.post("/tasks/{task_id}/complete")
async def complete_task(task_id: int, db: Session = Depends(get_db)):
    today = date.today()
    
    existing = db.execute(
        select(Completion).where(Completion.task_id == task_id, Completion.date == today)
    ).scalar_one_or_none()
    
    if existing is None:
        completion = Completion(task_id=task_id, date=today)
        db.add(completion)
        db.commit()
    
    return RedirectResponse(url="/today", status_code=303)


@router.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, db: Session = Depends(get_db)):
    stmt = select(Task).order_by(Task.id)
    tasks = db.execute(stmt).scalars().all()
    
    return request.app.state.templates.TemplateResponse(
        "tasks.html",
        {"request": request, "tasks": tasks}
    )


@router.post("/tasks/add")
async def add_task(
    name: str = Form(...), 
    task_type: str = Form("daily"),
    due_date: str = Form(None),
    db: Session = Depends(get_db)
):
    task_type_enum = TaskType.DAILY if task_type == "daily" else TaskType.ONE_TIME
    due_date_obj = None
    
    if task_type_enum == TaskType.ONE_TIME and due_date:
        try:
            due_date_obj = date.fromisoformat(due_date)
        except ValueError:
            due_date_obj = date.today()
    
    task = Task(
        name=name.strip(),
        task_type=task_type_enum,
        due_date=due_date_obj
    )
    db.add(task)
    db.commit()
    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/tasks/{task_id}/toggle-active")
async def toggle_task_active(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task:
        task.is_active = not task.is_active
        db.commit()
    return RedirectResponse(url="/tasks", status_code=303)


@router.post("/tasks/{task_id}/delete")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if task:
        db.delete(task)
        db.commit()
    return RedirectResponse(url="/tasks", status_code=303)


@router.get("/history", response_class=HTMLResponse)
async def history_page(request: Request, target_date: str = None, db: Session = Depends(get_db)):
    if target_date:
        try:
            query_date = date.fromisoformat(target_date)
        except ValueError:
            query_date = date.today()
    else:
        query_date = date.today()
    
    stmt = (
        select(Completion, Task)
        .join(Task)
        .where(Completion.date == query_date)
        .order_by(Task.name)
    )
    results = db.execute(stmt).all()
    
    completed_tasks = [{"name": task.name, "completed_at": comp.created_at} for comp, task in results]
    
    return request.app.state.templates.TemplateResponse(
        "history.html",
        {"request": request, "date": query_date, "completed_tasks": completed_tasks}
    )


@router.get("/calendar", response_class=HTMLResponse)
async def calendar_page(request: Request, year: int = None, month: int = None, db: Session = Depends(get_db)):
    today = date.today()
    if year is None:
        year = today.year
    if month is None:
        month = today.month
    
    # 生成月曆
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
    # 獲取該月所有完成紀錄
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    
    completions_stmt = select(Completion).where(
        Completion.date >= first_day,
        Completion.date <= last_day
    )
    completions = db.execute(completions_stmt).scalars().all()
    
    # 按日期分組完成紀錄
    completion_by_date = {}
    for comp in completions:
        if comp.date not in completion_by_date:
            completion_by_date[comp.date] = []
        completion_by_date[comp.date].append(comp)
    
    # 獲取活躍任務數量（用於計算完成率）
    active_daily_tasks = db.execute(
        select(Task).where(Task.is_active == True, Task.task_type == TaskType.DAILY)
    ).scalars().all()
    daily_task_count = len(active_daily_tasks)
    
    # 為每一天準備資料
    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                day_date = date(year, month, day)
                day_completions = completion_by_date.get(day_date, [])
                
                # 計算該天的完成率
                daily_completions = [c for c in day_completions if any(
                    task.task_type == TaskType.DAILY for task in [db.get(Task, c.task_id)]
                )]
                completion_rate = len(daily_completions) / daily_task_count if daily_task_count > 0 else 0
                
                week_data.append({
                    'day': day,
                    'date': day_date,
                    'is_today': day_date == today,
                    'completion_count': len(day_completions),
                    'completion_rate': completion_rate,
                    'is_future': day_date > today
                })
        calendar_data.append(week_data)
    
    # 導航用的上個月和下個月
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1
    
    if month == 12:
        next_year, next_month = year + 1, 1
    else:
        next_year, next_month = year, month + 1
    
    return request.app.state.templates.TemplateResponse(
        "calendar.html",
        {
            "request": request,
            "year": year,
            "month": month,
            "month_name": month_name,
            "calendar_data": calendar_data,
            "prev_year": prev_year,
            "prev_month": prev_month,
            "next_year": next_year,
            "next_month": next_month,
            "today": today
        }
    )
