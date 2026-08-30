from mindweave_mcp.tools.crud import get_note
from mindweave_mcp.tools.review import schedule_review, submit_review


def _save_due(next_review):
    # 直接构造带指定 next_review 的笔记并落盘
    from mindweave_mcp.models import Cornell, Cue, NoteRecord, ReviewState
    from mindweave_mcp.tools.crud import get_storage  # 调用时读取 crud._DATA_DIR，隔离生效
    n = NoteRecord(
        note_id="note_20260830_001", created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00", subject="语文",
        cornell=Cornell(cues=[Cue(cue_id="note_20260830_001_c1", question="q",
                                   review_state=ReviewState(next_review=next_review))]),
    )
    get_storage().save_note(n, overwrite=True)

def test_schedule_only_due(isolated_storage):
    _save_due("2020-01-01")  # 已过期
    r = schedule_review()
    assert r["due_count"] == 1 and r["returned"] == 1
    assert r["due_cues"][0]["cue_id"] == "note_20260830_001_c1"

def test_schedule_excludes_future(isolated_storage):
    _save_due("2099-01-01")
    r = schedule_review()
    assert r["due_count"] == 0 and r["returned"] == 0

def test_submit_review_grade_lt3_resets(isolated_storage):
    _save_due("2020-01-01")
    r = submit_review(cue_id="note_20260830_001_c1", grade=2)
    assert "next_review" in r
    note = get_note("note_20260830_001")["note"]
    rs = note["cornell"]["cues"][0]["review_state"]
    assert rs["repetitions"] == 0 and rs["interval"] == 1

def test_submit_review_writes_review_record(isolated_storage):
    _save_due("2020-01-01")
    submit_review(cue_id="note_20260830_001_c1", grade=3)
    from mindweave_mcp.tools.crud import get_storage
    assert len(get_storage().list_all_review_records()) == 1

def test_submit_invalid_grade_returns_error(isolated_storage):
    _save_due("2020-01-01")
    r = submit_review(cue_id="note_20260830_001_c1", grade=5)
    assert "error" in r
    # 原状态未被破坏
    note = get_note("note_20260830_001")["note"]
    assert note["cornell"]["cues"][0]["review_state"]["repetitions"] == 0

def test_submit_missing_cue_returns_error(isolated_storage):
    assert "error" in submit_review(cue_id="nonexistent_c1", grade=3)
