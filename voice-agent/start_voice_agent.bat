@echo off
REM =============================================================================
REM DAOUFYS TRANSIT Voice Agent — Windows Startup Script
REM =============================================================================
REM Usage: double-click this file OR run from cmd: start_voice_agent.bat
REM =============================================================================

set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║  DAOUFYS TRANSIT — Voice AI Receptionist                         ║
║  LiveKit Agents + Hermes Integration                                 ║
║  Darija (Arabizi) #1 | French #2                                     ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

REM Check for uv
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 'uv' not found in PATH.
    echo Install: curl -LsSf https://astral.sh/uv/install.sh ^| sh
    echo Or: pip install uv
    pause
    exit /b 1
)

REM Check for .env
if not exist ".env" (
    echo [WARN] .env not found. Copying from config/.env.example...
    if exist "config\.env.example" (
        copy config\.env.example .env
        echo.
        echo [ACTION REQUIRED] Edit .env with your API keys before running!
        echo.
        notepad .env
        echo.
    ) else (
        echo [ERROR] config/.env.example not found!
        pause
        exit /b 1
    )
)

REM Install/sync dependencies
echo [INFO] Syncing dependencies with uv...
uv sync --all-extras
if %errorlevel% neq 0 (
    echo [ERROR] Dependency install failed.
    pause
    exit /b 1
)

echo.
echo [INFO] Starting DAOUFYS Voice Agent in console mode...
echo [INFO] Press Ctrl+C to stop.
echo.
echo ═══════════════════════════════════════════════════════════════════
echo.

REM Run agent in console mode (text + voice)
uv run python -m agent.daoufys_receptionist console

echo.
echo [INFO] Agent stopped.
pause