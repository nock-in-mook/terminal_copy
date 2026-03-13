@echo off
chcp 65001 >nul
title Setup

:: Stop existing processes (Mutex release for new instance)
taskkill /f /im "即ランチャー.exe" >nul 2>&1
taskkill /f /im "透明キーボード.exe" >nul 2>&1
timeout /t 1 /nobreak >nul
echo Stopped existing processes.

:: Python
set "PYTHON="
if exist "C:\Python314\python.exe" (
    set "PYTHON=C:\Python314\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%i in ('py -c "import sys; print(sys.executable)"') do set "PYTHON=%%i"
    )
)
if "%PYTHON%"=="" (
    echo Python not found. Install Python first.
    pause
    exit /b 1
)
echo Python: %PYTHON%

:: Check pystray
"%PYTHON%" -c "import pystray" >nul 2>&1
if errorlevel 1 (
    echo Installing packages...
    "%PYTHON%" -m pip install pystray pillow pefile pyinstaller --quiet
)

:: Check Windows Terminal
where wt >nul 2>&1
if errorlevel 1 (
    echo Installing Windows Terminal...
    winget install Microsoft.WindowsTerminal --accept-source-agreements --accept-package-agreements
)

:: WT settings
set "WT_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if exist "%WT_SETTINGS%" (
    "%PYTHON%" "%~dp0_setup_wt.py"
)

:: Build exe（毎回再生成して最新状態を保証）
set "LAUNCHER_EXE=%~dp0即ランチャー.exe"
echo Building launcher exe...
set "PYTHONUTF8=1"
"%PYTHON%" "%~dp0_build_exe.py"

:: Build keyboard exe（透明キーボードも即ランチャーに統合）
set "KB_DIR=%~dp0..\透明キーボード"
if exist "%KB_DIR%\transparent_keyboard.py" (
    echo Building keyboard exe...
    "%PYTHON%" -m PyInstaller --noconfirm "%KB_DIR%\透明キーボード.spec" --distpath "%KB_DIR%\dist" --workpath "%KB_DIR%\build" >nul 2>&1
    if exist "%KB_DIR%\dist\透明キーボード.exe" (
        copy /y "%KB_DIR%\dist\透明キーボード.exe" "%KB_DIR%\透明キーボード.exe" >nul
        echo   Keyboard exe updated.
    ) else (
        echo   WARNING: Keyboard exe build failed.
    )
)

:: Shortcuts + Launch（日本語パス対応のためPythonで実行）
set "PYTHONUTF8=1"
"%PYTHON%" "%~dp0_setup_shortcuts.py"
echo.
echo Done. Press any key to close.
pause >nul
