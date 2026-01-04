from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import engine, Base
from app.routes import pages

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Discipline - 自律打卡")

templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

app.state.templates = Jinja2Templates(directory=str(templates_dir))

static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

app.include_router(pages.router)
