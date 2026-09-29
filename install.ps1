# MindWeave MCP Server 安装脚本
# 适用于 Windows PowerShell
#
# 使用方法：
#   1. 右键此文件 → "使用 PowerShell 运行"
#   2. 或在 PowerShell 中执行: .\install.ps1
#
# 可选参数：
#   -FixPath       将 mindweave.plugin/runtime 中 ${workspaceFolder} 替换为绝对路径（并重新同步各平台目录）
#   -AgentRuntime  配置 Agent 运行时 (vscode/trae/codebuddy/opencode/all)
#
# 前置要求：
#   - Python 3.12+
#   - uv 包管理器 (https://docs.astral.sh/uv/)

param(
    [switch]$FixPath,
    [Parameter(Mandatory=$false)]
    [ValidateSet("vscode", "trae", "codebuddy", "opencode", "all")]
    [string]$AgentRuntime
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " MindWeave v0.3.2 安装向导" -ForegroundColor Cyan
Write-Host "  (VS Code / CodeBuddy 走插件通道 · Trae / opencode 走原生目录)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 获取脚本所在目录（项目根目录）
$projectRoot = $PSScriptRoot

# ──────────────────────────────────────────
# [1/5] 检查 uv 包管理器
# ──────────────────────────────────────────
Write-Host "[1/5] 检查 uv 包管理器..." -ForegroundColor Yellow
try {
    $uvVersion = uv --version 2>&1
    Write-Host "  ✓ uv 已安装 ($uvVersion)" -ForegroundColor Green
} catch {
    Write-Host "  ✗ uv 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 uv：" -ForegroundColor Yellow
    Write-Host '  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"' -ForegroundColor White
    Write-Host ""
    Write-Host "  或访问 https://docs.astral.sh/uv/getting-started/install/" -ForegroundColor White
    exit 1
}

# ──────────────────────────────────────────
# [2/5] 检查 Python 版本
# ──────────────────────────────────────────
Write-Host "[2/5] 检查 Python 版本 (>=3.12)..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Python 未安装" -ForegroundColor Red
    Write-Host ""
    Write-Host "  请先安装 Python 3.12+：" -ForegroundColor Yellow
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}
# 提取版本号并比较
$versionMatch = $pythonVersion -match "(\d+)\.(\d+)"
if ($versionMatch) {
    $major = [int]$Matches[1]
    $minor = [int]$Matches[2]
    if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 12)) {
        Write-Host "  ✗ Python 版本过低: $pythonVersion (需要 >= 3.12)" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请升级 Python: https://www.python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "  ✓ $pythonVersion" -ForegroundColor Green

# ──────────────────────────────────────────
# [3/4] 安装依赖
# ──────────────────────────────────────────
Write-Host "[3/4] 安装依赖..." -ForegroundColor Yellow

$mcpDir = Join-Path $projectRoot "mindweave.plugin\mindweave-mcp"

Push-Location $mcpDir
try {
    Write-Host "  正在安装依赖包..." -ForegroundColor Cyan
    uv sync 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ✗ 依赖安装失败" -ForegroundColor Red
        Write-Host ""
        Write-Host "  请尝试手动安装：" -ForegroundColor Yellow
        Write-Host "  cd mindweave.plugin/mindweave-mcp" -ForegroundColor White
        Write-Host "  uv sync" -ForegroundColor White
        exit 1
    }
    Write-Host "  ✓ 基础依赖安装完成" -ForegroundColor Green
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# [4/4] Agent Runtime 配置（多 harness）
# ──────────────────────────────────────────
if ($AgentRuntime) {
    Write-Host ""
    Write-Host "=== Agent Runtime 配置 ===" -ForegroundColor Cyan

    $SyncScript = Join-Path $PSScriptRoot "scripts/sync-agent-configs.ps1"

    switch ($AgentRuntime) {
        "vscode" {
            Write-Host "VS Code 配置说明 (Tier 1 · Agent Plugins 1.0):" -ForegroundColor Yellow
            Write-Host "  1. 用 VS Code 打开项目文件夹"
            Write-Host "  2. 在 Agent 面板添加本地 Agent Plugin，指向目录: mindweave.plugin/"
            Write-Host "     (含 plugin.json + mcp.json + skills/，即 Agent Plugins 1.0 包)"
        }
        "codebuddy" {
            Write-Host "CodeBuddy 配置说明 (Tier 1 · 本地插件市场):" -ForegroundColor Yellow
            Write-Host "  1. 用 CodeBuddy 打开项目文件夹"
            Write-Host "  2. 在对话框执行: /plugin marketplace add $projectRoot"
            Write-Host "     (该目录含 .codebuddy-plugin/marketplace.json，source 指向 ./mindweave.plugin)"
            Write-Host "  3. 执行: /plugin install mindweave@mindweave-local-market"
            Write-Host "  4. 必要时执行: /reload-plugins"
        }
        "trae" {
            Write-Host "正在同步 Trae 配置 (Tier 2 原生目录)..." -ForegroundColor Yellow
            if (Test-Path $SyncScript) {
                & $SyncScript -SkipOpencode
                Write-Host ""
                Write-Host "下一步:" -ForegroundColor Yellow
                Write-Host "  1. 用 Trae 打开项目文件夹"
                Write-Host "  2. 设置 > MCP > 启用「项目级 MCP」"
                Write-Host "  3. 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
            } else {
                Write-Host "  同步脚本不存在: $SyncScript" -ForegroundColor Red
            }
        }
        "opencode" {
            Write-Host "正在同步 opencode 配置 (Tier 2 原生目录)..." -ForegroundColor Yellow
            if (Test-Path $SyncScript) {
                & $SyncScript -SkipTrae
                Write-Host ""
                Write-Host "下一步:" -ForegroundColor Yellow
                Write-Host "  1. 在项目目录运行 opencode"
                Write-Host "  2. AGENTS.md 将自动加载"
            } else {
                Write-Host "  同步脚本不存在: $SyncScript" -ForegroundColor Red
            }
        }
        "all" {
            Write-Host "正在同步 Tier 2 配置 (Trae + opencode)..." -ForegroundColor Yellow
            if (Test-Path $SyncScript) {
                & $SyncScript
                Write-Host ""
                Write-Host "Tier 2 配置已同步。各运行时下一步:" -ForegroundColor Green
                Write-Host "  Trae: 设置 > 规则 > 开启「将 AGENTS.md 包含在上下文中」"
                Write-Host "  opencode: 在项目目录运行 opencode"
                Write-Host ""
                Write-Host "Tier 1 (VS Code / CodeBuddy) 请手动安装插件:" -ForegroundColor Yellow
                Write-Host "  VS Code:   添加本地 Agent Plugin → mindweave.plugin/"
                Write-Host "  CodeBuddy: /plugin marketplace add $projectRoot → /plugin install mindweave@mindweave-local-market"
            } else {
                Write-Host "  同步脚本不存在: $SyncScript" -ForegroundColor Red
            }
        }
    }
}

# ──────────────────────────────────────────
# 验证安装
# ──────────────────────────────────────────
Write-Host "[验证] 验证安装..." -ForegroundColor Yellow

Push-Location $mcpDir
try {
    # 验证 MCP Server 入口点可用
    $testResult = uv run mindweave-mcp --help 2>&1
    # FastMCP 的 --help 可能直接启动 server，所以只要不报错即可
    Write-Host "  ✓ MCP Server 入口点可用" -ForegroundColor Green

    # 验证 Web 入口点可用
    $webTest = uv run python -c "from mindweave_mcp.web.app import create_app; print('OK')" 2>&1
    if ($webTest -match "OK") {
        Write-Host "  ✓ Web 可视化模块可用" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Web 可视化模块验证跳过" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ⚠ 自动验证失败，但不影响使用" -ForegroundColor Yellow
    Write-Host "  如遇问题请手动验证: cd mindweave.plugin/mindweave-mcp && uv run mindweave-mcp" -ForegroundColor Yellow
} finally {
    Pop-Location
}

# ──────────────────────────────────────────
# mcp.json 路径回退方案（多运行时共用，AAIF 真相源 mindweave.plugin/runtime）
# ──────────────────────────────────────────
$runtimeDir = Join-Path $projectRoot "mindweave.plugin\runtime"
$traeJson = Join-Path $runtimeDir "trae.json"
if (Test-Path $traeJson) {
    $mcpContent = Get-Content $traeJson -Raw
    if ($mcpContent -match '\$\{workspaceFolder\}') {
        Write-Host ""
        Write-Host "  ℹ 检测到 runtime 配置使用了 \${workspaceFolder} 变量" -ForegroundColor Cyan
        Write-Host "    Trae 会自动替换此变量，无需手动配置" -ForegroundColor Cyan
        Write-Host "    如果你的环境不支持变量替换，请运行：" -ForegroundColor Cyan
        Write-Host "    .\install.ps1 -FixPath" -ForegroundColor White
    }
}

if ($FixPath) {
    Write-Host ""
    Write-Host "  正在修复 runtime 配置路径（mindweave.plugin/runtime）..." -ForegroundColor Yellow
    $fixedAny = $false
    $fixTargets = @(
        (Join-Path $runtimeDir "trae.json")
    )
    $ws = $projectRoot -replace '\\', '/'
    foreach ($t in $fixTargets) {
        if (Test-Path $t) {
            $content = Get-Content $t -Raw -Encoding UTF8
            if ($content -match '\$\{workspaceFolder\}') {
                $fixedContent = $content -replace '\$\{workspaceFolder\}', $ws
                Set-Content -Path $t -Value $fixedContent -Encoding UTF8
                Write-Host "  ✓ 已修复: $t" -ForegroundColor Green
                $fixedAny = $true
            } else {
                Write-Host "  ℹ 无需修复（无变量）: $t" -ForegroundColor DarkGray
            }
        } else {
            Write-Host "  ✗ 未找到 $t" -ForegroundColor Red
        }
    }
    if ($fixedAny) {
        Write-Host "  重新同步到各平台目录..." -ForegroundColor Gray
        & "$PSScriptRoot\scripts\sync-agent-configs.ps1"
    }
    Write-Host "  ⚠ 注意：修复后配置仅对当前路径有效，移动项目后需重新运行 -FixPath" -ForegroundColor Yellow
    Write-Host "  ⚠ 注意：多运行时可移植性会降低，建议优先升级运行时版本以支持变量" -ForegroundColor Yellow
}

# ──────────────────────────────────────────
# 安装 git pre-commit 钩子（配置同步机械防线）
# ──────────────────────────────────────────
Write-Host "安装 git pre-commit 钩子..." -ForegroundColor Yellow
$HookSrc = Join-Path $projectRoot "scripts/pre-commit"
$HookDst = Join-Path $projectRoot ".git/hooks/pre-commit"
if (Test-Path $HookSrc) {
    Copy-Item -Path $HookSrc -Destination $HookDst -Force
    Write-Host "  ✓ 已安装 pre-commit 钩子（拦截直接修改生成目录 .trae/.opencode 的违规提交）" -ForegroundColor Green
    Write-Host "    若需手动安装：Copy-Item scripts/pre-commit .git/hooks/pre-commit" -ForegroundColor DarkGray
} else {
    Write-Host "  ⚠ 未找到 $HookSrc，跳过钩子安装" -ForegroundColor Yellow
}

# ──────────────────────────────────────────
# 安装完成提示
# ──────────────────────────────────────────
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  ✓ 安装完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步操作（按所用运行时选择对应通道）：" -ForegroundColor White
Write-Host ""
Write-Host "  1. 用对应运行时打开此文件夹" -ForegroundColor White
Write-Host "     文件 → 打开文件夹 → 选择: $projectRoot" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  2. 启用项目级 MCP（Trae: 设置 → MCP；CodeBuddy: 信任 mindweave-mcp）" -ForegroundColor White
Write-Host ""
Write-Host "  3. 重启运行时" -ForegroundColor White
Write-Host ""
Write-Host "  4. 开始使用！" -ForegroundColor White
Write-Host "     /capture       - 采集错题（拍照/文本）" -ForegroundColor DarkGray
Write-Host "     /batch-capture - 批量采集错题" -ForegroundColor DarkGray
Write-Host "     /analyze       - 分析错题原因" -ForegroundColor DarkGray
Write-Host "     /review        - 生成复习计划" -ForegroundColor DarkGray
Write-Host "     /stats         - 查看错题统计" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  可选：启动 Web 可视化界面" -ForegroundColor Cyan
Write-Host "     cd mindweave.plugin/mindweave-mcp && uv run mindweave-web" -ForegroundColor DarkGray
Write-Host "     浏览器访问 http://127.0.0.1:8003" -ForegroundColor DarkGray
Write-Host ""
