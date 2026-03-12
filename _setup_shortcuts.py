"""ショートカット作成＆即ランチャー起動（日本語パス対応）"""
import os
import sys
import subprocess
import tempfile

DIR = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(DIR, "即ランチャー.exe")
PYW_PATH = os.path.join(DIR, "folder_launcher_win.pyw")
ICO_PATH = os.path.join(DIR, "app.ico")

APPDATA = os.environ["APPDATA"]
STARTUP_LNK = os.path.join(APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", "即ランチャー.lnk")
STARTMENU_LNK = os.path.join(APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "即ランチャー.lnk")

# 旧名ショートカットを削除
for old_name in ["Folder Launcher.lnk"]:
    for d in ["Startup", ""]:
        old = os.path.join(APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", d, old_name).rstrip("\\")
        if os.path.exists(old):
            os.remove(old)
            print(f"Deleted old: {old}")

# 透明キーボードのスタートアップを削除（即ランチャーが制御するため単体起動不要）
for kb_name in ["透明キーボード.lnk"]:
    kb_startup = os.path.join(APPDATA, "Microsoft", "Windows", "Start Menu", "Programs", "Startup", kb_name)
    if os.path.exists(kb_startup):
        os.remove(kb_startup)
        print(f"Removed keyboard startup: {kb_startup}")

# PowerShellスクリプトをファイル経由で実行（bashの$エスケープ問題回避）
ps_script = f'''
$shell = New-Object -ComObject WScript.Shell
foreach ($lnk in @('{STARTUP_LNK}', '{STARTMENU_LNK}')) {{
    $s = $shell.CreateShortcut($lnk)
    $s.TargetPath = '{EXE_PATH}'
    $s.Arguments = '"{PYW_PATH}"'
    $s.WorkingDirectory = '{DIR}'
    $s.IconLocation = '{ICO_PATH},0'
    $s.Save()
}}
'''

ps_file = os.path.join(tempfile.gettempdir(), "soku_shortcuts.ps1")
with open(ps_file, "w", encoding="utf-8-sig") as f:
    f.write(ps_script)

result = subprocess.run(
    ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ps_file],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"WARNING: PowerShell error: {result.stderr}")
else:
    print("Startup shortcut updated")
    print("Start Menu shortcut updated")

# 即ランチャー起動
print("Starting...")
subprocess.Popen(
    [EXE_PATH, PYW_PATH],
    creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
)
