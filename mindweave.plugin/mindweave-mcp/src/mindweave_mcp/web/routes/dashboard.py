"""概览路由：今日到期/总卡数/学科分布/近 7 天复习趋势。"""
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from mindweave_mcp.web import services
from mindweave_mcp.web.app import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> Response:
    summary = services.get_dashboard_summary()
    return templates.TemplateResponse(
        request, "partials/dashboard.html",
        {"summary": summary, "active": "dashboard"},
    )


@router.get("/api/dashboard/summary")
async def dashboard_summary_api() -> dict[str, Any]:
    """概览 JSON（ECharts 数据源）。"""
    return services.get_dashboard_summary()
