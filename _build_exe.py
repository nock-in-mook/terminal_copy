"""即ランチャー.exeを生成: pythonw.exeをコピーしてアイコン・バージョン情報を書き換え"""
import os
import sys
import struct
import ctypes
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
for f in os.listdir(PYTHON_DIR):
    if f.startswith("python3") and f.endswith(".dll") and f != "python3.dll":
        DLLS.append(f)
        break

# pythonw.exe → 即ランチャー.exe（TEMP経由で日本語パス問題を回避）
TEMP_EXE = os.path.join(os.environ["TEMP"], "soku_launcher_build.exe")
print("Copying pythonw.exe...")
shutil.copy2(PYTHONW, TEMP_EXE)

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

# rceditダウンロード（アイコン設定用）
if not os.path.exists(RCEDIT_PATH):
    print("Downloading rcedit...")
    url = "https://github.com/electron/rcedit/releases/download/v2.0.0/rcedit-x64.exe"
    urllib.request.urlretrieve(url, RCEDIT_PATH)

# アイコン埋め込み（rceditはASCIIパスのTEMP_EXEに対して実行）
print("Setting icon...")
ico_tmp = os.path.join(os.environ["TEMP"], "app.ico")
shutil.copy2(ICO_PATH, ico_tmp)
subprocess.run([RCEDIT_PATH, TEMP_EXE, "--set-icon", ico_tmp], check=True)


# === バージョン情報をWin32 APIで書き換え（日本語対応） ===

def _align4(data):
    r = len(data) % 4
    return data + b'\x00' * (4 - r) if r else data

def _make_wstring(key, value):
    k = key.encode('utf-16-le') + b'\x00\x00'
    v = value.encode('utf-16-le') + b'\x00\x00'
    h = struct.pack('<HHH', 0, len(value) + 1, 1)
    d = h + k
    d = _align4(d)
    d += v
    d = _align4(d)
    return struct.pack('<H', len(d)) + d[2:]

def _make_string_table(lang_cp, strings):
    k = lang_cp.encode('utf-16-le') + b'\x00\x00'
    h = struct.pack('<HHH', 0, 0, 1)
    d = h + k
    d = _align4(d)
    for key, val in strings:
        d = _align4(d)
        d += _make_wstring(key, val)
    return struct.pack('<H', len(d)) + d[2:]

def _make_sfi(st_data):
    k = 'StringFileInfo'.encode('utf-16-le') + b'\x00\x00'
    h = struct.pack('<HHH', 0, 0, 1)
    d = h + k
    d = _align4(d)
    d += st_data
    return struct.pack('<H', len(d)) + d[2:]

def _make_vfi():
    k = 'VarFileInfo'.encode('utf-16-le') + b'\x00\x00'
    vk = 'Translation'.encode('utf-16-le') + b'\x00\x00'
    vv = struct.pack('<HH', 0x0409, 0x04b0)
    vh = struct.pack('<HHH', 0, len(vv), 0)
    vd = vh + vk
    vd = _align4(vd)
    vd += vv
    vd = _align4(vd)
    vd = struct.pack('<H', len(vd)) + vd[2:]
    h = struct.pack('<HHH', 0, 0, 1)
    d = h + k
    d = _align4(d)
    d += vd
    return struct.pack('<H', len(d)) + d[2:]

def build_version_info(strings):
    """VS_VERSION_INFOバイナリを構築"""
    ffi = struct.pack('<13I',
        0xFEEF04BD, 0x00010000,
        0x00010000, 0, 0x00010000, 0,
        0x3F, 0, 0x00040004, 1, 0, 0, 0)
    k = 'VS_VERSION_INFO'.encode('utf-16-le') + b'\x00\x00'
    h = struct.pack('<HHH', 0, len(ffi), 0)
    d = h + k
    d = _align4(d)
    d += ffi
    d = _align4(d)
    d += _make_sfi(_make_string_table('040904b0', strings))
    d = _align4(d)
    d += _make_vfi()
    d = _align4(d)
    return struct.pack('<H', len(d)) + d[2:]

print("Setting version info...")
vi_data = build_version_info([
    ('CompanyName', ''),
    ('FileDescription', '即ランチャー'),
    ('FileVersion', '1.0.0'),
    ('InternalName', 'SokuLauncher'),
    ('OriginalFilename', '即ランチャー.exe'),
    ('ProductName', '即ランチャー'),
    ('ProductVersion', '1.0.0'),
])

kernel32 = ctypes.windll.kernel32
kernel32.BeginUpdateResourceW.argtypes = [ctypes.c_wchar_p, ctypes.c_bool]
kernel32.BeginUpdateResourceW.restype = ctypes.c_void_p
kernel32.UpdateResourceW.argtypes = [
    ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
    ctypes.c_ushort, ctypes.c_void_p, ctypes.c_uint]
kernel32.UpdateResourceW.restype = ctypes.c_bool
kernel32.EndUpdateResourceW.argtypes = [ctypes.c_void_p, ctypes.c_bool]
kernel32.EndUpdateResourceW.restype = ctypes.c_bool

handle = kernel32.BeginUpdateResourceW(TEMP_EXE, False)
if not handle:
    print(f"ERROR: BeginUpdateResource failed ({ctypes.GetLastError()})")
    sys.exit(1)

buf = ctypes.create_string_buffer(vi_data)
# RT_VERSION=16, ID=1, 既存と同じ言語0x0409で上書き
ok = kernel32.UpdateResourceW(handle, 16, 1, 0x0409, buf, len(vi_data))
if not ok:
    print(f"WARNING: UpdateResource failed ({ctypes.GetLastError()})")

ok = kernel32.EndUpdateResourceW(handle, False)
if not ok:
    print(f"ERROR: EndUpdateResource failed ({ctypes.GetLastError()})")
    sys.exit(1)

# TEMP → 最終パスにコピー
shutil.copy2(TEMP_EXE, EXE_PATH)
print(f"Done: {EXE_PATH}")
