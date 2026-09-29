#!/usr/bin/env bash
# MindWeave 发布包构建脚本（bash 版）
# 与 scripts/build-release.ps1 逻辑对齐，供 GitHub Actions 和 Linux/macOS 用户使用
#
# 使用方法：
#   ./scripts/build-release.sh [VERSION]
#
# 输出：
#   dist/MindWeave-v${VERSION}.zip
#   dist/MindWeave-v${VERSION}.tar.zst
#   dist/MindWeave-v${VERSION}.tar.gz

set -euo pipefail

VERSION="${1:-0.3.2}"

# ──────────────────────────────────────────
# 路径定义
# ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$PROJECT_ROOT/dist"
PACKAGE_NAME="MindWeave-v$VERSION"
STAGING_DIR="$DIST_DIR/$PACKAGE_NAME"
ZIP_PATH="$DIST_DIR/$PACKAGE_NAME.zip"
ZST_PATH="$DIST_DIR/$PACKAGE_NAME.tar.zst"
GZ_PATH="$DIST_DIR/$PACKAGE_NAME.tar.gz"

# ──────────────────────────────────────────
# 颜色输出（与 PowerShell 版风格一致）
# ──────────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; RED=''; CYAN=''; NC=''
fi
log_step() { echo -e "${YELLOW}[build]${NC} $1"; }
log_ok()   { echo -e "${GREEN}[ok]${NC}    $1"; }
log_err()  { echo -e "${RED}[err]${NC}   $1" >&2; }

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  MindWeave v$VERSION release build${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# ──────────────────────────────────────────
# [1/6] 清理旧构建
# ──────────────────────────────────────────
log_step "[1/6] Clean previous build..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
log_ok "cleaned"

# ──────────────────────────────────────────
# [2/6] 创建目标目录结构
# ──────────────────────────────────────────
log_step "[2/6] Create directory structure..."
mkdir -p "$STAGING_DIR/.trae/skills"
mkdir -p "$STAGING_DIR/mindweave.plugin/skills"
mkdir -p "$STAGING_DIR/mindweave.plugin/runtime"
mkdir -p "$STAGING_DIR/.opencode/skills"
# CodeBuddy 插件清单目录（Tier 1 市场通道）：插件根内 .codebuddy-plugin/ + 根级 .codebuddy-plugin/
mkdir -p "$STAGING_DIR/mindweave.plugin/.codebuddy-plugin"
mkdir -p "$STAGING_DIR/.codebuddy-plugin"
mkdir -p "$STAGING_DIR/scripts"
mkdir -p "$STAGING_DIR/mindweave.plugin/mindweave-mcp/src"
mkdir -p "$STAGING_DIR/mindweave.plugin/mindweave-mcp/data/notes"
mkdir -p "$STAGING_DIR/mindweave.plugin/mindweave-mcp/data/reviews"
mkdir -p "$STAGING_DIR/mindweave.plugin/mindweave-mcp/data/images"
mkdir -p "$STAGING_DIR/mindweave.plugin/mindweave-mcp/data/quizzes"
mkdir -p "$STAGING_DIR/mindweave.plugin/mindweave-mcp/data/exports"
log_ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 .trae 配置（白名单）
# ──────────────────────────────────────────
log_step "[3/6] Copy .trae config..."

# .trae 顶层文件
[ -f "$PROJECT_ROOT/.trae/hooks.json" ] && \
    cp "$PROJECT_ROOT/.trae/hooks.json" "$STAGING_DIR/.trae/hooks.json"

# 写入发布版 mcp.json（使用 ${workspaceFolder} 变量，解压到任意位置均可工作）
# 注意：源 .trae/mcp.json 可能包含硬编码绝对路径，发布包必须用变量版本。
cat > "$STAGING_DIR/.trae/mcp.json" <<'EOF'
{
  "mcpServers": {
    "mindweave-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--no-sync",
        "--directory",
        "${workspaceFolder}/mindweave.plugin/mindweave-mcp",
        "mindweave-mcp"
      ]
    }
  }
}
EOF

# .trae/skills/ 每个 skill 目录（递归复制，排除 __pycache__）
# 用 cd + 相对路径的 find，避免 Git Bash 在 Windows 上路径混用导致复制到奇怪的 mnt/d/... 子目录
if [ -d "$PROJECT_ROOT/.trae/skills" ]; then
    for skill_dir in "$PROJECT_ROOT/.trae/skills"/*/; do
        [ -d "$skill_dir" ] || continue
        skill_name="$(basename "$skill_dir")"
        skill_dst="$STAGING_DIR/.trae/skills/$skill_name"
        mkdir -p "$skill_dst"
        (
            cd "$skill_dir"
            find . -mindepth 1 -type f ! -path '*/__pycache__/*' -print0
        ) | while IFS= read -r -d '' rel; do
            # rel 以 "./" 开头，去掉它
            rel="${rel#./}"
            dst="$skill_dst/$rel"
            mkdir -p "$(dirname "$dst")"
            cp "$skill_dir/$rel" "$dst"
        done
    done
fi
log_ok ".trae config copied"

# ──────────────────────────────────────────
# [3.5/6] 复制 AAIF 真相源 + 多 harness 配置（白名单）
# ──────────────────────────────────────────
log_step "[3.5/6] Copy AAIF source + multi-harness config..."

# mindweave.plugin/ 完整复制（AAIF 唯一真相源 + Agent Plugins 1.0，发布后 install 脚本依赖它重新同步）
PLUGIN_SRC="$PROJECT_ROOT/mindweave.plugin"
PLUGIN_DST="$STAGING_DIR/mindweave.plugin"
for f in AGENTS.md tools.json triggers.json workflows.json plugin.json mcp.json; do
    [ -f "$PLUGIN_SRC/$f" ] && cp "$PLUGIN_SRC/$f" "$PLUGIN_DST/$f"
done
cp -r "$PLUGIN_SRC/skills" "$PLUGIN_DST/skills"
cp -r "$PLUGIN_SRC/runtime" "$PLUGIN_DST/runtime"

# Tier 2 原生生成目录（opencode；skills/AGENTS.md 统一从 mindweave.plugin/ 复制，保证最新）
for harness in opencode; do
    h_dst="$STAGING_DIR/.$harness"
    cp -r "$PLUGIN_SRC/skills" "$h_dst/skills"
    cp "$PLUGIN_SRC/AGENTS.md" "$h_dst/AGENTS.md"
done

# .opencode/opencode.json（instructions 指向 mindweave.plugin/AGENTS.md，cwd 为相对路径）
cp "$PLUGIN_SRC/runtime/opencode.json" "$STAGING_DIR/.opencode/opencode.json"

# Tier 1（CodeBuddy，自有市场格式）：市场通道三文件
cp "$PLUGIN_SRC/.mcp.json" "$STAGING_DIR/mindweave.plugin/.mcp.json"
cp "$PLUGIN_SRC/.codebuddy-plugin/plugin.json" "$STAGING_DIR/mindweave.plugin/.codebuddy-plugin/plugin.json"
cp "$PROJECT_ROOT/.codebuddy-plugin/marketplace.json" "$STAGING_DIR/.codebuddy-plugin/marketplace.json"

# scripts/（同步与生成工具链，发布后 install 脚本依赖）
for f in generate-aaif-declarations.py sync-agent-configs.ps1 sync-agent-configs.sh pre-commit check-config-drift.sh check_version.py; do
    [ -f "$PROJECT_ROOT/scripts/$f" ] && cp "$PROJECT_ROOT/scripts/$f" "$STAGING_DIR/scripts/$f"
done

# 根 package.json（AAIF 声明入口 + publish 脚本）
[ -f "$PROJECT_ROOT/package.json" ] && cp "$PROJECT_ROOT/package.json" "$STAGING_DIR/package.json"
log_ok "AAIF source + multi-harness config copied"

# ──────────────────────────────────────────
# [4/6] 复制 mindweave-mcp 源码（白名单）
# ──────────────────────────────────────────
log_step "[4/6] Copy mindweave-mcp source..."

MCP_SRC="$PROJECT_ROOT/mindweave.plugin/mindweave-mcp"
MCP_DST="$STAGING_DIR/mindweave.plugin/mindweave-mcp"

# 4a. 顶层文件
for f in pyproject.toml uv.lock .python-version; do
    [ -f "$MCP_SRC/$f" ] && cp "$MCP_SRC/$f" "$MCP_DST/$f"
done

# 4b. src/ 递归复制（排除 __pycache__、.pytest_cache、*.pyc）
# 优先用 rsync；不可用时用 find + cp 兜底
# 注意：使用 cd + 相对路径的 find，避免 Git Bash 在 Windows 上路径混用问题
if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
        "$MCP_SRC/src/" "$MCP_DST/src/"
else
    mkdir -p "$MCP_DST/src"
    (
        cd "$MCP_SRC/src"
        find . -type f \
            ! -path '*/__pycache__/*' \
            ! -path '*/.pytest_cache/*' \
            ! -name '*.pyc' -print0
    ) | while IFS= read -r -d '' rel; do
        rel="${rel#./}"
        dst="$MCP_DST/src/$rel"
        mkdir -p "$(dirname "$dst")"
        cp "$MCP_SRC/src/$rel" "$dst"
    done
fi

# 4c. data/ 创建 .gitkeep 占位（不复制用户数据）
for sub in notes reviews images quizzes exports; do
    touch "$MCP_DST/data/$sub/.gitkeep"
done
log_ok "source copied"

# ──────────────────────────────────────────
# [5/6] 复制顶层文档和安装脚本
# ──────────────────────────────────────────
log_step "[5/6] Copy docs and install scripts..."
for f in install.ps1 install.sh README.md DEPLOY.md QUICKSTART.md LICENSE AGENTS.md package.json marketplace.json; do
    [ -f "$PROJECT_ROOT/$f" ] && cp "$PROJECT_ROOT/$f" "$STAGING_DIR/$f"
done
log_ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
log_step "[6/6] Verify and pack..."

# 验证关键文件存在
required=(
    ".trae/mcp.json"
    ".trae/skills/mindweave-capture/SKILL.md"
    "mindweave.plugin/AGENTS.md"
    "mindweave.plugin/tools.json"
    "mindweave.plugin/triggers.json"
    "mindweave.plugin/workflows.json"
    "mindweave.plugin/plugin.json"
    "mindweave.plugin/mcp.json"
    ".opencode/opencode.json"
    "mindweave.plugin/.mcp.json"
    "mindweave.plugin/.codebuddy-plugin/plugin.json"
    ".codebuddy-plugin/marketplace.json"
    "scripts/sync-agent-configs.sh"
    "AGENTS.md"
    "package.json"
    "mindweave.plugin/mindweave-mcp/pyproject.toml"
    "mindweave.plugin/mindweave-mcp/uv.lock"
    "mindweave.plugin/mindweave-mcp/.python-version"
    "mindweave.plugin/mindweave-mcp/src/mindweave_mcp/server.py"
    "install.ps1"
    "install.sh"
    "README.md"
    "marketplace.json"
)
missing=()
for rf in "${required[@]}"; do
    [ -f "$STAGING_DIR/$rf" ] || missing+=("$rf")
done
if [ ${#missing[@]} -gt 0 ]; then
    log_err "Missing required files:"
    for m in "${missing[@]}"; do log_err "  $m"; done
    exit 1
fi

# 验证没有误包含 .venv
if [ -d "$STAGING_DIR/mindweave.plugin/mindweave-mcp/.venv" ]; then
    log_err ".venv was accidentally included! Aborting."
    exit 1
fi

file_count=$(find "$STAGING_DIR" -type f | wc -l)
log_ok "verified ($file_count files, no .venv)"

# 打包为 zip（与 PowerShell 版产物一致）
log_step "Packing zip..."
if ! command -v zip >/dev/null 2>&1; then
    log_err "zip not found."
    log_err "  Linux/Debian: apt-get install -y zip"
    log_err "  macOS:        brew install zip"
    log_err "  Windows:      use scripts/build-release.ps1 (uses Compress-Archive)"
    exit 1
fi
(cd "$DIST_DIR" && zip -qr "$ZIP_PATH" "$PACKAGE_NAME")

# 打包为 tar.zst（现代 Linux/macOS 推荐，体积最小、速度最快）
log_step "Packing tar.zst..."
if ! command -v zstd >/dev/null 2>&1; then
    log_err "zstd not found."
    log_err "  Linux/Debian: apt-get install -y zstd"
    log_err "  macOS:        brew install zstd"
    exit 1
fi
tar -C "$DIST_DIR" -cf - --exclude='__pycache__' --exclude='.pytest_cache' --exclude='*.pyc' \
    "$PACKAGE_NAME" | zstd -3 -q -o "$ZST_PATH"

# 打包为 tar.gz（兼容性最好）
log_step "Packing tar.gz..."
if ! command -v gzip >/dev/null 2>&1; then
    log_err "gzip not found."
    exit 1
fi
tar -C "$DIST_DIR" -czf "$GZ_PATH" "$PACKAGE_NAME"

# 清理临时目录
rm -rf "$STAGING_DIR"

# 报告
echo ""
log_ok "packed:"
for f in "$ZIP_PATH" "$ZST_PATH" "$GZ_PATH"; do
    size=$(du -h "$f" | cut -f1)
    echo -e "  ${CYAN}$f${NC} ($size)"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Build complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "  Package: ${CYAN}$PACKAGE_NAME${NC}"
echo -e "  Files:   ${CYAN}$file_count${NC}"
echo ""
echo "  User steps:"
echo "  1. Extract MindWeave-v$VERSION.{zip|tar.zst|tar.gz}"
echo "  2. Run install.ps1 (or install.sh on Linux/macOS)"
echo "  3. Tier 1: add the local Agent Plugin (VS Code → mindweave.plugin/) or local market (CodeBuddy); Tier 2: open folder in Trae/opencode and enable project-level MCP"
echo ""
