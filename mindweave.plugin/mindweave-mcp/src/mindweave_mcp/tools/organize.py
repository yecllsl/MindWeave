"""organize_note：三模式返回康奈尔整理 prompt（宿主 LLM 填结构）。"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from mindweave_mcp.prompts.cornell_prompt import render_multimodal_prompt, render_text_prompt
from mindweave_mcp.tools import crud


def _data_dir() -> Path:
    """数据目录单一真相源：复用 crud._DATA_DIR（属性访问，测试 monkeypatch 可传导）。

    organize 不自带 _DATA_DIR 定义——自带会导致隔离 fixture 需 patch 多处，
    且易与 crud 漂移不同步。
    """
    return crud._DATA_DIR


def organize_note(image_path: str = "", text: str = "", subject: str = "") -> dict[str, Any]:
    # 模式 1：对话多模态（无参数）
    if not image_path and not text:
        return {
            "structured_note": None, "mode": "dialog", "parse_prompt": render_multimodal_prompt(),
            "image_path": "", "subject": subject,
            "message": "请使用 parse_prompt 读取对话中的图片完成整理，结果填入 structured_note",
        }
    # 模式 2：本地路径多模态
    if image_path and image_path.strip():
        resolved = Path(image_path).resolve()
        # 仅允许读取 data/images/ 内的图片（spec §7 采集规则 #5），
        # 避免宿主 LLM 以 image_path 指向 notes/reviews 等本地学习数据（prompt 注入放大面）
        if not resolved.is_relative_to((_data_dir() / "images").resolve()):
            return {"structured_note": None, "mode": "multimodal", "image_path": image_path,
                    "error": f"路径越界: {image_path}，仅允许读取 data/images/ 目录内的图片"}
        return {
            "structured_note": None, "mode": "multimodal", "parse_prompt": render_multimodal_prompt(),
            "image_path": image_path, "subject": subject,
            "message": "请使用 parse_prompt 读取指定路径图片完成整理，结果填入 structured_note",
        }
    # 模式 3：文本
    if text and text.strip():
        return {
            "structured_note": None, "mode": "text", "parse_prompt": render_text_prompt(text),
            "image_path": "", "subject": subject,
            "message": "请使用 parse_prompt 完成整理，结果填入 structured_note",
        }
    return {"structured_note": None, "mode": "dialog", "image_path": "", "subject": subject,
            "error": "整理失败：请提供图片（对话上传或本地路径）或文本"}
