"""导出工具：json / markdown，落 data/exports/。"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from mindweave_mcp.tools import crud

_VALID_FORMATS = {"json", "markdown"}


def export_data(format: str = "json", filters: dict[str, Any] | None = None) -> dict[str, Any]:
    if format not in _VALID_FORMATS:
        return {"error": f"不支持的格式: {format}，支持 {sorted(_VALID_FORMATS)}"}
    storage = crud.get_storage()
    # 复用 query 过滤逻辑（导入避免循环：query_notes 在 crud）
    notes = crud.query_notes(filters or {})["notes"]

    # 经 get_storage().exports_dir 取目录：get_storage 用 crud._DATA_DIR 构造，
    # 测试 monkeypatch crud._DATA_DIR 时一并隔离（避免按值 import 导致 patch 失效）
    exports_dir = storage.exports_dir
    exports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    if format == "json":
        fp = exports_dir / f"notes_{timestamp}.json"
        fp.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    else:  # markdown
        fp = exports_dir / f"notes_{timestamp}.md"
        lines = []
        for n in notes:
            lines.append(f"# {n['note_id']} · {n['subject']}")
            if n["knowledge_points"]:
                lines.append("知识点: " + "、".join(n["knowledge_points"]))
            lines.append("\n## 笔记栏\n" + n["cornell"]["body"])
            lines.append("\n## 总结\n" + n["cornell"]["summary"])
            lines.append("\n## 线索")
            for c in n["cornell"]["cues"]:
                lines.append(f"- Q: {c['question']}（A: {c['answer_hint']}）")
            lines.append("")
        fp.write_text("\n".join(lines), encoding="utf-8")
    return {"file_path": str(fp), "total_exported": len(notes)}
