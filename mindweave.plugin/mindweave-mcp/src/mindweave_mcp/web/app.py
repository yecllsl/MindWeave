"""MindWeave web 应用工厂与启动入口。

web 是人工处理面（浏览/编辑/删除/自评复习/统计），无出题路由（spec §0 决策）；
services 直调 tools 层函数，不经 MCP 协议、无 LLM 依赖。
绑定地址 MINDWEAVE_WEB_HOST 默认 127.0.0.1（有意比 VocabCraft 0.0.0.0 更保守），
端口 MINDWEAVE_WEB_PORT 默认 8003（避开 VocabCraft 8002）。
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

_WEB_DIR = Path(__file__).parent
_TEMPLATES_DIR = _WEB_DIR / "templates"
_STATIC_DIR = _WEB_DIR / "static"

templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))


def create_app() -> FastAPI:
    """创建 FastAPI 应用：挂载静态文件、注册四组路由。"""
    app = FastAPI(
        title="MindWeave 可视化",
        description="K12 康奈尔笔记本地人工处理面（浏览/编辑/删除/自评复习/统计）",
        version="0.2.0",
    )
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    from mindweave_mcp.web.routes import dashboard, notes, review, stats

    app.include_router(dashboard.router)
    app.include_router(notes.router)
    app.include_router(review.router)
    app.include_router(stats.router)
    return app


def main() -> None:
    """CLI 入口：启动 uvicorn（默认 127.0.0.1:8003，本机绑定）。"""
    import uvicorn

    host = os.environ.get("MINDWEAVE_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("MINDWEAVE_WEB_PORT", "8003"))
    uvicorn.run("mindweave_mcp.web.app:create_app", factory=True,
                host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
