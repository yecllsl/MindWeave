# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2026-08-30

### 首个版本：K12 康奈尔 AI 智能笔记 Agent Plugin

- **服务层**（`mindweave.plugin/mindweave-mcp/`）：Python 3.12+ / FastMCP / Pydantic v2 的标准 MCP server，10 个工具（`organize_note` / `save_note` / `get_note` / `query_notes` / `update_note` / `delete_note` / `schedule_review` / `submit_review` / `get_statistics` / `export_data`）；数据模型（NoteRecord/Cue/Cornell/ReviewState/ReviewRecord）；SM-2 算法（移植 VocabCraft 已验证实现，语义一致、代码独立）；JSON 原子写存储。
- **插件层**（`mindweave.plugin/`）：Agent Plugins 1.0 包（plugin.json / mcp.json）+ 4 个 Skill（capture / review / stats / export）+ 4 份 runtime 配置 + CodeBuddy CLI 身份；AAIF 声明文件（tools/triggers/workflows.json）由 `scripts/generate-aaif-declarations.py` 从真实源自省生成；`scripts/sync-agent-configs` 单向投影到 `.trae/` / `.opencode/` / `.codebuddy/`。
- **仓库级文档**：AGENTS.md（规则层：采集三模式 / cue≥1 / question 变更重置 / 每日 10 卡 / Prompt 防御 / 数据安全）、README.md、本 CHANGELOG、MIT LICENSE。
