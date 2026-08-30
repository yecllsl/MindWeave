"""Web 服务层：薄封装直调 tools 层函数（不经 MCP 协议；无 LLM 依赖、无出题路由）。

表单 → note_data 的组装逻辑集中在此，路由层只做 HTTP 编排。
"""
from __future__ import annotations

from typing import Any, cast

from starlette.datastructures import FormData

from mindweave_mcp.models import SUBJECTS
from mindweave_mcp.tools import crud, review, statistics

# 编辑页学科下拉选项（九学科，与 models.SUBJECTS 同源）
SUBJECT_OPTIONS = SUBJECTS


# ── dashboard ──

def get_dashboard_summary() -> dict[str, Any]:
    """总笔记数 / 总卡数 / 今日到期 / 学科分布 / 近 7 天复习趋势。"""
    from collections import Counter
    from datetime import UTC, datetime, timedelta

    from mindweave_mcp.algorithms import _today_utc
    storage = crud.get_storage()
    notes = storage.get_all_notes()
    today = _today_utc().isoformat()
    total_cues = sum(len(n.cornell.cues) for n in notes)
    due = review.schedule_review()
    subj_counter = Counter(n.subject for n in notes)

    week_ago = (datetime.now(UTC) - timedelta(days=6)).date().isoformat()
    rec_counter = Counter(
        r.review_time[:10] for r in storage.list_all_review_records()
        if r.review_time[:10] >= week_ago
    )
    trends = []
    for i in range(6, -1, -1):
        day = (datetime.now(UTC) - timedelta(days=i)).date().isoformat()
        trends.append({"date": day, "count": rec_counter.get(day, 0)})

    return {
        "total_notes": len(notes), "total_cues": total_cues,
        "due_count": due["due_count"],
        "subject_distribution": [
            {"name": k, "value": v} for k, v in subj_counter.most_common()
        ],
        "trends": trends, "today": today,
    }


# ── notes ──

def list_notes(subject: str = "", keyword: str = "") -> list[dict[str, Any]]:
    filters: dict[str, Any] = {}
    if subject:
        filters["subject"] = subject
    if keyword:
        filters["keyword"] = keyword
    return cast("list[dict[str, Any]]", crud.query_notes(filters or {})["notes"])


def get_note_detail(note_id: str) -> dict[str, Any] | None:
    return cast("dict[str, Any] | None", crud.get_note(note_id)["note"])


def _to_str(v: Any) -> str:
    """FormData 值统一转 str（文件字段 UploadFile 视为空串，文本字段原样）。"""
    return v if isinstance(v, str) else ""


def _field_str(form: FormData, key: str) -> str:
    return _to_str(form.get(key, None))


def _next_cue_id(note_id: str, existing_nums: set[int], n: int) -> str:
    """为新增 cue 分配不碰撞的 cue_id：取现有最大序号之后顺延 n 个。"""
    start = (max(existing_nums) if existing_nums else 0) + n
    return f"{note_id}_c{start}"


def update_note_from_web(note_id: str, form: FormData) -> dict[str, Any] | None:
    """编辑表单 → update_note 工具。

    表单字段：subject / knowledge_points（逗号分隔）/ body / summary
    + 平行列表 cue_id[] / cue_question[] / cue_answer_hint[] / cue_del[]（勾选删除）。
    新增 cue（cue_id 空）由服务端分配不碰撞 id，规避 update_note 按 enumerate
    自动补 id 在「删旧增新」场景与现存 cue 撞号的既有边界。
    """
    note = crud.get_note(note_id)["note"]
    if note is None:
        return None

    ids = [_to_str(v) for v in form.getlist("cue_id")]
    questions = [_to_str(v) for v in form.getlist("cue_question")]
    hints = [_to_str(v) for v in form.getlist("cue_answer_hint")]
    del_ids = {_to_str(v) for v in form.getlist("cue_del")}

    existing_nums = {
        int(c["cue_id"].rsplit("_c", 1)[1])
        for c in note["cornell"]["cues"] if "_c" in c["cue_id"]
    }
    raw_cues: list[dict[str, Any]] = []
    new_count = 0
    for i in range(min(len(ids), len(questions), len(hints))):
        cid, q, a = ids[i].strip(), questions[i].strip(), hints[i].strip()
        if cid and cid in del_ids:
            continue  # 勾选删除
        if not q and not a:
            continue  # 空行（未填写的模板新行）
        if not cid:
            new_count += 1
            cid = _next_cue_id(note_id, existing_nums, new_count)
        raw_cues.append({"cue_id": cid, "question": q, "answer_hint": a})

    kp_raw = _field_str(form, "knowledge_points")
    # 全角/半角逗号先统一为半角再切分，避免混合分隔符只切一种
    knowledge_points = [k.strip() for k in kp_raw.replace("，", ",").split(",") if k.strip()]
    return crud.update_note({
        "note_id": note_id,
        "subject": _field_str(form, "subject") or note["subject"],
        "knowledge_points": knowledge_points,
        "cornell": {"body": _field_str(form, "body"),
                    "summary": _field_str(form, "summary"),
                    "cues": raw_cues},
    })


def delete_note_from_web(note_id: str) -> dict[str, Any]:
    return crud.delete_note(note_id)


# ── review ──

def get_due_queue(subject: str = "") -> dict[str, Any]:
    return review.schedule_review(subject)


def submit_review_from_web(cue_id: str, grade: int) -> dict[str, Any]:
    return review.submit_review(cue_id, grade)


# ── stats ──

def get_stats(group_by: str) -> dict[str, Any]:
    return statistics.get_statistics(group_by)
