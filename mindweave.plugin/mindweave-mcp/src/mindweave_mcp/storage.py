"""本地 JSON 文件存储引擎（原子写）。目录：notes/ reviews/ exports/ images/。"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from mindweave_mcp.models import NoteRecord, ReviewRecord


class Storage:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.notes_dir = self.base_dir / "notes"
        self.reviews_dir = self.base_dir / "reviews"
        self.exports_dir = self.base_dir / "exports"
        self.images_dir = self.base_dir / "images"
        for d in [self.notes_dir, self.reviews_dir, self.exports_dir, self.images_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _atomic_write(fp: Path, data: str) -> None:
        tmp_fp = fp.with_suffix(fp.suffix + ".tmp")
        tmp_fp.write_text(data, encoding="utf-8")
        os.replace(tmp_fp, fp)

    # ── note CRUD ──
    def save_note(self, note: NoteRecord, overwrite: bool = False) -> dict[str, Any]:
        fp = self.notes_dir / f"{note.note_id}.json"
        if fp.exists() and not overwrite:
            return {"error": f"笔记已存在，禁止覆盖: {note.note_id}"}
        self._atomic_write(fp, note.model_dump_json(indent=2, ensure_ascii=False))
        return {"note_id": note.note_id, "saved_path": str(fp)}

    def load_note(self, note_id: str) -> NoteRecord | None:
        fp = self.notes_dir / f"{note_id}.json"
        if not fp.exists():
            return None
        return NoteRecord.model_validate(json.loads(fp.read_text(encoding="utf-8")))

    def update_note(self, note: NoteRecord) -> dict[str, Any]:
        return self.save_note(note, overwrite=True)

    def delete_note(self, note_id: str) -> bool:
        fp = self.notes_dir / f"{note_id}.json"
        if fp.exists():
            fp.unlink()
            return True
        return False

    def list_all_note_ids(self) -> list[str]:
        return [f.stem for f in self.notes_dir.glob("*.json")]

    def get_all_notes(self) -> list[NoteRecord]:
        return [n for nid in self.list_all_note_ids() if (n := self.load_note(nid))]

    # ── review CRUD ──
    def save_review_record(self, record: ReviewRecord) -> dict[str, Any]:
        fp = self.reviews_dir / f"{record.record_id}.json"
        self._atomic_write(fp, record.model_dump_json(indent=2, ensure_ascii=False))
        return {"record_id": record.record_id, "saved_path": str(fp)}

    def list_all_review_records(self) -> list[ReviewRecord]:
        return [
            ReviewRecord.model_validate(json.loads(fp.read_text(encoding="utf-8")))
            for fp in self.reviews_dir.glob("*.json")
        ]
