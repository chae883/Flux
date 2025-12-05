@echo off
REM Flux Pipeline Launcher for Nuke 16.0v3
REM Usage: Double click to launch default context. Or drag project folder onto this.

REM --- 1. CONFIGURATION ---
REM Configで設定した FLUX_ROOT と合わせる
set "FLUX_ROOT=D:\Studio\WIP"

REM Nukeの実行ファイルパス (環境に合わせて修正してください)
set "NUKE_PATH=C:\Program Files\Nuke16.0v3\Nuke16.0.exe"

REM --- 2. SET CONTEXT (DEFAULT) ---
REM 引数がない場合はデフォルトプロジェクト
if "%~1"=="" (
set "FLUX_PROJECT=TMP"
set "FLUX_SHOT=000_000"
) else (
REM ドラッグ＆ドロップ対応などはここで拡張可能
set "FLUX_PROJECT=%~1"
set "FLUX_SHOT=000_000"
)

REM --- 3. DISPLAY INFO ---
echo ==========================================
echo   FLUX PIPELINE LAUNCHER (Nuke 16)
echo ==========================================
echo   FLUX_ROOT    : %FLUX_ROOT%
echo   FLUX_PROJECT : %FLUX_PROJECT%
echo   FLUX_SHOT    : %FLUX_SHOT%
echo ==========================================
echo   Loading NukeX...

REM --- 4. LAUNCH NUKE X ---
"%NUKE_PATH%" --nukex