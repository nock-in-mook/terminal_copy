@echo off
chcp 65001 >nul
title Folder Launcher Setup

:: Python検出（C:\Python314 → py コマンド → エラー）
set "PYTHON="
if exist "C:\Python314\python.exe" (
    set "PYTHON=C:\Python314\python.exe"
    set "PYTHONW=C:\Python314\pythonw.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        for /f "delims=" %%i in ('py -c "import sys; print(sys.executable)"') do set "PYTHON=%%i"
        for /f "delims=" %%i in ('py -c "import sys,os; print(os.path.join(os.path.dirname(sys.executable), \"pythonw.exe\"))"') do set "PYTHONW=%%i"
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

:: WT設定: ライトテーマ + suppressApplicationTitle
set "WT_SETTINGS=%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
if exist "%WT_SETTINGS%" (
    "%PYTHON%" -c "import json,os;p=os.environ['WT_SETTINGS'];d=json.load(open(p,encoding='utf-8'));df=d.setdefault('profiles',{}).setdefault('defaults',{});changed=False;exec(\"\"\"if df.get('colorScheme')!='One Half Light':\n df['colorScheme']='One Half Light';changed=True\nif not df.get('suppressApplicationTitle'):\n df['suppressApplicationTitle']=True;changed=True\"\"\")\nif changed:\n json.dump(d,open(p,'w',encoding='utf-8'),indent=4,ensure_ascii=False);print('WT settings updated')\nelse:\n print('WT settings OK')"
)

:: スタートアップにショートカット作成
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Folder Launcher.lnk"
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Folder Launcher.lnk"
if not exist "%STARTUP%" (
    powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%STARTUP%');$s.TargetPath='%PYTHONW%';$s.Arguments='%~dp0folder_launcher_win.pyw';$s.WorkingDirectory='%~dp0';$s.Save()"
    echo Startup shortcut created
)
if not exist "%STARTMENU%" (
    powershell -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%STARTMENU%');$s.TargetPath='%PYTHONW%';$s.Arguments='%~dp0folder_launcher_win.pyw';$s.WorkingDirectory='%~dp0';$s.Save()"
    echo Start Menu shortcut created
)

:: Launch
echo Starting Folder Launcher...
start "" "%PYTHONW%" "%~dp0folder_launcher_win.pyw"
