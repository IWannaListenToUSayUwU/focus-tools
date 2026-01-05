import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.db import engine, Base
from app.routes import pages
from app.services.discord import start_periodic_messages

# 載入環境變數
load_dotenv()

Base.metadata.create_all(bind=engine)

# 背景任務管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    print("🚀 啟動 Discord 定期訊息服務...")
    discord_task = None
    
    # 檢查是否有設定 Discord webhook
    if os.getenv("DISCORD_WEBHOOK_URL"):
        discord_task = asyncio.create_task(start_periodic_messages())
        print("✅ Discord 定期訊息服務已啟動 (每 10 秒發送一次)")
    else:
        print("⚠️  未設定 DISCORD_WEBHOOK_URL，跳過 Discord 服務")
    
    yield
    
    # 關閉時執行
    if discord_task:
        discord_task.cancel()
        try:
            await discord_task
        except asyncio.CancelledError:
            print("🛑 Discord 定期訊息服務已停止")

app = FastAPI(title="Discipline - 自律打卡", lifespan=lifespan)

templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

app.state.templates = Jinja2Templates(directory=str(templates_dir))

static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(pages.router)
