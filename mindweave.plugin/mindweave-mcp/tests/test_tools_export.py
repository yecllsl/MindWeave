from pathlib import Path

from mindweave_mcp.tools.crud import save_note
from mindweave_mcp.tools.export import export_data


def test_export_invalid_format(isolated_storage):
    assert "error" in export_data("xml")

def test_export_json_empty(isolated_storage):
    r = export_data("json")
    assert "file_path" in r and r["total_exported"] == 0

def test_export_json_with_data_and_filter(isolated_storage):
    save_note({"subject": "语文", "knowledge_points": ["细胞"],
               "cornell": {"body": "b1", "summary": "s1",
                           "cues": [{"question": "q1", "answer_hint": "a1"}]}})
    save_note({"subject": "数学", "knowledge_points": ["函数"],
               "cornell": {"body": "b2", "summary": "s2",
                           "cues": [{"question": "q3", "answer_hint": "a3"}]}})
    r = export_data("json", filters={"subject": "语文"})
    assert r["total_exported"] == 1
    import json
    data = json.loads(Path(r["file_path"]).read_text(encoding="utf-8"))
    assert data[0]["subject"] == "语文"

def test_export_markdown_with_data(isolated_storage):
    r = save_note({"subject": "语文", "knowledge_points": ["细胞"],
                   "cornell": {"body": "b1", "summary": "s1",
                               "cues": [{"question": "q1", "answer_hint": "a1"}]}})
    note_id = r["note_id"]
    r = export_data("markdown")
    assert r["total_exported"] == 1
    text = Path(r["file_path"]).read_text(encoding="utf-8")
    assert note_id in text and "q1" in text
