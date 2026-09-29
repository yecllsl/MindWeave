# MindWeave 发布包构建脚本
# 从源码生成可分发的 zip 包（白名单复制策略，避免误打包 .venv）
#
# 使用方法：
#   pwsh .\scripts\build-release.ps1 [-Version "0.3.2"]
#
# 输出：
#   dist/MindWeave-v0.3.2.zip

param(
    [string]$Version = "0.3.2"
)

$ErrorActionPreference = "Stop"

# ──────────────────────────────────────────
# 路径定义
# ──────────────────────────────────────────
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$distDir = Join-Path $projectRoot "dist"
$packageName = "MindWeave-v$Version"
$tempDir = Join-Path $distDir $packageName
$zipPath = Join-Path $distDir "$packageName.zip"

function Write-Step([string]$msg) {
    Write-Host "[build] $msg" -ForegroundColor Yellow
}
function Write-Ok([string]$msg) {
    Write-Host "[ok]    $msg" -ForegroundColor Green
}
function Write-Err([string]$msg) {
    Write-Host "[err]   $msg" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  MindWeave v$Version release build" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ──────────────────────────────────────────
# [1/6] 清理旧构建（使用 .NET API 处理长路径）
# ──────────────────────────────────────────
Write-Step "[1/6] Clean previous build..."
if (Test-Path $distDir) {
    # 使用 .NET API 直接删除，可处理部分长路径；失败则用 robocopy MIR 清空
    try {
        [System.IO.Directory]::Delete($distDir, $true)
    } catch {
        $emptyTmp = Join-Path $env:TEMP "dr_empty_$(Get-Random)"
        New-Item -ItemType Directory -Path $emptyTmp -Force | Out-Null
        robocopy $emptyTmp $distDir /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null
        [System.IO.Directory]::Delete($distDir, $true)
        Remove-Item -Recurse -Force $emptyTmp -ErrorAction SilentlyContinue
    }
}
New-Item -ItemType Directory -Path $distDir | Out-Null
Write-Ok "cleaned"

# ──────────────────────────────────────────
# [2/6] 创建目标目录结构
# ──────────────────────────────────────────
Write-Step "[2/6] Create directory structure..."
# 顶层目录
New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
# .trae 子目录（skills/ 同步产物；rules 已合并入 mindweave.plugin/AGENTS.md，不再打包）
New-Item -ItemType Directory -Path (Join-Path $tempDir ".trae\skills") -Force | Out-Null
# AAIF 真相源 + 多 harness 目录
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\skills") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\runtime") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir ".opencode\skills") -Force | Out-Null
# CodeBuddy 插件清单目录（Tier 1 市场通道）：插件根内 .codebuddy-plugin/ + 根级 .codebuddy-plugin/
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\.codebuddy-plugin") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir ".codebuddy-plugin") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "scripts") -Force | Out-Null
# mindweave-mcp 子目录（内联在插件包内）
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\mindweave-mcp\src") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\mindweave-mcp\data\notes") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\mindweave-mcp\data\reviews") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\mindweave-mcp\data\images") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\mindweave-mcp\data\quizzes") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $tempDir "mindweave.plugin\mindweave-mcp\data\exports") -Force | Out-Null
Write-Ok "directories created"

# ──────────────────────────────────────────
# [3/6] 复制 .trae 配置（白名单）
# ──────────────────────────────────────────
Write-Step "[3/6] Copy .trae config..."

# .trae 顶层文件
# 注意：源 .trae/mcp.json 受 Trae 保护，可能包含硬编码的绝对路径 cwd。
# 发布包必须使用 ${workspaceFolder} 变量版本，因此在构建时覆盖写入正确内容。
$traeTopFiles = @("hooks.json")
foreach ($f in $traeTopFiles) {
    $src = Join-Path $projectRoot ".trae\$f"
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $tempDir ".trae\$f") -Force
    }
}

# 写入发布版 mcp.json（使用 ${workspaceFolder} 变量，解压到任意位置均可工作）
$releaseMcpJson = @'
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
'@
$releaseMcpJson | Set-Content -Path (Join-Path $tempDir ".trae\mcp.json") -Encoding UTF8 -NoNewline

# .trae/skills/ 每个 skill 目录（只复制 SKILL.md，排除 __pycache__）
$skillsSrc = Join-Path $projectRoot ".trae\skills"
if (Test-Path $skillsSrc) {
    Get-ChildItem $skillsSrc -Directory | ForEach-Object {
        $skillName = $_.Name
        $skillDst = Join-Path $tempDir ".trae\skills\$skillName"
        New-Item -ItemType Directory -Path $skillDst -Force | Out-Null
        # 复制 skill 目录下的所有文件（递归，但 skill 一般只有 SKILL.md）
        Get-ChildItem $_.FullName -File -Recurse | ForEach-Object {
            $relPath = $_.FullName.Substring($_.FullName.IndexOf($skillName) + $skillName.Length + 1)
            $dstFile = Join-Path $skillDst $relPath
            $dstParent = Split-Path $dstFile -Parent
            if (!(Test-Path $dstParent)) { New-Item -ItemType Directory -Path $dstParent -Force | Out-Null }
            Copy-Item $_.FullName $dstFile -Force
        }
    }
}
Write-Ok ".trae config copied"

# ──────────────────────────────────────────
# [3.5/6] 复制 AAIF 真相源 + 多 harness 配置（白名单）
# ──────────────────────────────────────────
Write-Step "[3.5/6] Copy AAIF source + multi-harness config..."

# mindweave.plugin/ 完整复制（AAIF 唯一真相源 + Agent Plugins 1.0，发布后 install 脚本依赖它重新同步）
$pluginSrc = Join-Path $projectRoot "mindweave.plugin"
$pluginDst = Join-Path $tempDir "mindweave.plugin"
$pluginTopFiles = @("AGENTS.md", "tools.json", "triggers.json", "workflows.json", "plugin.json", "mcp.json")
foreach ($f in $pluginTopFiles) {
    $src = Join-Path $pluginSrc $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $pluginDst $f) -Force
    }
}
Copy-Item (Join-Path $pluginSrc "skills") (Join-Path $pluginDst "skills") -Recurse -Force
Copy-Item (Join-Path $pluginSrc "runtime") (Join-Path $pluginDst "runtime") -Recurse -Force

# Tier 2 原生生成目录（opencode；skills/AGENTS.md 统一从 mindweave.plugin/ 复制，保证最新）
foreach ($harness in @("opencode")) {
    $hDst = Join-Path $tempDir ".$harness"
    Copy-Item (Join-Path $pluginSrc "skills") (Join-Path $hDst "skills") -Recurse -Force
    Copy-Item (Join-Path $pluginSrc "AGENTS.md") (Join-Path $hDst "AGENTS.md") -Force
}

# .opencode/opencode.json（instructions 指向 mindweave.plugin/AGENTS.md，cwd 为相对路径）
Copy-Item (Join-Path $pluginSrc "runtime\opencode.json") (Join-Path $tempDir ".opencode\opencode.json") -Force

# Tier 1（CodeBuddy，自有市场格式）：市场通道三文件
Copy-Item (Join-Path $pluginSrc ".mcp.json") (Join-Path $tempDir "mindweave.plugin\.mcp.json") -Force
Copy-Item (Join-Path $pluginSrc ".codebuddy-plugin\plugin.json") (Join-Path $tempDir "mindweave.plugin\.codebuddy-plugin\plugin.json") -Force
Copy-Item (Join-Path $projectRoot ".codebuddy-plugin\marketplace.json") (Join-Path $tempDir ".codebuddy-plugin\marketplace.json") -Force

# scripts/（同步与生成工具链，发布后 install 脚本依赖）
Copy-Item (Join-Path $projectRoot "scripts\generate-aaif-declarations.py") (Join-Path $tempDir "scripts\") -Force
Copy-Item (Join-Path $projectRoot "scripts\sync-agent-configs.ps1") (Join-Path $tempDir "scripts\") -Force
Copy-Item (Join-Path $projectRoot "scripts\sync-agent-configs.sh") (Join-Path $tempDir "scripts\") -Force
Copy-Item (Join-Path $projectRoot "scripts\pre-commit") (Join-Path $tempDir "scripts\") -Force
Copy-Item (Join-Path $projectRoot "scripts\check_version.py") (Join-Path $tempDir "scripts\") -Force
Copy-Item (Join-Path $projectRoot "scripts\check-config-drift.sh") (Join-Path $tempDir "scripts\") -Force

# 根 package.json（AAIF 声明入口 + publish 脚本）
Copy-Item (Join-Path $projectRoot "package.json") (Join-Path $tempDir "package.json") -Force
Write-Ok "AAIF source + multi-harness config copied"

# ──────────────────────────────────────────
# [4/6] 复制 mindweave-mcp 源码（白名单）
# ──────────────────────────────────────────
Write-Step "[4/6] Copy mindweave-mcp source..."

$mcpSrc = Join-Path $projectRoot "mindweave.plugin\mindweave-mcp"
$mcpDst = Join-Path $tempDir "mindweave.plugin\mindweave-mcp"

# 4a. 顶层配置文件
$mcpTopFiles = @("pyproject.toml", "uv.lock", ".python-version")
foreach ($f in $mcpTopFiles) {
    $src = Join-Path $mcpSrc $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $mcpDst $f) -Force
    }
}

# 4b. src/ 目录递归复制（用 robocopy 排除 __pycache__ 和 .pytest_cache）
$srcDir = Join-Path $mcpSrc "src"
$srcDst = Join-Path $mcpDst "src"
if (Test-Path $srcDir) {
    # robocopy 对单个目录的 /XD 排除很可靠（直接给目录名）
    $rc = robocopy $srcDir $srcDst /E /XD __pycache__ .pytest_cache /XF *.pyc /NFL /NDL /NJH /NJS /NP
    # robocopy exit code < 8 表示成功
    if ($LASTEXITCODE -ge 8) {
        Write-Err "robocopy failed with exit code $LASTEXITCODE"
        exit 1
    }
}

# 4c. data/ 目录：只创建 .gitkeep 占位文件（不复制用户数据）
$dataKeepFiles = @(
    "notes\.gitkeep",
    "reviews\.gitkeep",
    "images\.gitkeep",
    "quizzes\.gitkeep",
    "exports\.gitkeep"
)
foreach ($kf in $dataKeepFiles) {
    $srcKeep = Join-Path $mcpSrc "data\$kf"
    $dstKeep = Join-Path $mcpDst "data\$kf"
    if (Test-Path $srcKeep) {
        Copy-Item $srcKeep $dstKeep -Force
    } else {
        # 源没有 .gitkeep 也创建一个空占位
        New-Item -ItemType File -Path $dstKeep -Force | Out-Null
    }
}
Write-Ok "source copied"

# ──────────────────────────────────────────
# [5/6] 复制顶层文档和安装脚本
# ──────────────────────────────────────────
Write-Step "[5/6] Copy docs and install scripts..."
$topFiles = @("install.ps1", "install.sh", "README.md", "DEPLOY.md", "QUICKSTART.md", "LICENSE", "AGENTS.md", "package.json", "marketplace.json")
foreach ($f in $topFiles) {
    $src = Join-Path $projectRoot $f
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $tempDir $f) -Force
    }
}
Write-Ok "docs copied"

# ──────────────────────────────────────────
# [6/6] 验证关键文件 + 打包
# ──────────────────────────────────────────
Write-Step "[6/6] Verify and pack..."

# 验证关键文件存在
$requiredFiles = @(
    ".trae\mcp.json",
    ".trae\skills\mindweave-capture\SKILL.md",
    "mindweave.plugin\AGENTS.md",
    "mindweave.plugin\tools.json",
    "mindweave.plugin\triggers.json",
    "mindweave.plugin\workflows.json",
    "mindweave.plugin\plugin.json",
    "mindweave.plugin\mcp.json",
    ".opencode\opencode.json",
    "mindweave.plugin\.mcp.json",
    "mindweave.plugin\.codebuddy-plugin\plugin.json",
    ".codebuddy-plugin\marketplace.json",
    "scripts\sync-agent-configs.ps1",
    "AGENTS.md",
    "package.json",
    "mindweave.plugin\mindweave-mcp\pyproject.toml",
    "mindweave.plugin\mindweave-mcp\uv.lock",
    "mindweave.plugin\mindweave-mcp\.python-version",
    "mindweave.plugin\mindweave-mcp\src\mindweave_mcp\server.py",
    "install.ps1",
    "install.sh",
    "README.md",
    "marketplace.json"
)

$missing = @()
foreach ($rf in $requiredFiles) {
    $fullPath = Join-Path $tempDir $rf
    if (!(Test-Path $fullPath)) {
        $missing += $rf
    }
}

if ($missing.Count -gt 0) {
    Write-Err "Missing required files:"
    $missing | ForEach-Object { Write-Err "  $_" }
    exit 1
}

# 验证没有误包含 .venv
$venvCheck = Join-Path $tempDir "mindweave.plugin\mindweave-mcp\.venv"
if (Test-Path $venvCheck) {
    Write-Err ".venv was accidentally included! Aborting."
    exit 1
}

# 统计文件数
$fileCount = (Get-ChildItem $tempDir -Recurse -File | Measure-Object).Count
Write-Ok "verified ($fileCount files, no .venv)"

# 打包为 zip
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $tempDir -DestinationPath $zipPath -Force

$zipItem = Get-Item $zipPath
$zipSizeMB = [math]::Round($zipItem.Length / 1MB, 2)
Write-Ok "packed: $zipPath ($zipSizeMB MB)"

# ──────────────────────────────────────────
# 清理临时目录
# ──────────────────────────────────────────
try {
    [System.IO.Directory]::Delete($tempDir, $true)
} catch {
    # 长路径兜底
    $emptyTmp2 = Join-Path $env:TEMP "dr_empty2_$(Get-Random)"
    New-Item -ItemType Directory -Path $emptyTmp2 -Force | Out-Null
    robocopy $emptyTmp2 $tempDir /MIR /R:0 /W:0 /NFL /NDL /NJH /NJS /NP | Out-Null
    [System.IO.Directory]::Delete($tempDir, $true)
    Remove-Item -Recurse -Force $emptyTmp2 -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Build complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Package: $zipPath" -ForegroundColor Cyan
Write-Host "  Size:    $zipSizeMB MB" -ForegroundColor Cyan
Write-Host "  Files:   $fileCount" -ForegroundColor Cyan
Write-Host ""
Write-Host "  User steps:" -ForegroundColor White
Write-Host "  1. Extract MindWeave-v$Version.zip" -ForegroundColor DarkGray
Write-Host "  2. Run install.ps1" -ForegroundColor DarkGray
Write-Host "  3. Open folder in your runtime (Trae/CodeBuddy/opencode), enable project-level MCP" -ForegroundColor DarkGray
Write-Host ""
