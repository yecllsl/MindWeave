"""web 路由测试：TestClient + crud._DATA_DIR 单点隔离（与 test_tools 同款 monkeypatch）。"""
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from mindweave_mcp.algorithms import _today_utc
from mindweave_mcp.models import Cornell, Cue, NoteRecord, ReviewState
from mindweave_mcp.tools.crud import get_storage
from mindweave_mcp.web.app import create_app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("mindweave_mcp.tools.crud._DATA_DIR", tmp_path)
    return TestClient(create_app())


def _save_note(note_id="note_20260830_001", subject="生物", due=False):
    n = NoteRecord(
        note_id=note_id, created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00", subject=subject,
        cornell=Cornell(body="光合作用…", summary="光合作用",
                        cues=[Cue(cue_id=f"{note_id}_c1", question="光合作用的场所是？",
                                  answer_hint="叶绿体",
                                  review_state=ReviewState(next_review=(
                                      (_today_utc() + timedelta(days=-1 if due else 1)).isoformat())))]),
    )
    get_storage().save_note(n, overwrite=True)
    return n


def test_dashboard_get_200(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "MindWeave" in r.text


def test_dashboard_summary_shows_counts(client):
    _save_note()
    r = client.get("/")
    assert "总笔记" in r.text and "1" in r.text


# ── notes 列表/详情 ──
def test_notes_list_get_200(client):
    _save_note()
    r = client.get("/notes")
    assert r.status_code == 200
    assert "note_20260830_001" in r.text


def test_notes_list_filter_by_subject(client):
    _save_note(note_id="note_20260830_001", subject="生物")
    _save_note(note_id="note_20260830_002", subject="数学")
    r = client.get("/notes", params={"subject": "数学"})
    assert "note_20260830_002" in r.text
    assert "note_20260830_001" not in r.text


def test_note_detail_get_200(client):
    _save_note()
    r = client.get("/notes/note_20260830_001")
    assert r.status_code == 200
    assert "光合作用的场所是？" in r.text


def test_note_detail_404(client):
    assert client.get("/notes/note_20990101_001").status_code == 404


# ── notes 编辑/删除（人工处理页）──
def test_note_edit_get_form(client):
    _save_note()
    r = client.get("/notes/note_20260830_001/edit")
    assert r.status_code == 200
    assert "光合作用的场所是？" in r.text  # 表单回显既有 cue
    assert "修改线索问题" in r.text  # 提示文案


def test_note_edit_post_updates_note(client):
    _save_note()
    r = client.post("/notes/note_20260830_001/edit", data={
        "subject": "化学", "knowledge_points": "细胞,代谢",
        "body": "新笔记栏", "summary": "新总结",
        "cue_id": "note_20260830_001_c1",
        "cue_question": "新问题", "cue_answer_hint": "新答案",
    }, follow_redirects=False)
    assert r.status_code == 303
    note = get_storage().load_note("note_20260830_001")
    assert note.subject == "化学" and note.cornell.body == "新笔记栏"
    assert note.cornell.cues[0].question == "新问题"


def test_note_edit_question_change_resets_review_state(client):
    """question 变更 → review_state 重置（update_note 既有规则经 web 路径生效）。"""
    from mindweave_mcp.tools.crud import get_note
    from mindweave_mcp.tools.review import submit_review
    _save_note(due=True)
    submit_review("note_20260830_001_c1", 4)  # reps 0→1
    client.post("/notes/note_20260830_001/edit", data={
        "subject": "生物", "knowledge_points": "", "body": "", "summary": "",
        "cue_id": "note_20260830_001_c1",
        "cue_question": "改后的问题", "cue_answer_hint": "叶绿体",
    })
    rs = get_note("note_20260830_001")["note"]["cornell"]["cues"][0]["review_state"]
    assert rs["repetitions"] == 0 and rs["interval"] == 0


def test_note_edit_add_and_delete_cues(client):
    """cue 增删改：删 c1、保留 c2、新增一行（cue_id 空）。"""
    from mindweave_mcp.models import Cornell, Cue, NoteRecord
    n = NoteRecord(
        note_id="note_20260830_002", created_at="2026-08-30T00:00:00",
        updated_at="2026-08-30T00:00:00", subject="数学",
        cornell=Cornell(cues=[
            Cue(cue_id="note_20260830_002_c1", question="旧1"),
            Cue(cue_id="note_20260830_002_c2", question="旧2"),
        ]),
    )
    get_storage().save_note(n, overwrite=True)
    client.post("/notes/note_20260830_002/edit", data={
        "subject": "数学", "knowledge_points": "", "body": "", "summary": "",
        "cue_id": ["note_20260830_002_c1", "note_20260830_002_c2", ""],
        "cue_question": ["旧1", "旧2改", "全新问题"],
        "cue_answer_hint": ["", "hint2", "hint3"],
        "cue_del": "note_20260830_002_c1",
    })
    cues = get_storage().load_note("note_20260830_002").cornell.cues
    assert [c.question for c in cues] == ["旧2改", "全新问题"]
    # 新 cue 分配不碰撞 id
    assert cues[1].cue_id == "note_20260830_002_c3"


def test_note_delete_post(client):
    _save_note()
    r = client.post("/notes/note_20260830_001/delete", follow_redirects=False)
    assert r.status_code == 303
    assert get_storage().load_note("note_20260830_001") is None


# ── review ──
def test_review_get_200(client):
    _save_note(due=True)
    r = client.get("/review")
    assert r.status_code == 200
    assert "光合作用的场所是？" in r.text


def test_review_submit_updates_sm2(client):
    _save_note(due=True)
    r = client.post("/review/submit", data={
        "cue_id": "note_20260830_001_c1", "grade": "4",
    }, follow_redirects=False)
    assert r.status_code == 303
    rs = get_storage().load_note("note_20260830_001").cornell.cues[0].review_state
    assert rs.repetitions == 1
    assert len(get_storage().list_all_review_records()) == 1


def test_review_submit_invalid_grade(client):
    _save_note(due=True)
    r = client.post("/review/submit", data={
        "cue_id": "note_20260830_001_c1", "grade": "9",
    }, follow_redirects=False)
    assert r.status_code == 422
