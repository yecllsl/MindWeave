# MindWeave - K12 康奈尔 AI 智能笔记 Agent Plugin（skills + MCP 一体）

K12 康奈尔 AI 智能笔记一体化解决方案，支持 **Trae IDE CN / Trae Work CN**、**CodeBuddy**、**OpenCode**（goose 保留但未默认支持）。核心流程：拍照/文字录入 → 宿主 LLM 整理为康奈尔笔记（线索栏/笔记栏/总结栏）→ 用户确认保存 → 线索栏问题即知识卡 → 基于 SM-2 遗忘曲线的复习排程 → 到期遮挡回忆自评（1-4 档）→ 统计/导出。

设计理念：康奈尔笔记法的**线索栏（Cue Column）天然就是复习卡的正面**——「整理笔记」与「生成复习卡」是同一动作，无需两套实体流程（RemNote 模式，笔记即学习材料闭环）。

项目以 **Agent Plugins 1.0**（Vercel 等厂商中立打包规范，与 AAIF 无隶属关系）规范打包：`mindweave.plugin/` 即为插件根，含 `plugin.json`（manifest）、`mcp.json`（MCP 启动配置）与 `skills/`（5 个 Skill），可作为标准 Agent Plugin 分发到任意兼容客户端；各 harness 原生目录（`.trae/` 等）仍由 `scripts/sync-agent-configs` 单向生成，互不冲突。

## 核心功能

- 📷 **三模式采集**: 对话多模态 / 本地图片路径 / 文本录入，宿主 LLM 整理为康奈尔三栏结构
- 🗂️ **康奈尔结构化**: 线索栏（cues，即知识卡）/ 笔记栏（body）/ 总结栏（summary）
- 🧠 **智能存储**: 笔记本地保存，cue 内嵌 SM-2 记忆状态（reps / EF / interval / next_review）
- 📅 **复习排程**: SM-2 遗忘曲线算法，到期 cue 队列（每日上限 10 卡）
- ✅ **遮挡回忆自评**: 线索问题 → 用户回忆 → 揭示答案 → 自评 1-4，自动更新 SM-2 参数
- 🎯 **AI 出题测验**（`/quiz`）: 从知识卡生成选择/填空题 → 用户作答 → 判分（出题即复习，与自评等价推动 SM-2）
- 🖥️ **Web 可视化**（`mindweave-web`）: 本地人工处理面——概览 / 笔记浏览+编辑+删除（修正 LLM 整理结果）/ 自评复习 / 统计（ECharts），默认 127.0.0.1:8003
- 📊 **统计分析**: 按学科/知识点/日期/掌握度四维度聚合
- 📤 **数据导出**: JSON / Markdown 格式导出笔记

## 系统架构

```
用户交互层
├── 对话式交互 (命令 / 自然语言)
├── 四运行时: Trae + CodeBuddy + OpenCode（goose 保留未默认支持）
    ↓
Skills 编排层 (mindweave.plugin/skills/mindweave-*: capture / review / quiz / stats / export)
    ↓
MCP Tools 层 (mindweave.plugin/mindweave-mcp)
├── organize → save/get/query/update/delete → schedule/submit → statistics → export
├── + quiz 工具链: generate_quiz → save_quiz → grade_quiz（仅对话链路）
├── Web 层 (mindweave_mcp/web): FastAPI + Jinja2 + HTMX + ECharts（本地人工处理面，无出题路由）
    ↓
Rules 约束层 (mindweave.plugin/AGENTS.md — 统一规则源)
    ↓
数据存储层 (本地 JSON 文件，原子写入: data/notes/ reviews/ exports/ images/ quizzes/)
```

## 技术栈

- **MCP Server**: Python 3.12+ / FastMCP / Pydantic v2
- **复习算法**: SM-2 间隔重复（自实现，移植 VocabCraft 已验证实现，零额外依赖）
- **图片解析**: 宿主 LLM 多模态能力直接看图解析（MCP 侧零图像处理代码）
- **数据存储**: JSON 文件（本地存储，原子写入）
- **包管理**: uv
- **测试**: pytest + pytest-asyncio + pytest-cov

## 快速开始

### 前置要求

- Python 3.12+
- [uv 包管理器](https://docs.astral.sh/uv/)（Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`）
- Trae IDE CN / Trae Work CN、CodeBuddy 或 OpenCode（任选其一）

### 安装（同步配置 + 生成声明）

```powershell
# Windows
.\scripts\sync-agent-configs.ps1
```

```bash
# Linux / macOS
bash scripts/sync-agent-configs.sh
```

### 配置 Agent Runtime

##### Trae

1. 用 Trae IDE CN 或 Trae Work CN 打开项目文件夹
2. 进入 **设置 → MCP**，打开 **"启用项目级 MCP"** 开关
3. 进入 **设置 → 规则**，开启 **"将 AGENTS.md 包含在上下文中"**
4. 重启 Trae

> 💡 项目级 MCP 配置已内置于 `.trae/mcp.json`（由 `mindweave.plugin/runtime/trae.json` 经 `scripts/sync-agent-configs` 同步生成），使用 `${workspaceFolder}` 变量自动适配路径。

##### CodeBuddy / OpenCode

1. 运行同步脚本生成 `.codebuddy/` / `.opencode/` 投影
2. 用 CodeBuddy / OpenCode 打开项目文件夹，信任 mindweave-mcp

### 开始使用

```
/capture  - 录入笔记（拍照/文字 → 康奈尔整理）
/review   - 复习到期知识卡（SM-2 排程·自评）
/quiz     - 出题测验（选择/填空，出题即复习）
/stats    - 查看笔记统计
/export   - 导出笔记数据
```

自然语言：录笔记 / 该复习了 / 考我 / 笔记统计 / 导出笔记 亦可触发。

### Web 可视化（可选）

```bash
cd mindweave.plugin/mindweave-mcp && uv run mindweave-web
# 浏览器打开 http://127.0.0.1:8003（本机绑定；可用 MINDWEAVE_WEB_HOST/PORT 覆盖）
```

提供概览 / 笔记列表+详情 / 笔记人工处理（编辑+删除，修正 LLM 整理结果）/ 自评复习 / 统计五个页面。

## 项目结构

```
MindWeave/
├── AGENTS.md                             # 仓库级说明（规则层，与 mindweave.plugin/AGENTS.md 同步）
├── package.json                          # agents publish 入口
├── scripts/                              # sync-agent-configs(.ps1/.sh) + generate-aaif-declarations.py + pre-commit
├── README.md / CHANGELOG.md / LICENSE
├── mindweave.plugin/                     # Agent Plugin 根目录（单一配置与打包真相源）
│   ├── plugin.json / mcp.json            # Agent Plugins 1.0 manifest + MCP 启动配置
│   ├── AGENTS.md                         # 统一规则源（只改这里）
│   ├── tools.json / triggers.json / workflows.json   # AAIF 声明（脚本生成，勿手改）
│   ├── .codebuddy-plugin/plugin.json     # CodeBuddy CLI 插件身份
│   ├── runtime/{trae,codebuddy,opencode,goose}.json  # 各平台 MCP 运行时配置源
│   ├── skills/                           # 5 个 Skill（同步到 .trae/.opencode/.codebuddy）
│   └── mindweave-mcp/                    # MCP Server 服务层（Python，内联自包含）
│       ├── src/mindweave_mcp/            # server.py / models.py / algorithms.py / storage.py / prompts/ / tools/ / web/
│       ├── tests/                        # 测试套件
│       ├── data/                         # 运行时数据（被 .gitignore，保留 .gitkeep）
│       └── pyproject.toml                # 入口 mindweave-mcp / mindweave-web
├── .trae/ .opencode/ .codebuddy/         # 各平台配置（scripts/sync-agent-configs 生成）
└── docs/                                 # 设计文档 / 计划 / 评审（本地文档，不入库追踪）
```

## 架构设计说明

本项目采用 **"服务层 + 配置层 + 规则层"** 分离架构：

| 层级 | 位置 | 用途 |
|------|------|------|
| **服务层** | `mindweave.plugin/mindweave-mcp/` | 纯 Python MCP Server，通用，不绑定任何客户端，可独立发布；内联于插件目录，使插件完全自包含 |
| **配置层** | `mindweave.plugin/` | AAIF 唯一真相源，定义 Skills 流程与约束（单一真相源），同步生成 `.trae/` 等各平台目录 |
| **规则层** | `mindweave.plugin/AGENTS.md` | 业务规则（采集/复习/交互/数据安全）+ 开发规范 |

`mindweave.plugin/AGENTS.md` 是各运行时共用的统一规则源，保证行为一致。修改配置的正确流程：改 `mindweave.plugin/` → 跑 `scripts/sync-agent-configs.ps1`（或 `.sh`）→ 各生成目录改动一起提交（详见 AGENTS.md「流程规则 > 配置同步」）。

## Sage 集成

MindWeave 是 Sage 学习三支柱中的第三域（课堂/知识点笔记）。Sage 侧通过 `MindWeaveReader` 只读聚合 `data/notes/*.json`（cues 展平为 due items，due 来源 `cue.review_state.next_review`），`sync_from_plugins` 后可在 `get_profile` 出现 mindweave 域；`.trae/skills/` 投影使 TraeCode `list skills` 可见三插件共 15 技能（deep-review 5 + vocabcraft 5 + mindweave 5）。

## 数据安全

- ✅ 所有数据仅存储在本地
- ✅ 不收集任何个人身份信息
- ✅ 图片文件存储在项目 `data/images/` 目录下，不外传
- ✅ 导出数据前需用户确认

## 测试与开发

```bash
cd mindweave.plugin/mindweave-mcp

# 单元测试
uv sync --extra dev
uv run pytest -q

# 静态检查
uv run ruff check src tests
uv run mypy src

# 重新生成 AAIF 声明（tools/triggers/workflows.json）
uv run --no-sync --directory mindweave.plugin/mindweave-mcp python ../../scripts/generate-aaif-declarations.py
```

## License

MIT License
