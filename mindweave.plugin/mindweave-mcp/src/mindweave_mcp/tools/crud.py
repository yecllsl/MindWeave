"""笔记 CRUD Tools：save/get/query/update/delete。"""
from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Any

from mindweave_mcp.algorithms import _now_utc, _today_utc
from mindweave_mcp.models import Cornell, Cue, NoteRecord, ReviewState
from mindweave_mcp.storage import Storage

# 数据目录唯一真相源：export / organize / 测试隔离 fixture 均引用此处
_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"


def get_storage() -> Storage:
    return Storage(base_dir=_DATA_DIR)


def _generate_note_id(storage: Storage) -> str:
    today = _now_utc().strftime("%Y%m%d")
    p = f"note_{today}_"
    existing = [eid for eid in storage.list_all_note_ids() if eid.startswith(p)]
    nnn = max((int(eid.split("_")[-1]) for eid in existing), default=0) + 1
    return f"{p}{nnn:03d}"


def _init_cues(note_id: str, raw_cues: list[dict[str, Any]]) -> list[Cue]:
    cues: list[Cue] = []
    for i, rc in enumerate(raw_cues, 1):
        cue_id = rc.get("cue_id") or f"{note_id}_c{i}"
        next_review = (_today_utc() + timedelta(days=1)).isoformat()
        # ponytail: 新 cue 一律按"全新卡"初始化（reps=0/EF=2.5/次日复习），
        # 忽略 save_note 入参里可能携带的 review_state 字段（采集阶段无历史状态，
        # 传入视为越界，统一由服务端重置，避免宿主 LLM 伪造记忆进度）。
        cues.append(Cue(
            cue_id=cue_id, question=rc.get("question", ""),
            answer_hint=rc.get("answer_hint", ""),
            review_state=ReviewState(next_review=next_review),
        ))
    return cues


def save_note(note_data: dict[str, Any]) -> dict[str, Any]:
    """保存笔记：pydantic 校验 + cue 初始化 SM-2 状态；非法输入返回 {error}。"""
    storage = get_storage()
    subject = note_data.get("subject", "")
    cornell_raw = note_data.get("cornell") or {}
    raw_cues = cornell_raw.get("cues") or []
    if not raw_cues:
        return {"error": "cornell.cues 至少 1 条"}
    note_id = _generate_note_id(storage) if not note_data.get("note_id") else note_data["note_id"]
    now = _now_utc().isoformat()
    try:
        note = NoteRecord(
            note_id=note_id,
            created_at=note_data.get("created_at", now),
            updated_at=note_data.get("updated_at", now),
            subject=subject,
            knowledge_points=note_data.get("knowledge_points", []),
            cornell=Cornell(
                body=cornell_raw.get("body", ""),
                summary=cornell_raw.get("summary", ""),
                cues=_init_cues(note_id, raw_cues),
            ),
            source=note_data.get("source", {}),
        )
    except (ValueError, TypeError) as exc:
        # MCP 工具须吞掉校验异常返回 {error}，避免工具调用直接崩溃
        return {"error": f"保存失败: {exc}"}
    return storage.save_note(note)


def get_note(note_id: str) -> dict[str, Any]:
    """取单篇笔记（含 cues 复习状态）；不存在返回 {"note": None}。"""
    note = get_storage().load_note(note_id)
    return {"note": note.model_dump() if note else None}


def query_notes(filters: dict[str, Any]) -> dict[str, Any]:
    """按学科/知识点/关键词/日期区间过滤笔记，created_at 倒序。"""
    storage = get_storage()
    notes: list[dict[str, Any]] = []
    for n in storage.get_all_notes():
        if _matches(n, filters or {}):
            notes.append(n.model_dump())
    notes.sort(key=lambda d: d["created_at"], reverse=True)
    return {"notes": notes, "total_count": len(notes)}


def _matches(n: NoteRecord, f: dict[str, Any]) -> bool:
    if f.get("subject") and n.subject != f["subject"]:
        return False
    kp = f.get("knowledge_point")
    if kp and kp not in n.knowledge_points:
        return False
    kw = f.get("keyword")
    if kw and kw not in n.cornell.body and kw not in n.cornell.summary:
        return False
    dr = f.get("date_range")
    if dr:
        created = n.created_at[:10]
        if dr.get("start") and created < dr["start"]:
            return False
        if dr.get("end") and created > dr["end"]:
            return False
    return True


def update_note(note_data: dict[str, Any]) -> dict[str, Any]:
    """全量覆盖更新笔记；question 变更的 cue 重置 review_state，其余保留。"""
    storage = get_storage()
    note_id = note_data.get("note_id")
    if not note_id:
        return {"error": "更新笔记需提供 note_id"}
    old = storage.load_note(note_id)
    if old is None:
        return {"error": f"笔记不存在: {note_id}"}
    old_by_id = {c.cue_id: c for c in old.cornell.cues}
    cornell_raw = note_data.get("cornell") or {}
    raw_cues = cornell_raw.get("cues") or []
    # spec §7 采集规则 #4：cues 至少 1 条（与 save_note 同口径）。
    # 空 cues 会让笔记从复习队列与 Sage 聚合中静默消失，必须拒绝。
    if not raw_cues:
        return {"error": "更新失败：cornell.cues 至少 1 条"
                        "（清空全部线索请直接删除整条笔记）"}
    new_cues: list[Cue] = []
    for i, rc in enumerate(raw_cues, 1):
        cue_id = rc.get("cue_id") or f"{note_id}_c{i}"
        old_cue = old_by_id.get(cue_id)
        # question 变更 → 重置 review_state；否则保留
        if old_cue is not None and rc.get("question") == old_cue.question:
            rs = old_cue.review_state
        else:
            rs = ReviewState(next_review=(_today_utc() + timedelta(days=1)).isoformat())
        new_cues.append(Cue(
            cue_id=cue_id, question=rc.get("question", ""),
            answer_hint=rc.get("answer_hint", ""), review_state=rs,
        ))
    now = _now_utc().isoformat()
    try:
        note = NoteRecord(
            note_id=note_id,
            created_at=old.created_at,
            updated_at=note_data.get("updated_at", now),
            subject=note_data.get("subject", old.subject),
            knowledge_points=note_data.get("knowledge_points", old.knowledge_points),
            cornell=Cornell(
                body=cornell_raw.get("body", old.cornell.body),
                summary=cornell_raw.get("summary", old.cornell.summary),
                cues=new_cues,
            ),
            source=note_data.get("source", old.source),
        )
    except (ValueError, TypeError) as exc:
        return {"error": f"更新失败: {exc}"}
    return storage.update_note(note)


def delete_note(note_id: str) -> dict[str, Any]:
    """删除笔记文件；历史 ReviewRecord 保留为孤儿记录（见 ponytail 注释）。"""
    # ponytail: 删除笔记不级联清理 reviews/*.json —— 孤儿记录保留历史，统计时被忽略；
    # 未来如需清理，可加孤儿回收（按 note_id 匹配），本期接受该已知天花板。
    return {"note_id": note_id, "deleted": get_storage().delete_note(note_id)}
