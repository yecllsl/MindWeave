#!/usr/bin/env pwsh
# 将 mindweave.plugin/ (配置真相源 + Agent Plugins 1.0 插件包) 单向同步到 Tier 2 原生 harness 项目目录:
#   .trae/  .opencode/
#
# 注：CodeBuddy 与 VS Code 走 Tier 1 插件通道（mindweave.plugin/ 即 Agent Plugins 1.0 包，
#      经 .codebuddy-plugin/marketplace.json 本地市场安装），不再生成 .codebuddy/ 原生目录。
#
# 用法:
#   ./scripts/sync-agent-configs.ps1                 # 同步全部 (Tier 2: .trae + .opencode)
#   ./scripts/sync-agent-configs.ps1 -SkipTrae       # 跳过 Trae
[CmdletBinding()]
param(
    [switch]$SkipTrae,
    [switch]$SkipOpencode
)

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$PluginDir = Join-Path $ProjectRoot 'mindweave.plugin'
$PluginRuntime = Join-Path $PluginDir 'runtime'
$PluginSkills = Join-Path $PluginDir 'skills'
$PluginMd = Join-Path $PluginDir 'AGENTS.md'
$McpDir = Join-Path $PluginDir 'mindweave-mcp'

$Green = "$([char]0x1b)[32m"
$Yellow = "$([char]0x1b)[33m"
$Cyan = "$([char]0x1b)[36m"
$Red = "$([char]0x1b)[31m"
$NC = "$([char]0x1b)[0m"

if (-not (Test-Path $PluginRuntime)) { throw "错误: 运行时配置目录不存在: $PluginRuntime" }
if (-not (Test-Path $PluginSkills)) { throw "错误: 技能目录不存在: $PluginSkills" }
if (-not (Test-Path $PluginMd)) { throw "错误: AGENTS.md 不存在: $PluginMd" }

Write-Host "$Cyan=== MindWeave AAIF Config Sync ===$NC"
Write-Host "项目根目录: $ProjectRoot"
Write-Host "配置源: mindweave.plugin/ (AAIF 标准 + Agent Plugins 1.0)"

# ── 先重新生成 AAIF 声明文件（tools/triggers/workflows.json）──
function Invoke-AaifDeclarations {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "$Red未找到 uv，无法生成 AAIF 声明文件 (tools.json/triggers.json/workflows.json)$NC" -ForegroundColor Red
        throw "uv not found"
    }
    $script = Join-Path $PSScriptRoot 'generate-aaif-declarations.py'
    Write-Host "$Yellow生成 AAIF 声明文件 → mindweave.plugin/$NC"
    Push-Location $ProjectRoot
    try {
        & uv run --no-sync --directory $McpDir python $script
        if ($LASTEXITCODE -ne 0) { throw "AAIF 声明文件生成失败 (exit=$LASTEXITCODE)" }
    } finally {
        Pop-Location
    }
    Write-Host "$Green  已生成 tools.json / triggers.json / workflows.json$NC"
}

function Sync-Skills {
    param([string]$TargetDir)
    $targetSkills = Join-Path $TargetDir 'skills'
    New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
    if (Test-Path $targetSkills) { Remove-Item -Recurse -Force $targetSkills }
    Write-Host "$Yellow同步 Skills → $targetSkills$NC"
    Copy-Item -Recurse $PluginSkills $targetSkills
    $count = (Get-ChildItem $targetSkills -Directory).Count
    Write-Host "$Green  已同步 $count 个 Skills$NC"
}

function Sync-AgentsMd {
    param([string]$TargetDir)
    $targetMd = Join-Path $TargetDir 'AGENTS.md'
    Write-Host "$Yellow同步 AGENTS.md → $targetMd$NC"
    Copy-Item -Force $PluginMd $targetMd
    Write-Host "$Green  已同步 AGENTS.md$NC"
}

function Generate-TraeConfig {
    $traeDir = Join-Path $ProjectRoot '.trae'
    New-Item -ItemType Directory -Force -Path $traeDir | Out-Null
    $source = Join-Path $PluginRuntime 'trae.json'
    if (Test-Path $source) {
        Write-Host "$Yellow复制 Trae 配置 → .trae/$NC"
        Copy-Item -Force $source (Join-Path $traeDir 'mcp.json')
        Write-Host "$Green  已生成 Trae 配置$NC"
    }
}

function Generate-OpencodeConfig {
    $opencodeDir = Join-Path $ProjectRoot '.opencode'
    New-Item -ItemType Directory -Force -Path $opencodeDir | Out-Null
    $source = Join-Path $PluginRuntime 'opencode.json'
    if (Test-Path $source) {
        Write-Host "$Yellow复制 opencode 配置 → .opencode/$NC"
        Copy-Item -Force $source (Join-Path $opencodeDir 'opencode.json')
        Write-Host "$Green  已生成 opencode 配置$NC"
    }
}

# ── 主流程 ──
Invoke-AaifDeclarations

if (-not $SkipTrae) {
    Write-Host "`n$Cyan--- Trae ---$NC"
    Sync-Skills (Join-Path $ProjectRoot '.trae')
    Sync-AgentsMd $ProjectRoot   # Trae 读取项目根 AGENTS.md
    Generate-TraeConfig
}
if (-not $SkipOpencode) {
    Write-Host "`n$Cyan--- opencode ---$NC"
    Sync-Skills (Join-Path $ProjectRoot '.opencode')
    Sync-AgentsMd (Join-Path $ProjectRoot '.opencode')
    Generate-OpencodeConfig
}

Write-Host "`n$Cyan=== 同步完成 ===$NC"
