"""即ランチャー.exeを生成: pythonw.exeをコピーしてアイコン・バージョン情報を書き換え"""
import os
import sys
import shutil
import subprocess
import urllib.request

DIR = os.path.dirname(os.path.abspath(__file__))
EXE_PATH = os.path.join(DIR, "即ランチャー.exe")
ICO_PATH = os.path.join(DIR, "app.ico")
RCEDIT_PATH = os.path.join(os.environ["TEMP"], "rcedit.exe")

# pythonw.exeの場所
PYTHONW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(PYTHONW):
    print(f"ERROR: pythonw.exe not found at {PYTHONW}")
    sys.exit(1)

# 必要なDLL
PYTHON_DIR = os.path.dirname(sys.executable)
DLLS = ["python3.dll"]
# python3XX.dll を探す
for f in os.listdir(PYTHON_DIR):
    if f.startswith("python3") and f.endswith(".dll") and f != "python3.dll":
        DLLS.append(f)
        break

# pythonw.exe → 即ランチャー.exe
print("Copying pythonw.exe...")
shutil.copy2(PYTHONW, EXE_PATH)

# DLLをコピー
for dll in DLLS:
    src = os.path.join(PYTHON_DIR, dll)
    dst = os.path.join(DIR, dll)
    if os.path.exists(src):
        shutil.copy2(src, dst)

# _pthファイル生成
pth_name = [d for d in DLLS if d != "python3.dll"][0].replace(".dll", "._pth")
pth_path = os.path.join(DIR, pth_name)
with open(pth_path, "w", encoding="utf-8") as f:
    f.write(f"{PYTHON_DIR}\\Lib\n")
    f.write(f"{PYTHON_DIR}\\DLLs\n")
    f.write(f"{PYTHON_DIR}\\Lib\\site-packages\n")
    f.write(f"{PYTHON_DIR}\n")
    f.write("import site\n")

# rceditダウンロード（なければ）
if not os.path.exists(RCEDIT_PATH):
    print("Downloading rcedit...")
    url = "https://github.com/electron/rcedit/releases/download/v2.0.0/rcedit-x64.exe"
    urllib.request.urlretrieve(url, RCEDIT_PATH)

# アイコン埋め込み
print("Setting icon...")
subprocess.run([RCEDIT_PATH, EXE_PATH, "--set-icon", ICO_PATH], check=True)

# バージョン情報書き換え
print("Setting version info...")
version_strings = {
    "FileDescription": "即ランチャー",
    "ProductName": "即ランチャー",
    "OriginalFilename": "即ランチャー.exe",
    "CompanyName": "",
}
for key, val in version_strings.items():
    r = subprocess.run([RCEDIT_PATH, EXE_PATH, "--set-version-string", key, val],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  Warning: {key} failed (non-critical)")

print("Done: 即ランチャー.exe ready")
