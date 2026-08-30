from mindweave_mcp.tools.crud import (
    delete_note,
    get_note,
    get_storage,
    save_note,
    update_note,
)


def _note_data(subject="语文", cues=None, note_id=None):
    d = {
        "subject": subject, "knowledge_points": ["细胞"],
        "cornell": {"body": "b", "summary": "s",
                    "cues": cues if cues is not None else [{"question": "q1", "answer_hint": "a1"}]},
    }
    if note_id:
        d["note_id"] = note_id
    return d

def test_save_initializes_sm2(isolated_storage):
    r = save_note(_note_data())
    assert "note_id" in r and r["note_id"].startswith("note_")
    note = get_note(r["note_id"])["note"]
    cue = note["cornell"]["cues"][0]
    rs = cue["review_state"]
    assert rs["repetitions"] == 0 and rs["ease_factor"] == 2.5
    assert rs["next_review"] != ""  # 次日

def test_save_requires_cues(isolated_storage):
    r = save_note(_note_data(cues=[]))
    assert "error" in r

def test_update_requires_cues(isolated_storage):
    # spec §7 #4 硬约束：update 与 save 同口径，拒绝清空全部线索
    r = save_note(_note_data())
    upd = _note_data(cues=[])
    upd["note_id"] = r["note_id"]
    res = update_note(upd)
    assert "error" in res
    # 原笔记未被破坏
    assert len(get_note(r["note_id"])["note"]["cornell"]["cues"]) == 1

def test_save_invalid_subject_returns_error(isolated_storage):
    # pydantic ValueError 被捕获为 {error}，而非抛异常
    r = save_note(_note_data(subject="音乐"))
    assert "error" in r

def test_update_question_resets_review_state(isolated_storage):
    r = save_note(_note_data())
    note = get_note(r["note_id"])["note"]
    cue_id = note["cornell"]["cues"][0]["cue_id"]
    # 手动把 reps 抬到 3 再更新 question
    st = get_storage()
    n = st.load_note(r["note_id"])
    n.cornell.cues[0].review_state.repetitions = 3
    st.update_note(n)
    # question 变更 → 重置
    upd = _note_data(cues=[{"cue_id": cue_id, "question": "q1-CHANGED", "answer_hint": "a1"}])
    upd["note_id"] = r["note_id"]
    update_note(upd)
    note2 = get_note(r["note_id"])["note"]
    assert note2["cornell"]["cues"][0]["review_state"]["repetitions"] == 0

def test_delete_note(isolated_storage):
    r = save_note(_note_data())
    assert delete_note(r["note_id"])["deleted"] is True
    assert get_note(r["note_id"])["note"] is None
