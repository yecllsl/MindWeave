import pytest

from mindweave_mcp.models import (
    SUBJECTS,
    Cornell,
    Cue,
    NoteRecord,
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
