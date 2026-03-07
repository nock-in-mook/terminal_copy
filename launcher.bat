@echo off
chcp 65001 >nul
title Setup

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
    "%PYTHON%" -m pip install pystray pillow --quiet
)

:: Check Windows Terminal
where wt >nul 2>&1
if errorlevel 1 (
    echo Installing Windows Terminal...
    winget install Microsoft.WindowsTerminal --accept-source-agreements --accept-package-agreements
)

:: WT settings
set "WT_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
set "WT_SCRIPT=%~dp0_setup_wt.py"
if exist "%WT_SETTINGS%" (
    "%PYTHON%" "%WT_SCRIPT%"
)

:: Shortcuts
set "LAUNCHER_EXE=%~dp0即ランチャー.exe"
set "SCRIPT=%~dp0folder_launcher_win.pyw"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\即ランチャー.lnk"
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\即ランチャー.lnk"

:: Delete old shortcuts
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Folder Launcher.lnk" del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Folder Launcher.lnk"
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Folder Launcher.lnk" del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Folder Launcher.lnk"

if not exist "%STARTUP%" (
    powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%STARTUP%');$s.TargetPath='%LAUNCHER_EXE%';$s.Arguments='%SCRIPT%';$s.WorkingDirectory='%~dp0';$s.Save()"
    echo Startup shortcut created
)
if not exist "%STARTMENU%" (
    powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%STARTMENU%');$s.TargetPath='%LAUNCHER_EXE%';$s.Arguments='%SCRIPT%';$s.WorkingDirectory='%~dp0';$s.Save()"
    echo Start Menu shortcut created
)

:: Launch
echo Starting...
start "" "%LAUNCHER_EXE%" "%SCRIPT%"
