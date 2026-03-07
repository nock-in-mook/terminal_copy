@echo off
chcp 65001 >nul

:: Check pystray
py -c "import pystray" >/dev/null 2>&1
if errorlevel 1 (
    echo Installing packages...
    py -m pip install pystray pillow --quiet
)

:: Check Windows Terminal
where wt >/dev/null 2>&1
if errorlevel 1 (
    echo Installing Windows Terminal...
    winget install Microsoft.WindowsTerminal --accept-source-agreements --accept-package-agreements
)

:: Set light theme if not set
set "WT_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if exist "%WT_SETTINGS%" (
    py -c "import json,os;p=os.environ[\"WT_SETTINGS\"];d=json.load(open(p,encoding=\"utf-8\"));c=d.get(\"profiles\",{}).get(\"defaults\",{}).get(\"colorScheme\");exec(\"\"\"if c!=\\\"One Half Light\\\":\n d.setdefault(\\\"profiles\\\",{}).setdefault(\\\"defaults\\\",{})[\\\"colorScheme\\\"]=\\\"One Half Light\\\"\n json.dump(d,open(p,\\\"w\\\",encoding=\\\"utf-8\\\"),indent=4,ensure_ascii=False)\"\"\")"
)

:: Launch
start "" py "%~dp0folder_launcher_win.pyw"
