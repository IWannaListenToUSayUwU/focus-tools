import os
import asyncio
import httpx
from datetime import datetime, date, time, timedelta
from typing import Optional, Set
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Task, Completion, TaskType, TimeType


class DiscordService:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
        # 記錄今天已經發送過提醒的任務 ID，避免重複提醒
        self.notified_tasks: Set[int] = set()
        self.last_reset_date: date = date.today()
    
    async def send_message(self, content: str) -> bool:
        """發送訊息到 Discord webhook"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "content": content,
                    "username": "雅爾貝德"
                }
                
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0
                )
                
                if response.status_code == 204:
                    print(f"✅ Discord 訊息發送成功: {content}")
                    return True
                else:
                    print(f"❌ Discord 訊息發送失敗: {response.status_code}")
                    return False
                    
        except Exception as e:
            print(f"❌ Discord 訊息發送錯誤: {e}")
            return False
    
    def reset_daily_notifications(self):
        """每天重置已通知的任務列表"""
        today = date.today()
        if today != self.last_reset_date:
            self.notified_tasks.clear()
            self.last_reset_date = today
            print(f"🔄 已重置每日通知記錄 ({today})")


# 全域 Discord 服務實例
discord_service: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """取得 Discord 服務實例"""
    global discord_service
    if discord_service is None:
        discord_service = DiscordService()
    return discord_service


async def check_and_send_task_reminders():
    """檢查任務時間並發送提醒"""
    service = get_discord_service()
    service.reset_daily_notifications()
    
    now = datetime.now()
    current_time = now.time()
    today = now.date()
    
    # 建立資料庫連線
    db = SessionLocal()
    try:
        # 取得今天已完成的任務
        completed_stmt = select(Completion.task_id).where(Completion.date == today)
        completed_task_ids = set(db.execute(completed_stmt).scalars().all())
        
        # 取得所有啟用的任務
        stmt = select(Task).where(Task.is_active == True)
        tasks = db.execute(stmt).scalars().all()
        
        for task in tasks:
            # 跳過已完成的任務
            if task.id in completed_task_ids:
                continue
            
            # 跳過已經通知過的任務
            if task.id in service.notified_tasks:
                continue
            
            # 檢查是否需要發送提醒
            should_notify = False
            notify_message = ""
            
            if task.time_type == TimeType.TIMED and task.scheduled_time:
                # 定時任務：時間到了就提醒
                if current_time >= task.scheduled_time:
                    should_notify = True
                    time_str = task.scheduled_time.strftime('%H:%M')
                    notify_message = f"⏰ **{task.name}**\n預定時間 {time_str} 已到！該行動了！"
            
            elif task.time_type == TimeType.DURATION and task.time_range_start:
                # 時段任務：開始時間到了就提醒
                if current_time >= task.time_range_start:
                    should_notify = True
                    start_str = task.time_range_start.strftime('%H:%M')
                    end_str = task.time_range_end.strftime('%H:%M') if task.time_range_end else "?"
                    notify_message = f"📅 **{task.name}**\n時段 {start_str}～{end_str} 已開始！"
            
            if should_notify:
                await service.send_message(notify_message)
                service.notified_tasks.add(task.id)
    
    finally:
        db.close()


async def start_task_reminder_service():
    """啟動任務提醒服務（每分鐘檢查一次）"""
    print("🔔 任務提醒服務已啟動")
    
    while True:
        try:
            await check_and_send_task_reminders()
            await asyncio.sleep(60)  # 每 60 秒檢查一次
        except Exception as e:
            print(f"❌ 任務提醒服務錯誤: {e}")
            await asyncio.sleep(60)
