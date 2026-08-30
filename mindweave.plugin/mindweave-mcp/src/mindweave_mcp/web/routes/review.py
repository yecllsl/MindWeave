"""自评复习路由：到期队列 + 逐卡自评（更新 SM-2）。"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from mindweave_mcp.web import services
from mindweave_mcp.web.app import templates

router = APIRouter()


@router.get("/review", response_class=HTMLResponse)
async def review_page(request: Request, subject: str = "") -> Response:
    queue = services.get_due_queue(subject)
    return templates.TemplateResponse(
        request, "partials/review.html",
        {"queue": queue, "subject": subject,
         "subject_options": services.SUBJECT_OPTIONS, "active": "review"},
    )


@router.post("/review/submit")
async def review_submit(request: Request) -> RedirectResponse:
    form = await request.form()
    cue_val = form.get("cue_id", "")
    cue_id = cue_val if isinstance(cue_val, str) else ""
    grade_val = form.get("grade", "")
    grade_str = grade_val if isinstance(grade_val, str) else ""
    try:
        grade = int(grade_str)
    except ValueError:
        raise HTTPException(status_code=422, detail="grade 须为 1-4 整数") from None
    result = services.submit_review_from_web(cue_id, grade)
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return RedirectResponse("/review", status_code=303)
