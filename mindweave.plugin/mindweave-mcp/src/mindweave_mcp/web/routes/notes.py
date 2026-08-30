"""笔记路由：列表（过滤）/ 详情 / 编辑（人工处理页）/ 删除。无出题路由（spec §0）。"""
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

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


# ── 人工处理页（编辑 + 删除）──

@router.get("/notes/{note_id}/edit", response_class=HTMLResponse)
async def note_edit(request: Request, note_id: str) -> Response:
    """人工处理页：编辑表单（修正 LLM 整理结果）。"""
    note: dict[str, Any] | None = services.get_note_detail(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return templates.TemplateResponse(
        request, "partials/note_edit.html",
        {"note": note, "subject_options": services.SUBJECT_OPTIONS, "active": "notes"},
    )


@router.post("/notes/{note_id}/edit")
async def note_edit_submit(note_id: str, request: Request) -> RedirectResponse:
    form = await request.form()
    result = services.update_note_from_web(note_id, form)
    if result is None or "error" in result:
        detail = result.get("error", "笔记不存在") if result else "笔记不存在"
        raise HTTPException(status_code=422, detail=detail)
    return RedirectResponse(f"/notes/{note_id}", status_code=303)


@router.post("/notes/{note_id}/delete")
async def note_delete(note_id: str) -> RedirectResponse:
    services.delete_note_from_web(note_id)
    return RedirectResponse("/notes", status_code=303)
