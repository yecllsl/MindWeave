from mindweave_mcp.models import Cornell, Cue, NoteRecord, QuizRecord, ReviewRecord


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


# ── v0.2 quizzes CRUD ──
def _make_quiz(quiz_id="quiz_20260830_001"):
    return QuizRecord(
        quiz_id=quiz_id, note_id="note_20260830_001",
        cue_id="note_20260830_001_c1", quiz_type="选择",
        question="q", options=["A", "B", "C", "D"], answer="A",
        created_at="2026-08-30T00:00:00",
    )


def test_storage_creates_quizzes_dir(storage):
    assert storage.quizzes_dir.exists() and storage.quizzes_dir.is_dir()


def test_storage_save_and_load_quiz(storage):
    r = storage.save_quiz(_make_quiz())
    assert "error" not in r
    loaded = storage.load_quiz("quiz_20260830_001")
    assert loaded is not None and loaded.answer == "A"


def test_storage_load_quiz_missing_returns_none(storage):
    assert storage.load_quiz("quiz_20990101_001") is None


def test_storage_list_all_quiz_ids(storage):
    storage.save_quiz(_make_quiz("quiz_20260830_001"))
    storage.save_quiz(_make_quiz("quiz_20260830_002"))
    assert set(storage.list_all_quiz_ids()) == {"quiz_20260830_001", "quiz_20260830_002"}
