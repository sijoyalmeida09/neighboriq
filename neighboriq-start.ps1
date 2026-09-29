<#
.SYNOPSIS
    Start NeighborIQ services (API server + optional content pipeline).

.DESCRIPTION
    Validates Python environment, creates required directories, then starts
    the FastAPI server. Optionally runs PM2 for full process management.

.EXAMPLE
    .\neighboriq-start.ps1                   # start API server in foreground
    .\neighboriq-start.ps1 -Pm2              # start via PM2 (background, auto-restart)
    .\neighboriq-start.ps1 -Pm2 -Stop        # stop all PM2 processes
    .\neighboriq-start.ps1 -RunPipeline 02122  # run content pipeline for a zip

.NOTES
    Requires: Python 3.11+, uvicorn (pip install uvicorn fastapi)
    Optional: pm2 (npm install -g pm2), groq / anthropic API keys in .env
#>

param(
    [switch]$Pm2,
    [switch]$Stop,
    [string]$RunPipeline = "",
    [int]$Port = 8000
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root      = "C:\Sijoy_2.0\automation"
$NiqRoot   = "$Root\neighboriq"
$LogDir    = "$NiqRoot\data\logs"
$DataDir   = "$NiqRoot\data\content"
$EnvFile   = "$NiqRoot\.env"

# ── helpers ─────────────────────────────────────────────────────────────────

function Write-Step($msg) { Write-Host "  >> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)   { Write-Host "  OK $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "  !! $msg" -ForegroundColor Yellow }

# ── stop mode ────────────────────────────────────────────────────────────────

if ($Stop) {
    Write-Step "Stopping NeighborIQ PM2 processes..."
    pm2 stop ecosystem.config.js
    pm2 delete ecosystem.config.js
    Write-Ok "All processes stopped."
    exit 0
}

# ── env check ────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "NeighborIQ Startup" -ForegroundColor White
Write-Host "==================" -ForegroundColor White

Write-Step "Checking Python..."
try {
    $pyVersion = python --version 2>&1
    Write-Ok $pyVersion
} catch {
    Write-Error "Python not found. Install Python 3.11+ and add to PATH."
    exit 1
}

Write-Step "Checking uvicorn..."
$uvFound = python -c "import uvicorn; print('ok')" 2>&1
if ($uvFound -ne "ok") {
    Write-Warn "uvicorn not installed. Running: pip install uvicorn fastapi"
    pip install uvicorn fastapi
}

# ── directories ──────────────────────────────────────────────────────────────

foreach ($dir in @($LogDir, $DataDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
        Write-Step "Created $dir"
    }
}

# ── load .env ────────────────────────────────────────────────────────────────

if (Test-Path $EnvFile) {
    Write-Step "Loading .env..."
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key   = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"').Trim("'")
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
    Write-Ok ".env loaded"
} else {
    Write-Warn "No .env file found at $EnvFile — LLM features disabled"
}

# ── content pipeline mode ────────────────────────────────────────────────────

if ($RunPipeline -ne "") {
    Write-Step "Running content pipeline for zip $RunPipeline..."
    Set-Location $Root
    $env:PYTHONPATH = $Root
    python -m neighboriq.content.pipeline --zip $RunPipeline --top 3
    exit $LASTEXITCODE
}

# ── pm2 mode ─────────────────────────────────────────────────────────────────

if ($Pm2) {
    Write-Step "Checking PM2..."
    $pm2Found = Get-Command pm2 -ErrorAction SilentlyContinue
    if (-not $pm2Found) {
        Write-Warn "PM2 not installed. Running: npm install -g pm2"
        npm install -g pm2
    }

    Set-Location $NiqRoot
    Write-Step "Starting PM2 processes from ecosystem.config.js..."
    pm2 start ecosystem.config.js
    pm2 save
    Write-Ok "PM2 processes started."
    Write-Host ""
    pm2 status
    Write-Host ""
    Write-Host "Dashboard: http://localhost:$Port" -ForegroundColor Green
    Write-Host "Logs:      pm2 logs neighboriq-api" -ForegroundColor Gray
    Write-Host "Stop:      .\neighboriq-start.ps1 -Pm2 -Stop" -ForegroundColor Gray
    exit 0
}

# ── foreground API mode (default) ─────────────────────────────────────────────

Set-Location $Root
$env:PYTHONPATH = $Root

Write-Host ""
Write-Host "Starting NeighborIQ API on http://localhost:$Port" -ForegroundColor Green
Write-Host "Dashboard: http://localhost:$Port" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""

python -m uvicorn neighboriq.api.server:app --host 0.0.0.0 --port $Port --reload
