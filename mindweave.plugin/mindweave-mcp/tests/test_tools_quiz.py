"""quiz 工具链测试：generate（占位落盘）/ save（校验回写）。"""
from mindweave_mcp.tools.crud import get_storage
from mindweave_mcp.tools.quiz import generate_quiz, save_quiz


def _save_note(cues=None, subject="生物", note_id="note_20260830_001"):
    """直构笔记落盘：默认 1 cue（今日到期）。"""
    from datetime import timedelta

    from mindweave_mcp.algorithms import _today_utc
    from mindweave_mcp.models import Cornell, Cue, NoteRecord, ReviewState
    n = NoteRecord(
        note_id=note_id, created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00", subject=subject,
        cornell=Cornell(body="光合作用是绿色植物利用光能…", summary="光合作用",
                        cues=cues or [Cue(
                            cue_id=f"{note_id}_c1", question="光合作用的场所是？",
                            answer_hint="叶绿体",
                            review_state=ReviewState(
                                next_review=(_today_utc() + timedelta(days=-1)).isoformat()),
                        )]),
    )
    get_storage().save_note(n, overwrite=True)
    return n


def test_generate_quiz_creates_placeholder(isolated_storage):
    _save_note()
    r = generate_quiz(cue_id="note_20260830_001_c1", quiz_type="选择")
    assert "quiz_id" in r and "generate_prompt" in r
    quiz = get_storage().load_quiz(r["quiz_id"])
    assert quiz is not None
    assert quiz.answer == "" and quiz.quiz_type == "选择"
    assert quiz.cue_id == "note_20260830_001_c1"
    assert "叶绿体" in r["generate_prompt"]


def test_generate_quiz_missing_cue_returns_error(isolated_storage):
    _save_note()
    assert "error" in generate_quiz(cue_id="nonexistent_c1", quiz_type="选择")


def test_generate_quiz_fill_uses_cue_material(isolated_storage):
    _save_note()
    r = generate_quiz(cue_id="note_20260830_001_c1", quiz_type="填空")
    quiz = get_storage().load_quiz(r["quiz_id"])
    assert quiz.quiz_type == "填空" and quiz.options == []


def test_generate_quiz_choice_prompt_has_distractor_pool(isolated_storage):
    """选择题 prompt 含同学科其他 cue 作为干扰项素材。"""
    from mindweave_mcp.models import Cornell, Cue, NoteRecord
    _save_note(note_id="note_20260830_001")
    n2 = NoteRecord(
        note_id="note_20260830_002", created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00", subject="生物",
        cornell=Cornell(cues=[Cue(cue_id="note_20260830_002_c1", question="线粒体的功能是？")]),
    )
    get_storage().save_note(n2, overwrite=True)
    r = generate_quiz(cue_id="note_20260830_001_c1", quiz_type="选择")
    assert "线粒体的功能是？" in r["generate_prompt"]


def test_save_quiz_writes_back_valid(isolated_storage):
    _save_note()
    r = generate_quiz(cue_id="note_20260830_001_c1", quiz_type="选择")
    qid = r["quiz_id"]
    back = save_quiz(qid, {
        "question": "光合作用主要发生在哪个细胞器？",
        "options": ["叶绿体", "线粒体", "核糖体", "内质网"],
        "answer": "叶绿体",
    })
    assert "error" not in back
    quiz = get_storage().load_quiz(qid)
    assert quiz.question == "光合作用主要发生在哪个细胞器？"
    assert quiz.answer == "叶绿体" and len(quiz.options) == 4


def test_save_quiz_invalid_choice_answer_rejected(isolated_storage):
    """answer 不在 options 中直接拒绝（模型硬防线）。"""
    _save_note()
    r = generate_quiz(cue_id="note_20260830_001_c1", quiz_type="选择")
    back = save_quiz(r["quiz_id"], {
        "question": "q", "options": ["A", "B", "C", "D"], "answer": "E",
    })
    assert "error" in back
    # 占位 quiz 未被破坏
    quiz = get_storage().load_quiz(r["quiz_id"])
    assert quiz.answer == ""


def test_save_quiz_missing_quiz_returns_error(isolated_storage):
    assert "error" in save_quiz("quiz_20990101_001", {"question": "q", "answer": "a"})


def test_save_quiz_forbidden_fields_ignored(isolated_storage):
    """quiz_id/cue_id/note_id/answered 等服务端字段不可经 quiz_data 篡改。"""
    _save_note()
    r = generate_quiz(cue_id="note_20260830_001_c1", quiz_type="填空")
    back = save_quiz(r["quiz_id"], {
        "question": "q", "answer": "叶绿体",
        "quiz_id": "quiz_20990101_999", "answered": True, "grade": 4,
    })
    assert "error" not in back
    quiz = get_storage().load_quiz(r["quiz_id"])
    assert quiz.quiz_id == r["quiz_id"] and quiz.answered is False and quiz.grade is None
