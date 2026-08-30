"""MindWeave MCP Server 入口（13 个工具）。"""
from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from mindweave_mcp.tools import crud, export, organize, quiz, review, statistics

mcp = FastMCP(name="mindweave-mcp", instructions="K12 康奈尔 AI 智能笔记 MCP Server")


@mcp.tool()
def organize_note(image_path: str = "", text: str = "", subject: str = "") -> dict[str, Any]:
    """返回康奈尔整理 prompt（三模式：对话多模态 > image_path > text），宿主 LLM 填结构。"""
    return organize.organize_note(image_path, text, subject)


@mcp.tool()
def save_note(note_data: dict[str, Any]) -> dict[str, Any]:
    """pydantic 校验 + 保存笔记（cue 初始化 SM-2 状态）。"""
    return crud.save_note(note_data)


@mcp.tool()
def get_note(note_id: str) -> dict[str, Any]:
    """取单篇笔记（含 cues 复习状态）。"""
    return crud.get_note(note_id)


@mcp.tool()
def query_notes(filters: dict[str, Any]) -> dict[str, Any]:
    """按学科/知识点/日期/关键词过滤。"""
    return crud.query_notes(filters)


@mcp.tool()
def update_note(note_data: dict[str, Any]) -> dict[str, Any]:
    """更新笔记（question 变更重置该 cue 的 review_state）。"""
    return crud.update_note(note_data)


@mcp.tool()
def delete_note(note_id: str) -> dict[str, Any]:
    """删除笔记。"""
    return crud.delete_note(note_id)


@mcp.tool()
def schedule_review(subject: str = "", limit: int = 10) -> dict[str, Any]:
    """到期 cue 队列（next_review <= 今天，可按学科筛）。"""
    return review.schedule_review(subject, limit)


@mcp.tool()
def submit_review(cue_id: str, grade: int) -> dict[str, Any]:
    """cue 自评 1-4 → SM-2 更新（<3 重置周期）+ 写 ReviewRecord。"""
    return review.submit_review(cue_id, grade)


@mcp.tool()
def get_statistics(group_by: str) -> dict[str, Any]:
    """聚合统计（subject/knowledge_point/date/mastery）。"""
    return statistics.get_statistics(group_by)


@mcp.tool()
def export_data(format: str = "json", filters: dict[str, Any] | None = None) -> dict[str, Any]:
    """导出 json / markdown 到 data/exports/。"""
    return export.export_data(format, filters)


@mcp.tool()
def generate_quiz(cue_id: str, quiz_type: str = "") -> dict[str, Any]:
    """为 cue 渲染命题 prompt 并生成占位 quiz 落盘（宿主 LLM 生成后经 save_quiz 回写）。"""
    return quiz.generate_quiz(cue_id, quiz_type)


@mcp.tool()
def save_quiz(quiz_id: str, quiz_data: dict[str, Any]) -> dict[str, Any]:
    """题干/选项/答案经 pydantic 校验写回 quiz（选择题校验 answer ∈ options）。"""
    return quiz.save_quiz(quiz_id, quiz_data)


@mcp.tool()
def grade_quiz(quiz_id: str, response: str) -> dict[str, Any]:
    """判分并更新 SM-2：选择精确匹配（4/1）；填空返回 grade_prompt 语义评分（默认 3）。"""
    return quiz.grade_quiz(quiz_id, response)


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
