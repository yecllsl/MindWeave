"""统计工具：按 subject/knowledge_point/date/mastery 分组。"""
from __future__ import annotations

from collections import Counter
from typing import Any

from mindweave_mcp.tools.crud import get_storage

_VALID_GROUPS = {"subject", "knowledge_point", "date", "mastery"}


def _mastery_level(repetitions: int) -> str:
    # ponytail: MVP 用 repetitions 划分掌握度（cue 无持久 grade）；未来可改用最近 ReviewRecord.grade
    if repetitions <= 0:
        return "新卡"
    if repetitions <= 2:
        return "生疏"
    if repetitions <= 4:
        return "熟悉"
    return "掌握"


def get_statistics(group_by: str) -> dict[str, Any]:
    if group_by not in _VALID_GROUPS:
        return {"error": f"不支持的分组维度: {group_by}，支持 {sorted(_VALID_GROUPS)}"}
    storage = get_storage()
    notes = storage.get_all_notes()
    counter: Counter[str] = Counter()
    if group_by == "subject":
        counter = Counter(n.subject for n in notes)
    elif group_by == "knowledge_point":
        counter = Counter(kp for n in notes for kp in n.knowledge_points)
    elif group_by == "date":
        counter = Counter(n.created_at[:10] for n in notes)
    else:  # mastery（按 cue）
        counter = Counter(
            _mastery_level(c.review_state.repetitions)
            for n in notes for c in n.cornell.cues
        )
    items = [{"key": k, "count": v} for k, v in sorted(counter.items())]
    total_cues = sum(len(n.cornell.cues) for n in notes)
    # total = 笔记总数，与 export 的 total_exported 语义对齐（空态=0 供前端/LLM 判断无数据）
    return {
        "group_by": group_by, "items": items,
        "total": len(notes), "total_notes": len(notes), "total_cues": total_cues,
    }
