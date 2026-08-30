# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-08-30

### 新增
- **AI 出题测验（对话链路）**：`generate_quiz` / `save_quiz` / `grade_quiz` 三工具，选择/填空题型；出题即复习（判分与自评共享 `apply_review` SM-2 更新路径，ReviewRecord 新增 `source` 字段区分 self/quiz 口径）。
- **`mindweave-quiz` skill**（`/quiz` 命令，触发词：出题/考我/练一练/测验）。
- **Web 可视化人工处理面**（`mindweave-web`，FastAPI + Jinja2 + HTMX/Alpine + ECharts）：概览 / 笔记列表+详情 / 笔记编辑+删除（修正 LLM 整理结果，question 变更重置复习状态）/ 自评复习 / 统计五页面；默认本机绑定 127.0.0.1:8003。

### 安全
- quiz 判分三道硬防御：空作答拒绝、占位题（answer 空）拒绝、已判分 quiz 拒绝二次评分。
- `save_quiz` 经 `QuizRecord` pydantic 重建校验（选择题 answer ∈ options），禁止宿主直写 quizzes 文件；`data/quizzes/` 不入 Git。

## [0.1.0] - 2026-08-30

### 首个版本：K12 康奈尔 AI 智能笔记 Agent Plugin

- **服务层**（`mindweave.plugin/mindweave-mcp/`）：Python 3.12+ / FastMCP / Pydantic v2 的标准 MCP server，10 个工具（`organize_note` / `save_note` / `get_note` / `query_notes` / `update_note` / `delete_note` / `schedule_review` / `submit_review` / `get_statistics` / `export_data`）；数据模型（NoteRecord/Cue/Cornell/ReviewState/ReviewRecord）；SM-2 算法（移植 VocabCraft 已验证实现，语义一致、代码独立）；JSON 原子写存储。
- **插件层**（`mindweave.plugin/`）：Agent Plugins 1.0 包（plugin.json / mcp.json）+ 4 个 Skill（capture / review / stats / export）+ 4 份 runtime 配置 + CodeBuddy CLI 身份；AAIF 声明文件（tools/triggers/workflows.json）由 `scripts/generate-aaif-declarations.py` 从真实源自省生成；`scripts/sync-agent-configs` 单向投影到 `.trae/` / `.opencode/` / `.codebuddy/`。
- **仓库级文档**：AGENTS.md（规则层：采集三模式 / cue≥1 / question 变更重置 / 每日 10 卡 / Prompt 防御 / 数据安全）、README.md、本 CHANGELOG、MIT LICENSE。
