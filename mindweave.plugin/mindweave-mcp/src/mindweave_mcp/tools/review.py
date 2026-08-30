"""复习工具：schedule_review（到期队列）+ submit_review（自评 → SM-2 更新）。"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from mindweave_mcp.algorithms import _now_utc, _today_utc, compute_next_review
from mindweave_mcp.models import ReviewRecord
from mindweave_mcp.tools.crud import get_storage


def schedule_review(subject: str = "", limit: int = 10) -> dict[str, Any]:
    """返回到期 cue 队列（next_review <= 今天，可按学科筛）。"""
    storage = get_storage()
    today = _today_utc().isoformat()
    due: list[dict[str, Any]] = []
    for note in storage.get_all_notes():
        if subject and note.subject != subject:
            continue
        for cue in note.cornell.cues:
            nr = cue.review_state.next_review
            if nr and nr <= today:
                due.append({"note_id": note.note_id, "cue_id": cue.cue_id,
                            "question": cue.question, "due_date": nr})
    due.sort(key=lambda d: (d["due_date"], d["cue_id"]))
    # due_count = 全部到期数；limit = 上限；returned = 本次实际返回数（受 limit 截断）
    return {"today": today, "due_count": len(due), "limit": limit,
            "returned": len(due[:limit]), "due_cues": due[:limit]}


def submit_review(cue_id: str, grade: int) -> dict[str, Any]:
    """cue 自评 1-4 → SM-2 更新（<3 重置周期）+ 写 ReviewRecord。"""
    storage = get_storage()
    for note in storage.get_all_notes():
        for cue in note.cornell.cues:
            if cue.cue_id == cue_id:
                rs = cue.review_state
                # grade 越界（宿主 LLM 传参错误的现实高频路径）须兜底为 {error}，
                # 绝不让 MCP 工具抛异常
                try:
                    r = compute_next_review(rs.ease_factor, rs.interval, rs.repetitions, grade)
                except ValueError as exc:
                    return {"error": f"复习评分失败: {exc}"}
                cue.review_state.ease_factor = r["ease_factor"]
                cue.review_state.interval = r["interval"]
                cue.review_state.repetitions = r["repetitions"]
                cue.review_state.next_review = r["next_review_date"]
                storage.update_note(note)
                # ponytail: note 与 record 为两次独立文件写，进程在两者间崩溃会产生
                # 「review_state 已推进但 ReviewRecord 缺失」的不一致（Sage recent_activity 漏记）。
                # 单用户本地场景概率极低，本期接受；升级路径：先写 record 再写 note。
                # record_id 追加 uuid4 前 8 位：同秒同 cue 重复提交也不碰撞
                rec = ReviewRecord(
                    record_id=f"review_{_now_utc().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}_{cue_id}",
                    note_id=note.note_id, cue_id=cue_id,
                    review_time=_now_utc().isoformat(), grade=grade,
                )
                storage.save_review_record(rec)
                return {"cue_id": cue_id, "grade": grade,
                        "next_review": r["next_review_date"],
                        "repetitions": r["repetitions"], "ease_factor": r["ease_factor"]}
    return {"error": f"cue 不存在: {cue_id}"}
