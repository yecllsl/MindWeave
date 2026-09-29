#!/usr/bin/env bash
# 将 mindweave.plugin/ (配置真相源 + Agent Plugins 1.0 插件包) 单向同步到 Tier 2 原生 harness 项目目录:
#   .trae/  .opencode/
#
# 注：CodeBuddy 与 VS Code 走 Tier 1 插件通道（mindweave.plugin/ 即 Agent Plugins 1.0 包，
#      经 .codebuddy-plugin/marketplace.json 本地市场安装），不再生成 .codebuddy/ 原生目录。
#
# 用法:
#   ./scripts/sync-agent-configs.sh                 # 同步全部 (Tier 2: .trae + .opencode)
#   ./scripts/sync-agent-configs.sh --skip-trae     # 跳过 Trae
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

PLUGIN_DIR="$PROJECT_ROOT/mindweave.plugin"
PLUGIN_RUNTIME="$PLUGIN_DIR/runtime"
PLUGIN_SKILLS="$PLUGIN_DIR/skills"
PLUGIN_MD="$PLUGIN_DIR/AGENTS.md"
MCP_DIR="$PLUGIN_DIR/mindweave-mcp"

[ -d "$PLUGIN_RUNTIME" ] || { echo "错误: 运行时配置目录不存在: $PLUGIN_RUNTIME"; exit 1; }
[ -d "$PLUGIN_SKILLS" ] || { echo "错误: 技能目录不存在: $PLUGIN_SKILLS"; exit 1; }
[ -f "$PLUGIN_MD" ] || { echo "错误: AGENTS.md 不存在: $PLUGIN_MD"; exit 1; }

if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; RED='\033[0;31m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; CYAN=''; RED=''; NC=''
fi

echo -e "${CYAN}=== MindWeave AAIF Config Sync ===${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo "配置源: mindweave.plugin/ (AAIF 标准 + Agent Plugins 1.0)"

SKIP_TRAE=false
SKIP_OPENCODE=false
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-trae) SKIP_TRAE=true; shift ;;
        --skip-opencode) SKIP_OPENCODE=true; shift ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

sync_skills() {
    local target_dir="$1"
    local target_skills="$target_dir/skills"
    mkdir -p "$target_dir"
    rm -rf "$target_skills"
    echo -e "${YELLOW}同步 Skills → $target_skills${NC}"
    cp -r "$PLUGIN_SKILLS" "$target_skills"
    local skill_count
    skill_count=$(find "$target_skills" -mindepth 1 -maxdepth 1 -type d | wc -l)
    echo -e "${GREEN}  已同步 $skill_count 个 Skills${NC}"
}

sync_agents_md() {
    local target_dir="$1"
    local target_agents_md="$target_dir/AGENTS.md"
    echo -e "${YELLOW}同步 AGENTS.md → $target_agents_md${NC}"
    cp -f "$PLUGIN_MD" "$target_agents_md"
    echo -e "${GREEN}  已同步 AGENTS.md${NC}"
}

generate_trae_config() {
    local trae_dir="$PROJECT_ROOT/.trae"
    mkdir -p "$trae_dir"
    local source_config="$PLUGIN_RUNTIME/trae.json"
    if [ -f "$source_config" ]; then
        echo -e "${YELLOW}复制 Trae 配置 → .trae/${NC}"
        cp -f "$source_config" "$trae_dir/mcp.json"
        echo -e "${GREEN}  已生成 Trae 配置${NC}"
    fi
}

generate_opencode_config() {
    local opencode_dir="$PROJECT_ROOT/.opencode"
    mkdir -p "$opencode_dir"
    local source_config="$PLUGIN_RUNTIME/opencode.json"
    if [ -f "$source_config" ]; then
        echo -e "${YELLOW}复制 opencode 配置 → .opencode/${NC}"
        cp -f "$source_config" "$opencode_dir/opencode.json"
        echo -e "${GREEN}  已生成 opencode 配置${NC}"
    fi
}

generate_aaif_declarations() {
    if ! command -v uv >/dev/null 2>&1; then
        echo -e "${RED}未找到 uv，无法生成 AAIF 声明文件 (tools.json/triggers.json/workflows.json)${NC}" >&2
        exit 1
    fi
    local decl_script="$SCRIPT_DIR/generate-aaif-declarations.py"
    echo -e "${YELLOW}生成 AAIF 声明文件 → mindweave.plugin/${NC}"
    uv run --no-sync --directory "$MCP_DIR" python "$decl_script"
    if [ $? -ne 0 ]; then
        echo -e "${RED}AAIF 声明文件生成失败${NC}" >&2
        exit 1
    fi
    echo -e "${GREEN}  已生成 tools.json / triggers.json / workflows.json${NC}"
}

generate_aaif_declarations

if [ "$SKIP_TRAE" = false ]; then
    echo -e "\n${CYAN}--- Trae ---${NC}"
    sync_skills "$PROJECT_ROOT/.trae"
    sync_agents_md "$PROJECT_ROOT"
    generate_trae_config
fi
if [ "$SKIP_OPENCODE" = false ]; then
    echo -e "\n${CYAN}--- opencode ---${NC}"
    sync_skills "$PROJECT_ROOT/.opencode"
    sync_agents_md "$PROJECT_ROOT/.opencode"
    generate_opencode_config
fi

echo -e "\n${CYAN}=== 同步完成 ===${NC}"
