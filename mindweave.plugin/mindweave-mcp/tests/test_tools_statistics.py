from mindweave_mcp.tools.statistics import get_statistics


def test_statistics_invalid_group():
    assert "error" in get_statistics("bad")

def test_statistics_subject_group_empty(isolated_storage):
    r = get_statistics("subject")
    assert r["group_by"] == "subject" and r["total"] == 0
