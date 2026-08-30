from mindweave_mcp.tools.crud import save_note
from mindweave_mcp.tools.statistics import get_statistics


def test_statistics_invalid_group():
    assert "error" in get_statistics("bad")

def test_statistics_subject_group_empty(isolated_storage):
    r = get_statistics("subject")
    assert r["group_by"] == "subject" and r["total"] == 0

def _seed_two_notes():
    """语文 2 cue 1 卡 + 数学 1 cue 1 卡（含知识点标签）。"""
    save_note({"subject": "语文", "knowledge_points": ["细胞"],
               "cornell": {"body": "b1", "summary": "s1",
                           "cues": [{"question": "q1", "answer_hint": "a1"},
                                    {"question": "q2", "answer_hint": "a2"}]}})
    save_note({"subject": "数学", "knowledge_points": ["函数"],
               "cornell": {"body": "b2", "summary": "s2",
                           "cues": [{"question": "q3", "answer_hint": "a3"}]}})

def test_statistics_subject_with_data(isolated_storage):
    _seed_two_notes()
    r = get_statistics("subject")
    assert r["total"] == 2
    assert {i["key"]: i["count"] for i in r["items"]} == {"语文": 1, "数学": 1}

def test_statistics_knowledge_point(isolated_storage):
    _seed_two_notes()
    r = get_statistics("knowledge_point")
    assert {i["key"]: i["count"] for i in r["items"]} == {"细胞": 1, "函数": 1}

def test_statistics_date(isolated_storage):
    _seed_two_notes()
    r = get_statistics("date")
    assert len(r["items"]) == 1  # 两篇同一天

def test_statistics_mastery_after_reviews(isolated_storage):
    from mindweave_mcp.tools.crud import get_storage
    from mindweave_mcp.tools.review import submit_review
    _seed_two_notes()
    for note in get_storage().get_all_notes():
        for cue in note.cornell.cues:
            submit_review(cue.cue_id, grade=4)  # reps → 1（生疏档）
    r = get_statistics("mastery")
    assert {i["key"] for i in r["items"]} == {"生疏"}
    assert r["total_cues"] == 3
