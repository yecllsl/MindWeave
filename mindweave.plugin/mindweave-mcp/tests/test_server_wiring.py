"""server.py 工具注册 wiring 测试。"""
import asyncio

from mindweave_mcp import server


def test_all_ten_tools_registered():
    names = {t.name for t in asyncio.run(server.mcp.list_tools())}
    expected = {"organize_note", "save_note", "get_note", "query_notes",
                "update_note", "delete_note", "schedule_review", "submit_review",
                "get_statistics", "export_data"}
    assert names == expected


def test_registered_tool_end_to_end_call():
    # 穿透调用冒烟（评审 S4）：注册的工具函数须真实可调，且透传到底层 tools 实现。
    # 用 organize_note()（无参 → dialog 模式）验证——不触碰数据目录，无副作用。
    r = server.organize_note()
    assert r["mode"] == "dialog" and "parse_prompt" in r
