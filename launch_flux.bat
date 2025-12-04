@echo off
REM Flux Pipeline Launcher for Windows
REM Usage: launch_flux.bat [Project] [Shot]
REM Example: launch_flux.bat TMP 101_010

REM --- 1. Pipeline Configuration ---
set "FLUX_ROOT=D:\Studio\WIP"
set "NUKE_PATH=C:\Program Files\Nuke15.0v4\Nuke15.0.exe"

REM --- 2. Set Context ---
if "%~1"=="" (
echo [Flux] No Project specified. Launching in Default Context.
set "FLUX_PROJECT=TMP"
set "FLUX_SHOT=000_000"
) else (
set "FLUX_PROJECT=%~1"
set "FLUX_SHOT=%~2"
)

echo ==========================================
echo   FLUX PIPELINE LAUNCHER
echo ==========================================
echo   ROOT    : %FLUX_ROOT%
echo   PROJECT : %FLUX_PROJECT%
echo   SHOT    : %FLUX_SHOT%
echo ==========================================

REM --- 3. Launch Nuke ---
"%NUKE_PATH%" --nukex