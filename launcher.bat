@echo off
chcp 65001 >nul

:: Check pystray (Python 3.14)
C:\Python314\python.exe -c "import pystray" >nul 2>&1
if errorlevel 1 (
    echo Installing packages...
    C:\Python314\python.exe -m pip install pystray pillow --quiet
)

:: Check Windows Terminal
where wt >nul 2>&1
if errorlevel 1 (
    echo Installing Windows Terminal...
    winget install Microsoft.WindowsTerminal --accept-source-agreements --accept-package-agreements
)

:: Set light theme if not set
set "WT_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if exist "%WT_SETTINGS%" (
    C:\Python314\python.exe -c "import json,os;p=os.environ['WT_SETTINGS'];d=json.load(open(p,encoding='utf-8'));c=d.get('profiles',{}).get('defaults',{}).get('colorScheme');exec(\"\"\"if c!='One Half Light':\n d.setdefault('profiles',{}).setdefault('defaults',{})['colorScheme']='One Half Light'\n json.dump(d,open(p,'w',encoding='utf-8'),indent=4,ensure_ascii=False)\"\"\")"
)

:: Launch
start "" C:\Python314\pythonw.exe "%~dp0folder_launcher_win.pyw"
