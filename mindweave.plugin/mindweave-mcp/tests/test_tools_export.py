from mindweave_mcp.tools.export import export_data


def test_export_invalid_format(isolated_storage):
    assert "error" in export_data("xml")

def test_export_json_empty(isolated_storage):
    r = export_data("json")
    assert "file_path" in r and r["total_exported"] == 0
