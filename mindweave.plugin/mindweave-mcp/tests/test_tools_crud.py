from mindweave_mcp.tools.crud import (
    delete_note,
    get_note,
    get_storage,
    query_notes,
    save_note,
    update_note,
)
from mindweave_mcp.tools.review import submit_review


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

def test_update_same_question_preserves_review_state(isolated_storage):
    # spec §7 规则 7：question 未变更 → 保留 review_state（不重置）
    r = save_note(_note_data())
    note = get_note(r["note_id"])["note"]
    cue_id = note["cornell"]["cues"][0]["cue_id"]
    st = get_storage()
    n = st.load_note(r["note_id"])
    n.cornell.cues[0].review_state.repetitions = 3
    st.update_note(n)
    # 同 cue 同 question 更新（仅改 answer_hint）→ reps 保持 3
    upd = _note_data(cues=[{"cue_id": cue_id, "question": "q1", "answer_hint": "a1-NEW"}])
    upd["note_id"] = r["note_id"]
    update_note(upd)
    note2 = get_note(r["note_id"])["note"]
    rs = note2["cornell"]["cues"][0]["review_state"]
    # 复习状态保留（reps 仍 3），内容字段（answer_hint）正常更新
    assert rs["repetitions"] == 3
    assert note2["cornell"]["cues"][0]["answer_hint"] == "a1-NEW"

def test_query_notes_filters(isolated_storage):
    # 显式 created_at，避免两次 save 的默认 now 同微秒导致倒序不稳定
    save_note({"subject": "语文", "knowledge_points": ["细胞"],
               "created_at": "2026-08-30T00:00:00", "note_id": "note_20260830_001",
               "cornell": {"body": "b", "summary": "s",
                           "cues": [{"question": "q1", "answer_hint": "a1"}]}})
    save_note({"subject": "数学", "knowledge_points": ["函数"],
               "created_at": "2026-08-30T00:00:01", "note_id": "note_20260830_002",
               "cornell": {"body": "b", "summary": "s",
                           "cues": [{"question": "q2", "answer_hint": "a2"}]}})
    # subject 过滤
    assert query_notes({"subject": "数学"})["total_count"] == 1
    # knowledge_point 过滤
    assert query_notes({"knowledge_point": "细胞"})["total_count"] == 1
    assert query_notes({"knowledge_point": "函数"})["total_count"] == 1
    assert query_notes({"knowledge_point": "不存在"})["total_count"] == 0
    # keyword 过滤（搜 body）
    assert query_notes({"keyword": "b"})["total_count"] == 2
    assert query_notes({"keyword": "zzz"})["total_count"] == 0
    # date_range 过滤
    assert query_notes({"date_range": {"start": "2026-08-30", "end": "2026-08-30"}})["total_count"] == 2
    assert query_notes({"date_range": {"start": "2026-09-01"}})["total_count"] == 0
    # 无过滤返回全部，created_at 倒序（后保存的在前）
    all_notes = query_notes({})["notes"]
    assert len(all_notes) == 2 and all_notes[0]["note_id"] == "note_20260830_002"

def test_delete_leaves_orphan_review_records(isolated_storage):
    # 删除笔记后，历史 ReviewRecord 保留为孤儿记录（统计忽略，spec §8 ponytail）
    r = save_note(_note_data())
    note = get_note(r["note_id"])["note"]
    cue_id = note["cornell"]["cues"][0]["cue_id"]
    submit_review(cue_id, grade=4)
    assert len(get_storage().list_all_review_records()) == 1
    delete_note(r["note_id"])
    # 笔记已删，但复习记录仍在（孤儿）
    assert len(get_storage().list_all_review_records()) == 1
    assert get_note(r["note_id"])["note"] is None


def test_generate_id_generic_prefix(isolated_storage):
    """前缀参数化的通用 _generate_id：note 与 quiz 各自独立递增（评审 P3-5）。"""
    from mindweave_mcp.algorithms import _now_utc
    from mindweave_mcp.tools.crud import _generate_id
    stamp = _now_utc().strftime("%Y%m%d")
    assert _generate_id("quiz", []) == f"quiz_{stamp}_001"
    assert _generate_id("quiz", [f"quiz_{stamp}_001"]) == f"quiz_{stamp}_002"
