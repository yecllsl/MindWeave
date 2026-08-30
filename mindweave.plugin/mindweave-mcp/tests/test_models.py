import pytest
from pydantic import ValidationError as PydValidationError

from mindweave_mcp.models import (
    SUBJECTS,
    Cornell,
    Cue,
    NoteRecord,
    QuizRecord,
    ReviewRecord,
    ReviewState,
)


def test_subjects_exactly_nine():
    assert SUBJECTS == ["语文", "数学", "英语", "物理", "化学", "生物", "政治", "历史", "地理"]

def test_review_state_defaults():
    rs = ReviewState()
    assert rs.repetitions == 0 and rs.ease_factor == 2.5
    assert rs.interval == 0 and rs.next_review == ""

def test_note_subject_enum_validated():
    with pytest.raises(ValueError):
        NoteRecord(
            note_id="note_20260830_001", created_at="2026-08-30T00:00:00",
            updated_at="2026-08-30T00:00:00", subject="音乐",
            cornell=Cornell(cues=[Cue(cue_id="note_20260830_001_c1", question="q")]),
        )

def test_note_id_prefix_validated():
    # Cornell 有 min_length=1 硬约束，此处须传占位 cue 才能触达 note_id 校验
    with pytest.raises(ValueError):
        NoteRecord(
            note_id="bad_001", created_at="", updated_at="", subject="语文",
            cornell=Cornell(cues=[Cue(cue_id="note_20260830_001_c1", question="q")]),
        )

def test_cornell_requires_at_least_one_cue():
    # spec §7 #4 硬约束在模型层的兜底（评审 B4 后 cues 为必填）：
    # 不传 cues → Field required；传空列表 → min_length=1，两条路径均拒绝
    with pytest.raises(ValueError):
        Cornell()
    with pytest.raises(ValueError):
        Cornell(body="b", summary="s", cues=[])

def test_cue_id_prefix_validated():
    with pytest.raises(ValueError):
        Cue(cue_id="bad_c1", question="q")

def test_review_record_grade_range():
    with pytest.raises(ValueError):
        ReviewRecord(record_id="r1", note_id="n1", cue_id="c1", review_time="", grade=5)


# ── v0.2 QuizRecord ──
def _quiz(**kw):
    base = dict(
        quiz_id="quiz_20260830_001", note_id="note_20260830_001",
        cue_id="note_20260830_001_c1", quiz_type="选择",
        question="q", options=["A", "B", "C", "D"], answer="A",
        created_at="2026-08-30T00:00:00",
    )
    base.update(kw)
    return QuizRecord(**base)


def test_quizrecord_minimal_placeholder():
    """占位 quiz：answer 空、options 空、question 占位，合法。"""
    q = _quiz(question="（占位题干）", options=[], answer="")
    assert q.answered is False and q.grade is None


def test_quizrecord_bad_quiz_id_rejected():
    with pytest.raises(PydValidationError):
        _quiz(quiz_id="bad_001")


def test_quizrecord_bad_quiz_type_rejected():
    with pytest.raises(PydValidationError):
        _quiz(quiz_type="拼写")


def test_quizrecord_bad_grade_rejected():
    with pytest.raises(PydValidationError):
        _quiz(answered=True, grade=5)


def test_quizrecord_choice_answer_must_be_in_options():
    """选择题 answer 非 empty 时必须 ∈ options（判分『所选==answer』前提，评审 P3-6）。"""
    with pytest.raises(PydValidationError):
        _quiz(answer="E")


def test_quizrecord_choice_requires_4_options_when_answer_set():
    """answer 非空时选择题须恰 4 项（校验看 answer 非空，非 answered）。"""
    with pytest.raises(PydValidationError):
        _quiz(options=["A", "B"], answer="A")


def test_quizrecord_fill_allows_empty_options():
    """填空题 options 为空、answer 为参考答案，合法。"""
    q = _quiz(quiz_type="填空", options=[], answer="光合作用")
    assert q.quiz_type == "填空"


def test_reviewrecord_source_default_self():
    """v0.1 旧记录缺 source 字段反序列化默认 self（向后兼容）。"""
    rec = ReviewRecord.model_validate({
        "record_id": "review_20260830_00000000_ab12cd34_note_20260830_001_c1",
        "note_id": "note_20260830_001", "cue_id": "note_20260830_001_c1",
        "review_time": "2026-08-30T00:00:00", "grade": 3,
    })
    assert rec.source == "self"


def test_reviewrecord_source_bad_value_rejected():
    with pytest.raises(PydValidationError):
        ReviewRecord.model_validate({
            "record_id": "r", "note_id": "note_20260830_001",
            "cue_id": "note_20260830_001_c1",
            "review_time": "2026-08-30T00:00:00", "grade": 3, "source": "other",
        })
