<# 
=============================================================================
DAOUFYS TRANSIT Voice Agent — PowerShell Startup Script
=============================================================================
Usage: Right-click → "Run with PowerShell" OR run from terminal:
  .\start_voice_agent.ps1
=============================================================================
#>

param(
    [switch]$InstallDeps,
    [switch]$EditEnv,
    [switch]$TestOnly
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ProjectDir

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  DAOUFYS TRANSIT — Voice AI Receptionist                         ║" -ForegroundColor Cyan
Write-Host "║  LiveKit Agents + Hermes Integration                                 ║" -ForegroundColor Cyan
Write-Host "║  Darija (Arabizi) #1 | French #2                                     ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check for uv
$uvPath = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvPath) {
    Write-Host "[ERROR] 'uv' not found in PATH." -ForegroundColor Red
    Write-Host "Install: curl -LsSf https://astral.sh/uv/install.sh | sh" -ForegroundColor Yellow
    Write-Host "Or: pip install uv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check/edit .env
if (-not (Test-Path ".env")) {
    Write-Host "[WARN] .env not found. Copying from config/.env.example..." -ForegroundColor Yellow
    if (Test-Path "config\.env.example") {
        Copy-Item "config\.env.example" ".env" -Force
        Write-Host ""
        Write-Host "[ACTION REQUIRED] Edit .env with your API keys before running!" -ForegroundColor Red
        Write-Host ""
        notepad .env
        Write-Host ""
    } else {
        Write-Host "[ERROR] config/.env.example not found!" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

if ($EditEnv) {
    notepad .env
    exit 0
}

# Install/sync dependencies
if ($InstallDeps -or -not (Test-Path ".venv")) {
    Write-Host "[INFO] Syncing dependencies with uv..." -ForegroundColor Green
    uv sync --all-extras
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Dependency install failed." -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

if ($TestOnly) {
    Write-Host "[INFO] Running tests..." -ForegroundColor Green
    uv run pytest tests/ -v
    Read-Host "Press Enter to exit"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[INFO] Starting DAOUFYS Voice Agent in console mode..." -ForegroundColor Green
Write-Host "[INFO] Press Ctrl+C to stop." -ForegroundColor Gray
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

try {
    uv run python -m agent.daoufys_receptionist console
} catch {
    Write-Host "[ERROR] Agent crashed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[INFO] Agent stopped." -ForegroundColor Gray
Read-Host "Press Enter to exit"