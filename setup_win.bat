@echo off
chcp 65001 >nul
echo ============================================
echo   Folder Launcher Setup
echo ============================================
echo.

echo [1/3] Installing Python packages...
py -m pip install pystray pillow --quiet
if errorlevel 1 (
    echo ERROR: pip install failed
    pause
    exit /b 1
)
echo Done.
echo.

echo [2/3] Installing Windows Terminal...
where wt >/dev/null 2>&1
if errorlevel 1 (
    winget install Microsoft.WindowsTerminal --accept-source-agreements --accept-package-agreements
) else (
    echo Already installed.
)
echo.

echo [3/3] Setting light theme...
set "WT_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if exist "%WT_SETTINGS%" (
    py -c "import json,os;p=os.environ[\"WT_SETTINGS\"];d=json.load(open(p,encoding=\"utf-8\"));d[\"profiles\"][\"defaults\"][\"colorScheme\"]=\"One Half Light\";json.dump(d,open(p,\"w\",encoding=\"utf-8\"),indent=4,ensure_ascii=False);print(\"Light theme set.\")"
) else (
    echo Windows Terminal settings not found. Open WT once first, then re-run this script.
)
echo.

echo ============================================
echo   Setup complete!
echo   To launch: double-click folder_launcher_win.pyw
echo ============================================
pause
