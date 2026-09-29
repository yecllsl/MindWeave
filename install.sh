#!/bin/bash
# MindWeave MCP Server 安装脚本
# 适用于 Linux / macOS
#
# 使用方法：
#   chmod +x install.sh
#   ./install.sh
#
# 可选参数：
#   --fix-path                将 mindweave.plugin/runtime 中 ${workspaceFolder} 替换为绝对路径（并重新同步各平台目录）
#   --agent-runtime <name>    配置 Agent 运行时 (vscode/trae/codebuddy/opencode/all)
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

set -e

# ──────────────────────────────────────────
# 参数解析
# ──────────────────────────────────────────
FIX_PATH=false
AGENT_RUNTIME=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix-path) FIX_PATH=true; shift ;;
        --agent-runtime)
            if [[ -z "$2" ]]; then echo "错误: --agent-runtime 需要一个值"; exit 1; fi
            AGENT_RUNTIME="$2"; shift 2 ;;
        *) echo "未知参数: $1"; echo "用法: ./install.sh [--fix-path] [--agent-runtime trae|codebuddy|opencode|all]"; exit 1 ;;
    esac
done

# 校验 AgentRuntime 值
case "$AGENT_RUNTIME" in
    ""|vscode|trae|codebuddy|opencode|all) ;;
    *) echo "错误: --agent-runtime 仅支持 trae/codebuddy/opencode/all"; exit 1 ;;
esac

# 颜色输出（非 TTY 时禁用）
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; GRAY='\033[1;30m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; CYAN=''; RED=''; GRAY=''; NC=''
fi

echo ""
echo "========================================"
echo "  MindWeave v0.3.2 安装向导"
echo "  (VS Code / CodeBuddy 走插件通道 · Trae / opencode 走原生目录)"
echo "========================================"
echo ""

# 获取脚本所在目录（项目根目录）
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ──────────────────────────────────────────
# [1/5] 检查 uv 包管理器
# ──────────────────────────────────────────
echo "[1/5] 检查 uv 包管理器..."
if ! command -v uv &> /dev/null; then
    echo -e "  ${RED}✗ uv 未安装${NC}"
    echo ""
    echo "  请先安装 uv："
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  或访问 https://docs.astral.sh/uv/getting-started/install/"
    exit 1
fi
echo -e "  ${GREEN}✓ uv 已安装 ($(uv --version))${NC}"

# ──────────────────────────────────────────
# [2/5] 检查 Python 版本
# ──────────────────────────────────────────
echo "[2/5] 检查 Python 版本 (>=3.12)..."
if ! command -v python3 &> /dev/null; then
    echo -e "  ${RED}✗ Python 未安装${NC}"
    echo ""
    echo "  请先安装 Python 3.12+："
    echo "  https://www.python.org/downloads/"
    exit 1
fi
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 12 ]); then
    echo -e "  ${RED}✗ Python 版本过低: $PYTHON_VERSION (需要 >= 3.12)${NC}"
    echo ""
    echo "  请升级 Python: https://www.python.org/downloads/"
    exit 1
fi
echo -e "  ${GREEN}✓ Python $PYTHON_VERSION${NC}"

# ──────────────────────────────────────────
# [3/4] 安装依赖
# ──────────────────────────────────────────
MCP_DIR="$PROJECT_ROOT/mindweave.plugin/mindweave-mcp"

echo "[3/4] 安装依赖..."

cd "$MCP_DIR"

echo "  正在安装依赖包..."
if ! uv sync 2>&1; then
    echo -e "  ${RED}✗ 依赖安装失败${NC}"
    echo ""
    echo "  请尝试手动安装："
    echo "  cd mindweave.plugin/mindweave-mcp"
    echo "  uv sync"
    exit 1
fi
echo -e "  ${GREEN}✓ 基础依赖安装完成${NC}"

# ──────────────────────────────────────────
# [4/4] Agent Runtime 配置（多 harness）
# ──────────────────────────────────────────
SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync-agent-configs.sh"

if [ -n "$AGENT_RUNTIME" ]; then
    echo ""
    echo -e "${CYAN}=== Agent Runtime 配置 ===${NC}"

    case "$AGENT_RUNTIME" in
        "vscode")
            echo -e "  ${YELLOW}VS Code 配置说明 (Tier 1 · Agent Plugins 1.0):${NC}"
            echo "  1. 用 VS Code 打开项目文件夹"
            echo "  2. 在 Agent 面板添加本地 Agent Plugin，指向目录: mindweave.plugin/"
            echo "     (含 plugin.json + mcp.json + skills/，即 Agent Plugins 1.0 包)"
            ;;
        "codebuddy")
            echo -e "  ${YELLOW}CodeBuddy 配置说明 (Tier 1 · 本地插件市场):${NC}"
            echo "  1. 用 CodeBuddy 打开项目文件夹"
            echo "  2. 在对话框执行: /plugin marketplace add $PROJECT_ROOT"
            echo "     (该目录含 .codebuddy-plugin/marketplace.json，source 指向 ./mindweave.plugin)"
            echo "  3. 执行: /plugin install mindweave@mindweave-local-market"
            echo "  4. 必要时执行: /reload-plugins"
            ;;
        "trae")
            echo -e "  ${YELLOW}正在同步 Trae 配置 (Tier 2 原生目录)...${NC}"
            if [ -f "$SYNC_SCRIPT" ]; then
                bash "$SYNC_SCRIPT" --skip-opencode
                echo ""
                echo -e "  ${YELLOW}下一步:${NC}"
                echo "  1. 用 Trae 打开项目文件夹"
                echo "  2. 设置 > MCP > 启用「项目级 MCP」"
                echo "  3. 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
            else
                echo -e "  ${RED}  同步脚本不存在: $SYNC_SCRIPT${NC}"
            fi
            ;;
        "opencode")
            echo -e "  ${YELLOW}正在同步 opencode 配置 (Tier 2 原生目录)...${NC}"
            if [ -f "$SYNC_SCRIPT" ]; then
                bash "$SYNC_SCRIPT" --skip-trae
                echo ""
                echo -e "  ${YELLOW}下一步:${NC}"
                echo "  1. 在项目目录运行 opencode"
                echo "  2. AGENTS.md 将自动加载"
            else
                echo -e "  ${RED}  同步脚本不存在: $SYNC_SCRIPT${NC}"
            fi
            ;;
        "all")
            echo -e "  ${YELLOW}正在同步 Tier 2 配置 (Trae + opencode)...${NC}"
            if [ -f "$SYNC_SCRIPT" ]; then
                bash "$SYNC_SCRIPT"
                echo ""
                echo -e "  ${GREEN}Tier 2 配置已同步。各运行时下一步:${NC}"
                echo "  Trae: 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
                echo "  opencode: 在项目目录运行 opencode"
                echo ""
                echo -e "  ${YELLOW}Tier 1 (VS Code / CodeBuddy) 请手动安装插件:${NC}"
                echo "  VS Code:   添加本地 Agent Plugin → mindweave.plugin/"
                echo "  CodeBuddy: /plugin marketplace add $PROJECT_ROOT → /plugin install mindweave@mindweave-local-market"
            else
                echo -e "  ${RED}  同步脚本不存在: $SYNC_SCRIPT${NC}"
            fi
            ;;
    esac
fi

cd "$PROJECT_ROOT"

# ──────────────────────────────────────────
# 验证安装
# ──────────────────────────────────────────
echo -e "${YELLOW}[验证] 验证安装...${NC}"

cd "$MCP_DIR"
# 验证 MCP Server 入口点可用
if uv run mindweave-mcp --help &> /dev/null; then
    echo -e "  ${GREEN}✓ MCP Server 入口点可用${NC}"
else
    echo -e "  ${YELLOW}  ⚠ MCP Server 验证跳过（入口点可能需要交互模式）${NC}"
fi

# 验证 Web 入口点可用
if uv run python -c "from mindweave_mcp.web.app import create_app; print('OK')" 2>&1 | grep -q "OK"; then
    echo -e "  ${GREEN}✓ Web 可视化模块可用${NC}"
else
    echo -e "  ${YELLOW}  ⚠ Web 可视化模块验证跳过${NC}"
fi
cd "$PROJECT_ROOT"

# ──────────────────────────────────────────
# mcp.json 路径回退方案（多运行时共用，AAIF 真相源 mindweave.plugin/runtime）
# ──────────────────────────────────────────
RUNTIME_DIR="$PROJECT_ROOT/mindweave.plugin/runtime"
TRAE_JSON="$RUNTIME_DIR/trae.json"
if [ -f "$TRAE_JSON" ]; then
    if grep -q '${workspaceFolder}' "$TRAE_JSON" 2>/dev/null; then
        echo ""
        echo -e "  ${CYAN}ℹ 检测到 runtime 配置使用了 \${workspaceFolder} 变量${NC}"
        echo "    Trae 会自动替换此变量，无需手动配置"
        echo "    如果你的环境不支持变量替换，请运行："
        echo "    ./install.sh --fix-path"
    fi
fi

# 处理 --fix-path 参数：将 mindweave.plugin/runtime 中 ${workspaceFolder} 替换为实际路径
if [ "$FIX_PATH" = true ]; then
    echo ""
    echo "  正在修复 runtime 配置路径（mindweave.plugin/runtime）..."
    FIXED_ANY=false
    for f in trae.json; do
        T="$RUNTIME_DIR/$f"
        if [ -f "$T" ]; then
            if grep -q '\${workspaceFolder}' "$T" 2>/dev/null; then
                ESCAPED_ROOT="${PROJECT_ROOT//\//\\/}"
                sed -i.bak "s/\${workspaceFolder}/$ESCAPED_ROOT/g" "$T"
                rm -f "$T.bak"
                echo -e "  ${GREEN}✓ 已修复: $T${NC}"
                FIXED_ANY=true
            else
                echo -e "  ${GRAY}ℹ 无需修复（无变量）: $T${NC}"
            fi
        else
            echo -e "  ${RED}✗ 未找到 $T${NC}"
        fi
    done
    if [ "$FIXED_ANY" = true ] && [ -f "$SYNC_SCRIPT" ]; then
        echo "  重新同步到各平台目录..."
        bash "$SYNC_SCRIPT"
    fi
    echo -e "  ${YELLOW}⚠ 注意：修复后配置仅对当前路径有效，移动项目后需重新运行 --fix-path${NC}"
    echo -e "  ${YELLOW}⚠ 注意：多运行时可移植性会降低，建议优先升级运行时版本以支持变量${NC}"
fi

# ──────────────────────────────────────────
# 安装 git pre-commit 钩子（配置同步机械防线）
# ──────────────────────────────────────────
echo "安装 git pre-commit 钩子..."
HOOK_SRC="$PROJECT_ROOT/scripts/pre-commit"
HOOK_DST="$PROJECT_ROOT/.git/hooks/pre-commit"
if [ -f "$HOOK_SRC" ]; then
    mkdir -p "$PROJECT_ROOT/.git/hooks"
    cp -f "$HOOK_SRC" "$HOOK_DST"
    chmod +x "$HOOK_DST"
    echo -e "  ${GREEN}✓ 已安装 pre-commit 钩子（拦截直接修改生成目录 .trae/.opencode 的违规提交）${NC}"
    echo -e "  ${GRAY}    若需手动安装：cp scripts/pre-commit .git/hooks/pre-commit${NC}"
else
    echo -e "  ${YELLOW}⚠ 未找到 $HOOK_SRC，跳过钩子安装${NC}"
fi

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
echo ""
echo "========================================"
echo -e "  ${GREEN}✓ 安装完成！${NC}"
echo "========================================"
echo ""
echo "下一步操作（按所用运行时选择对应通道）："
echo ""
echo "  1. 用对应运行时打开此文件夹"
echo "     文件 → 打开文件夹 → 选择: $PROJECT_ROOT"
echo ""
echo "  2. 启用项目级 MCP（Trae: 设置 → MCP；CodeBuddy: 信任 mindweave-mcp）"
echo ""
echo "  3. 重启运行时"
echo ""
echo "  4. 开始使用！"
echo "     /capture       - 采集错题（拍照/文本）"
echo "     /batch-capture - 批量采集错题"
echo "     /analyze       - 分析错题原因"
echo "     /review        - 生成复习计划"
echo "     /stats         - 查看错题统计"
echo ""
echo "  可选：启动 Web 可视化界面"
echo "     cd mindweave.plugin/mindweave-mcp && uv run mindweave-web"
echo "     浏览器访问 http://127.0.0.1:8003"
echo ""
