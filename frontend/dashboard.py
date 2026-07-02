"""仪表盘路由 - 返回ECharts可视化HTML页面"""
import logging
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from config import config

logger = logging.getLogger(__name__)

templates_dir = config.app.base_dir / "frontend" / "templates"
static_dir = config.app.base_dir / "frontend" / "static"

templates = Jinja2Templates(directory=str(templates_dir))

router = APIRouter()


def get_template_context(request: Request):
    """生成模板上下文"""
    return {
        "request": request,
        "title": "农业新闻分析与预警系统",
        "current_year": datetime.now().year,
        "api_base": "/api",
    }


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """主仪表盘页面"""
    return templates.TemplateResponse("dashboard.html", get_template_context(request))
