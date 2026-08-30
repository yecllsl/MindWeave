"""统计路由：ECharts 图表页（subject/knowledge_point/mastery）。"""
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from mindweave_mcp.web import services
from mindweave_mcp.web.app import templates

router = APIRouter()

_VALID_GROUPS = {"subject", "knowledge_point", "mastery"}


@router.get("/stats", response_class=HTMLResponse)
async def stats_page(request: Request) -> Response:
    return templates.TemplateResponse(
        request, "partials/stats.html",
        {"active": "stats", "group_options": [
            ("subject", "按学科"), ("knowledge_point", "按知识点"), ("mastery", "按掌握度"),
        ]},
    )


@router.get("/api/stats")
async def stats_api(group_by: str = "subject") -> dict[str, Any]:
    if group_by not in _VALID_GROUPS:
        raise HTTPException(status_code=422, detail=f"不支持的分组维度: {group_by}")
    result = services.get_stats(group_by)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result
