from mindweave_mcp.tools.organize import organize_note


def test_dialog_mode_no_args():
    r = organize_note()
    assert r["mode"] == "dialog" and r["structured_note"] is None
    assert "parse_prompt" in r

def test_text_mode():
    r = organize_note(text="细胞膜的结构")
    assert r["mode"] == "text" and "细胞膜" in r["parse_prompt"]

def test_multimodal_mode_valid_path(isolated_storage):
    # 图片建在隔离后的 data/ 内（isolated_storage 即 tmp data 根）
    img_dir = isolated_storage / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    img = img_dir / "a.png"
    img.write_bytes(b"x")
    r = organize_note(image_path=str(img))
    assert r["mode"] == "multimodal" and "error" not in r

def test_multimodal_path_escape_rejected(isolated_storage, tmp_path_factory):
    # 另一处 tmp 目录，必在隔离 data/ 之外
    outside_dir = tmp_path_factory.mktemp("outside")
    outside = outside_dir / "outside.png"
    outside.write_bytes(b"x")
    r = organize_note(image_path=str(outside))
    assert "error" in r

def test_no_input_error():
    r = organize_note(image_path="", text="")
    assert r["mode"] == "dialog"  # 空参即对话模式
