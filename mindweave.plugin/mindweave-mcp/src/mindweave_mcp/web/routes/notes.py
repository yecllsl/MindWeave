"""笔记路由：列表（过滤）/ 详情 / 编辑（人工处理页）/ 删除。无出题路由（spec §0）。"""
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, Response

from mindweave_mcp.web import services
from mindweave_mcp.web.app import templates

router = APIRouter()


@router.get("/notes", response_class=HTMLResponse)
async def notes_list(request: Request, subject: str = "", keyword: str = "") -> Response:
    notes = services.list_notes(subject=subject, keyword=keyword)
    return templates.TemplateResponse(
        request, "partials/notes_list.html",
        {"notes": notes, "subject": subject, "keyword": keyword,
         "subject_options": services.SUBJECT_OPTIONS, "active": "notes"},
    )


@router.get("/notes/{note_id}", response_class=HTMLResponse)
async def note_detail(request: Request, note_id: str) -> Response:
    note: dict[str, Any] | None = services.get_note_detail(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return templates.TemplateResponse(
        request, "partials/note_detail.html",
        {"note": note, "active": "notes"},
    )
