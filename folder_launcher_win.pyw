#!/usr/bin/env python3
# folder_launcher_win.pyw
# 即ランチャー（Windows版）：システムトレイ常駐
# - OPEN サブメニューからフォルダ選択 → 即起動
# - 最大3ウィンドウ制限、Show All、Close All

import os
import sys
import subprocess
import threading
import ctypes
import ctypes.wintypes
import time

# Tcl/Tkライブラリのパス設定（即ランチャー.exeから起動時に必要）
for _d in [os.path.dirname(sys.executable)] + sys.path:
    _tcl_dir = os.path.join(_d, "tcl")
    if os.path.isdir(os.path.join(_tcl_dir, "tcl8.6")):
        os.environ.setdefault("TCL_LIBRARY", os.path.join(_tcl_dir, "tcl8.6"))
        os.environ.setdefault("TK_LIBRARY", os.path.join(_tcl_dir, "tk8.6"))
        break

import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw

# 多重起動防止（Windows Mutex）
_mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "SokuLauncher_Mutex")
if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
    sys.exit(0)

# タスクトレイ等でのアプリ名を「即ランチャー」にする（pythonw.exe表示を防ぐ）
APP_ID = "SokuLauncher.即ランチャー"
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)

# DPIスケーリング: 呼ばない方がMoveWindowの論理座標でWTを狭くできる

# 監視対象の親ディレクトリ
APPS_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "Google ドライブ", "_Apps2026")
if not os.path.isdir(APPS_DIR):
    APPS_DIR = r"G:\マイドライブ\_Apps2026"

# 透明キーボードと同じ配置定数
SCREEN_USE_RATIO = 0.95
MARGIN_TOP_RATIO = 0.0
MARGIN_BOTTOM_RATIO = 0.20  # キーボード領域を確保
SHADOW_OVERLAP = 14
SHADOW_INSET = 7  # ウィンドウ影の片側幅
MAX_TERMINALS = 3
KB_HEIGHT_RATIO = 0.20  # キーボード高さ = 画面の20%

# 透明キーボードのパス
KB_DIR = os.path.join(APPS_DIR, "透明キーボード")
KB_EXE = os.path.join(KB_DIR, "透明キーボード.exe")
KB_SCRIPT = os.path.join(KB_DIR, "transparent_keyboard.py")


GDRIVE_DIR = os.path.dirname(APPS_DIR)  # マイドライブ直下
OTHER_PROJECTS_DIR = os.path.join(GDRIVE_DIR, "_other-projects")


def get_folders():
    """フォルダ一覧を取得（_other-projects内も含む）"""
    try:
        entries = sorted(os.listdir(APPS_DIR), key=str.lower)
        # 除外フォルダ
        exclude = {'images', 'text', 'テレパシーワード', 'others', '_other_projects'}
        folders = [e for e in entries
                   if not e.startswith('.') and e not in exclude
                   and os.path.isdir(os.path.join(APPS_DIR, e))]
        # マイドライブ直下の_other-projects内のサブフォルダも追加
        if os.path.isdir(OTHER_PROJECTS_DIR):
            for e in sorted(os.listdir(OTHER_PROJECTS_DIR), key=str.lower):
                if not e.startswith('.') and os.path.isdir(os.path.join(OTHER_PROJECTS_DIR, e)):
                    folders.append(e)
            folders.sort(key=str.lower)
        return folders
    except OSError:
        return []


def resolve_folder_path(name):
    """フォルダ名からフルパスを解決（_other-projects内も探す）"""
    direct = os.path.join(APPS_DIR, name)
    if os.path.isdir(direct):
        return direct
    other = os.path.join(OTHER_PROJECTS_DIR, name)
    if os.path.isdir(other):
        return other
    return direct  # フォールバック


def _calc_layout():
    """透明キーボードと同じ計算式でレイアウト情報を返す"""
    user32 = ctypes.windll.user32
    sw = user32.GetSystemMetrics(0)
    # 作業領域（タスクバーを除いた領域）
    work_rect = ctypes.wintypes.RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work_rect), 0)
    work_top = work_rect.top
    work_h = work_rect.bottom - work_rect.top
    # 幅は画面全体ベース
    total_w = int(sw * SCREEN_USE_RATIO)
    win_w = (total_w + SHADOW_OVERLAP * (MAX_TERMINALS - 1)) // MAX_TERMINALS
    # 高さは作業領域ベース
    margin_top = int(work_h * MARGIN_TOP_RATIO) + work_top
    term_h = work_h - int(work_h * MARGIN_TOP_RATIO) - int(work_h * MARGIN_BOTTOM_RATIO)
    kb_h = int(work_h * KB_HEIGHT_RATIO) + SHADOW_INSET
    return sw, work_h, win_w, margin_top, term_h, kb_h, work_top


def _find_kb_windows():
    """透明キーボードのウィンドウハンドルを全て取得"""
    user32 = ctypes.windll.user32
    hwnds = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    def enum_callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            title_buf = ctypes.create_unicode_buffer(256)
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetWindowTextW(hwnd, title_buf, 256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if title_buf.value == '透明キーボード' and cls_buf.value == 'TkTopLevel':
                hwnds.append(hwnd)
        return True

    user32.EnumWindows(enum_callback, 0)
    return hwnds


def _reposition_windows():
    """ターミナル+キーボードを整列（透明キーボードの_realign_allと同じロジック）"""
    user32 = ctypes.windll.user32
    sw, work_h, win_w, margin_top, term_h, kb_h, work_top = _calc_layout()

    # ターミナルを検出してx座標でソート
    wt_hwnds = _find_wt_windows()[:MAX_TERMINALS]
    rect = ctypes.wintypes.RECT()
    wt_sorted = []
    for hwnd in wt_hwnds:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        wt_sorted.append((rect.left, hwnd))
    wt_sorted.sort(key=lambda r: r[0])

    # キーボードを検出してx座標でソート
    kb_sorted = []
    for hwnd in _find_kb_windows():
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        kb_sorted.append((rect.left, hwnd))
    kb_sorted.sort(key=lambda r: r[0])

    n_wt = len(wt_sorted)

    # ターミナルを右寄せで再配置（右の影を画面外に押し出す）
    x = sw + SHADOW_INSET
    wt_positions = []
    for i in range(n_wt - 1, -1, -1):
        x -= win_w
        if i < n_wt - 1:
            x += SHADOW_OVERLAP
        _, hwnd = wt_sorted[i]
        user32.MoveWindow(hwnd, x, margin_top, win_w, term_h, True)
        wt_positions.insert(0, x)

    # キーボードを配置（ターミナルの真下、影に食い込ませる）
    kb_w = win_w - SHADOW_INSET * 2
    kb_y = margin_top + term_h - SHADOW_INSET
    for i, (_, hwnd) in enumerate(kb_sorted):
        if i < n_wt:
            kx = wt_positions[i] + SHADOW_INSET
        else:
            if n_wt > 0:
                kx = wt_positions[0] + SHADOW_INSET - kb_w
                extra = i - n_wt
                kx -= extra * kb_w
            else:
                kx = sw - kb_w - i * kb_w
        user32.MoveWindow(hwnd, kx, kb_y, kb_w, kb_h, True)


def _launch_keyboard():
    """透明キーボードを1つ起動（既にMAX_TERMINALS個あればスキップ）"""
    existing = len(_find_kb_windows())
    if existing >= MAX_TERMINALS:
        return
    if not os.path.exists(KB_SCRIPT):
        return
    # pyコマンド（Pythonランチャー）でスクリプトを直接実行
    # 透明キーボード.exeはランタイムDLL不足でtkinterが使えないため
    subprocess.Popen(['py', '-3', KB_SCRIPT], cwd=KB_DIR,
                     creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)


def open_terminals(folder_names):
    """Windows Terminalウィンドウを起動し、透明キーボードも同時起動して整列"""
    if not folder_names:
        return

    # 起動前のWTウィンドウを記録
    before_hwnds = set(_find_wt_windows())
    n = len(folder_names)

    # 新しいターミナルを起動（タブタイトル設定 + Claude自動起動）
    for name in folder_names:
        full_path = resolve_folder_path(name)
        env = os.environ.copy()
        env.pop('CLAUDECODE', None)
        subprocess.Popen(['wt', '--title', name, '-d', full_path, 'cmd', '/k', 'claude --dangerously-skip-permissions'],
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                         env=env)
        # 透明キーボードも一緒に起動
        _launch_keyboard()
        time.sleep(0.5)

    # 新しいウィンドウが出揃うのを待つ
    for _ in range(20):
        time.sleep(0.3)
        current = set(_find_wt_windows())
        new_hwnds = list(current - before_hwnds)
        if len(new_hwnds) >= n:
            break

    # キーボードが出揃うのも少し待つ
    time.sleep(0.5)
    _reposition_windows()


def _find_wt_windows():
    """Windows Terminalのトップレベルウィンドウハンドルを全て取得"""
    user32 = ctypes.windll.user32
    hwnds = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    def enum_callback(hwnd, lparam):
        if user32.IsWindowVisible(hwnd):
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if 'CASCADIA_HOSTING_WINDOW_CLASS' in cls_buf.value:
                hwnds.append(hwnd)
        return True

    user32.EnumWindows(enum_callback, 0)
    return hwnds


def bring_terminals_to_front():
    """全WTウィンドウを再配置して最前面に出す"""
    _reposition_windows()
    user32 = ctypes.windll.user32
    hwnds = _find_wt_windows()
    for hwnd in reversed(hwnds):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.05)


def close_all_terminals():
    """全WTウィンドウを閉じる"""
    user32 = ctypes.windll.user32
    hwnds = _find_wt_windows()
    WM_CLOSE = 0x0010
    for hwnd in hwnds:
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)


def make_icon():
    """トレイアイコン画像を生成（高解像度）"""
    size = 256
    img = Image.new('RGBA', (size, size), (0, 120, 212, 255))
    draw = ImageDraw.Draw(img)
    s = size / 64
    draw.rectangle([int(8*s), int(20*s), int(56*s), int(52*s)],
                    fill=(255, 200, 50, 255), outline=(200, 150, 0, 255), width=int(3*s))
    draw.rectangle([int(8*s), int(14*s), int(28*s), int(24*s)],
                    fill=(255, 200, 50, 255), outline=(200, 150, 0, 255), width=int(3*s))
    return img


# === メインアプリ ===

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.icon = pystray.Icon("即ランチャー", make_icon(), "即ランチャー", self._build_menu())
        self.icon.HAS_DEFAULT_ACTION = False
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _open_single(self, folder_name):
        """シングル起動: 既存WT数チェック後、1つ起動して再配置"""
        current_count = len(_find_wt_windows())
        if current_count >= MAX_TERMINALS:
            self.root.after(0, lambda: messagebox.showwarning("即ランチャー",
                f"Already {current_count} terminals open (max {MAX_TERMINALS}).\n"
                f"Close some terminals first."))
            return
        open_terminals([folder_name])

    def _close_all(self):
        """Close All: 確認2回してから全WT閉じる"""
        def do_close():
            count = len(_find_wt_windows())
            if count == 0:
                messagebox.showinfo("即ランチャー", "No terminals open.")
                return
            r1 = messagebox.askyesno("即ランチャー",
                f"Close all {count} terminal(s)?")
            if not r1:
                return
            r2 = messagebox.askyesno("即ランチャー",
                f"Are you sure? All unsaved work will be lost.")
            if not r2:
                return
            close_all_terminals()
        self.root.after(0, do_close)

    # === トレイメニュー ===

    def _build_menu(self):
        folders = get_folders()
        items = []

        # OPEN → サブメニューでフォルダ一覧
        open_items = []
        for name in folders:
            open_items.append(pystray.MenuItem(name, self._make_single_callback(name)))
        items.append(pystray.MenuItem("OPEN", pystray.Menu(*open_items)))
        items.append(pystray.Menu.SEPARATOR)

        # Show All
        items.append(pystray.MenuItem("Show All", lambda: bring_terminals_to_front()))
        items.append(pystray.Menu.SEPARATOR)

        # Refresh, Close All, Quit
        items.append(pystray.MenuItem("Refresh", lambda: self._rebuild_menu()))
        items.append(pystray.MenuItem("Close All", lambda: self._close_all()))
        items.append(pystray.MenuItem("Quit", lambda: self._quit()))
        return pystray.Menu(*items)

    def _make_single_callback(self, name):
        def callback():
            threading.Thread(target=lambda: self._open_single(name), daemon=True).start()
        return callback

    def _rebuild_menu(self):
        self.icon.menu = self._build_menu()

    def _quit(self):
        def do_quit():
            if messagebox.askyesno("即ランチャー", "Quit Folder Launcher?"):
                self.icon.stop()
                self.root.destroy()
        self.root.after(0, do_quit)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    # --show-all モード: 全ターミナルを再配置＋最前面に出して終了
    if "--show-all" in sys.argv:
        bring_terminals_to_front()
        sys.exit(0)
    App().run()
