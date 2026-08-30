from mindweave_mcp.models import Cornell, Cue, NoteRecord, ReviewRecord


def _note(note_id="note_20260830_001"):
    return NoteRecord(
        note_id=note_id, created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00", subject="语文",
        cornell=Cornell(body="b", summary="s",
                        cues=[Cue(cue_id=f"{note_id}_c1", question="q")]),
    )

def test_save_and_load_note(storage):
    storage.save_note(_note())
    loaded = storage.load_note("note_20260830_001")
    assert loaded is not None and loaded.subject == "语文"

def test_save_duplicate_not_overwrite(storage):
    storage.save_note(_note())
    res = storage.save_note(_note())
    assert "error" in res

def test_update_overwrites(storage):
    storage.save_note(_note())
    n = _note()
    n.cornell.body = "updated"
    storage.update_note(n)
    assert storage.load_note("note_20260830_001").cornell.body == "updated"

def test_delete_note(storage):
    storage.save_note(_note())
    assert storage.delete_note("note_20260830_001") is True
    assert storage.load_note("note_20260830_001") is None

def test_save_review_record_and_list(storage):
    storage.save_review_record(ReviewRecord(record_id="r1", note_id="n1", cue_id="c1", review_time="t", grade=4))
    assert len(storage.list_all_review_records()) == 1
