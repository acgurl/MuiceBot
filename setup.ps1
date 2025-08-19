param(
  [string]$RepoUrl = "https://github.com/Moemu/MuiceBot.git",
  [string]$TargetDir = ".\MuiceBot",
  [switch]$NonInteractive
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Info([string]$s) { Write-Host ('[INFO] {0}' -f $s) -ForegroundColor Cyan }
function Write-Warn([string]$s) { Write-Host ('[WARN] {0}' -f $s) -ForegroundColor Yellow }
function Write-Err([string]$s)  { Write-Host ('[ERROR] {0}' -f $s) -ForegroundColor Red }

function Test-Command([string]$exe) {
  try {
    Get-Command $exe -ErrorAction Stop > $null
    return $true
  } catch {
    return $false
  }
}

function Ensure-UV {
  try {
    if (Test-Command "uv") {
      Write-Info "uv 已存在."
      return
    }

  Write-Info "尝试通过 winget 安装 uv..."
  if (Test-Command "winget") {
      try {
        winget install --id=astral-sh.uv -e --accept-package-agreements --accept-source-agreements
        if (Test-Command 'uv') {
          Write-Info 'uv 安装成功(winget)'
          return
        }
      } catch {
  Write-Warn "winget 安装失败，改为官方安装脚本。"
      }
    }

  Write-Info "通过官方安装脚本安装 uv..."
    try {
  $script = (New-Object System.Net.WebClient).DownloadString('https://astral.sh/uv/install.ps1')
      Invoke-Expression $script
      } catch {
        Write-Err "下载/执行 uv 安装脚本失败，请手动安装 uv: https://astral.sh/uv"
        throw
      }

    if (Test-Command "uv") {
      Write-Info "uv 安装完成"
    } else {
      throw "uv 安装后仍不可用"
    }
  } catch {
    throw
  }
}

function Ensure-Python312 {
  try {
    $pythonOk = $false
  if (Test-Command "python") {
      try {
        $pv = (& python --version 2>&1).Trim()
        if ($pv -match 'Python\s+3\.12') {
          $pythonOk = $true
          Write-Info ("系统 Python 已为 3.12: {0}" -f $pv)
        }
      } catch {
        # 忽略
      }
    }

    if (-not $pythonOk) {
      if (-not (Test-Command "uv")) {
        Write-Warn "uv 未安装，跳过 uv 安装 python"
        return
      }
      Write-Info "用 uv 安装 Python 3.12（若已存在则会跳过）..."
      try {
        uv python install 3.12 --default
      } catch {
  Write-Warn "uv 安装 Python 失败，后续使用 uv run 运行命令。"
      }
    }
  } catch {
    throw
  }
}

function Clone-Or-Update {
  param([string]$url, [string]$dir)
  try {
    if (Test-Path $dir) {
      if (Test-Command "git") {
        Write-Info ("目录存在，尝试 git pull 更新： {0}" -f $dir)
        Push-Location $dir
        try {
          git pull --ff-only
        } catch {
          Write-Warn "git pull 失败，保留现有代码。"
        } finally {
          Pop-Location
        }
      } else {
        Write-Warn "目录存在但未安装 git，跳过自动更新。"
      }
    } else {
      if (Test-Command "git") {
        Write-Info ("克隆仓库到 {0}" -f $dir)
        git clone $url $dir
      } else {
        Write-Info "未找到 git，改用下载 zip 的方式克隆（仅 main 分支）"
        $tmp = Join-Path $env:TEMP ('repo_{0}.zip' -f (Get-Random))
        $zipUrl = ($url.TrimEnd('.git') + '/archive/refs/heads/main.zip')
        Invoke-WebRequest -Uri $zipUrl -OutFile $tmp -UseBasicParsing
        $parent = Split-Path -Path $dir -Parent
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
        Expand-Archive -Path $tmp -DestinationPath $parent -Force
        Remove-Item $tmp -Force
  # 移动解压出的文件夹至目标名
  $extracted = Get-ChildItem -Path $parent -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  $resolvedTarget = Resolve-Path -LiteralPath $dir -ErrorAction SilentlyContinue
  if ($extracted -and ($null -eq $resolvedTarget -or $extracted.FullName -ne $resolvedTarget)) {
          $destName = Split-Path -Path $dir -Leaf
          $targetFull = Join-Path $parent $destName
          if (Test-Path $targetFull) { Remove-Item -Recurse -Force $targetFull }
          Rename-Item -Path $extracted.FullName -NewName $destName
        }
      }
    }
  } catch {
    throw
  }
}

function UV-Sync-Project {
  param([string]$projDir)
  try {
  if (-not (Test-Path $projDir)) { throw ("项目目录不存在: {0}" -f $projDir) }
    Push-Location $projDir
    try {
  Write-Info "执行 uv sync 安装依赖..."
      uv sync
      uv add "nonebot2[websockets]"
  Write-Info "uv sync 完成。"
    } catch {
  Write-Warn ("uv sync 失败: {0}" -f $_.Exception.Message)
      throw
    } finally {
      Pop-Location
    }
  } catch {
    throw
  }
}

function Run-DB-Migrations {
  param([string]$projDir)
  try {
  if (-not (Test-Path $projDir)) { throw ("项目目录不存在: {0}" -f $projDir) }
    Push-Location $projDir
    try {
  Write-Info "尝试运行 nb orm upgrade..."
      uv run nb orm upgrade
  Write-Info "nb orm upgrade 已尝试执行。"
    } catch {
  Write-Warn "nb orm upgrade 失败，尝试 alembic upgrade head..."
      try {
        uv run python -m alembic upgrade head
      } catch {
  Write-Warn ("alembic 迁移也失败：{0}" -f $_.Exception.Message)
      }
    } finally {
      Pop-Location
    }
  } catch {
    throw
  }
}

function Ensure-Env-For-NapCat {
  param([string]$projDir)
  try {
  if (-not (Test-Path $projDir)) { throw ("项目目录不存在: {0}" -f $projDir) }
    $envPath = Join-Path $projDir ".env"
    if (Test-Path $envPath) {
  Write-Info ".env 已存在，跳过写入示例"
      return
    }
    $content = @'
# MuiceBot .env 示例（NapCat / OneBot v11 适配）
# 替换下面的值为你的配置
DRIVER=~httpx+~websockets
ONEBOT_ACCESS_TOKEN=your_napcat_token_here
# DATABASE_URL=sqlite+aiosqlite:///./muicebot.sqlite
'@
  Write-Info ("写入 .env 示例到 {0}" -f $envPath)
    $content | Out-File -FilePath $envPath -Encoding utf8
  } catch {
    throw
  }
}

# 主流程
try {
  Write-Info "开始 MuiceBot 部署流程"

  Ensure-UV
  Ensure-Python312
  Clone-Or-Update -url $RepoUrl -dir $TargetDir
  UV-Sync-Project -projDir $TargetDir
  Ensure-Env-For-NapCat -projDir $TargetDir
  Run-DB-Migrations -projDir $TargetDir

  Write-Info "完成。建议检查 .env 并手动启动机器人。"
  Write-Host "常用命令：" -ForegroundColor Green
  Write-Host " uv sync" -ForegroundColor Green
  Write-Host " uv run nb orm upgrade" -ForegroundColor Green
  Write-Host " uv run python bot.py" -ForegroundColor Green
  exit 0
} catch {
  Write-Err ('部署出错：{0}' -f $_.Exception.Message)
  exit 1
}
