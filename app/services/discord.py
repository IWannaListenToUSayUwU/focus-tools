import os
import asyncio
import httpx
from datetime import datetime
from typing import Optional
import random


class DiscordService:
    def __init__(self):
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL environment variable is required")
    
    async def send_message(self, content: str) -> bool:
        """發送訊息到 Discord webhook"""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "content": content,
                    "username": "亞爾貝德"
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
    
    def get_random_message(self) -> str:
        """產生隨機訊息內容"""
        messages = [
            f"🕐 {datetime.now().strftime('%H:%M:%S')} - 保持專注！",
            f"💪 {datetime.now().strftime('%H:%M:%S')} - 你正在變得更好！",
            f"🎯 {datetime.now().strftime('%H:%M:%S')} - 目標就在前方！",
            f"⚡ {datetime.now().strftime('%H:%M:%S')} - 持續努力中...",
            f"🔥 {datetime.now().strftime('%H:%M:%S')} - 燃燒你的小宇宙！",
            f"🌟 {datetime.now().strftime('%H:%M:%S')} - 每一秒都在進步！",
            f"🚀 {datetime.now().strftime('%H:%M:%S')} - 向著夢想前進！",
            f"💎 {datetime.now().strftime('%H:%M:%S')} - 自律讓你閃閃發光！"
        ]
        return random.choice(messages)


# 全域 Discord 服務實例
discord_service: Optional[DiscordService] = None


def get_discord_service() -> DiscordService:
    """取得 Discord 服務實例"""
    global discord_service
    if discord_service is None:
        discord_service = DiscordService()
    return discord_service


async def start_periodic_messages():
    """啟動定期發送訊息的背景任務"""
    service = get_discord_service()
    
    while True:
        try:
            message = service.get_random_message()
            await service.send_message(message)
            await asyncio.sleep(10)  # 每 10 秒發送一次
        except Exception as e:
            print(f"❌ 定期訊息任務錯誤: {e}")
            await asyncio.sleep(10)  # 發生錯誤也要等 10 秒再試
