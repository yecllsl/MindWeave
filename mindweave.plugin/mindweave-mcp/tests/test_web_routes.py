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
