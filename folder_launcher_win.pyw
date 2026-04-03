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
import logging
import traceback

# デバッグログ
_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'launcher_debug.log')
logging.basicConfig(filename=_log_path, level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    encoding='utf-8')

# DPI Aware（くっきり表示 — Windows DPIスケーリングによるぼやけを防止）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI Aware V2
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

def _get_dpi_scale():
    """DPIスケール取得（96dpi=1.0, 120dpi=1.25, 144dpi=1.5）"""
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)  # LOGPIXELSX
        ctypes.windll.user32.ReleaseDC(0, hdc)
        return dpi / 96.0
    except Exception:
        return 1.0

DPI_SCALE = _get_dpi_scale()

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

# 監視対象の親ディレクトリ
APPS_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "Google ドライブ", "_Apps2026")
if not os.path.isdir(APPS_DIR):
    APPS_DIR = r"G:\マイドライブ\_Apps2026"

# 透明キーボードと同じ配置定数
SCREEN_USE_RATIO = 0.95
MARGIN_TOP_RATIO = 0.0
MARGIN_BOTTOM_RATIO = 0.20  # キーボード領域を確保
SHADOW_OVERLAP = round(14 * DPI_SCALE)
SHADOW_INSET = round(7 * DPI_SCALE)  # ウィンドウ影の片側幅
MAX_TERMINALS = 3
KB_HEIGHT_RATIO = 0.20  # キーボード高さ = 画面の20%

# 透明キーボードのパス
KB_DIR = os.path.join(APPS_DIR, "透明キーボード")
KB_EXE = os.path.join(KB_DIR, "透明キーボード.exe")
KB_SCRIPT = os.path.join(KB_DIR, "transparent_keyboard.py")


GDRIVE_DIR = os.path.dirname(APPS_DIR)  # マイドライブ直下
OTHER_PROJECTS_DIR = os.path.join(GDRIVE_DIR, "_other-projects")


def get_folders():
    """フォルダ一覧を取得（_Apps2026内とother-projects内を分けて返す）
    戻り値: (apps_folders, other_folders) のタプル
    """
    try:
        entries = sorted(os.listdir(APPS_DIR), key=str.lower)
        exclude = {'images', 'text', 'テレパシーワード', 'others', '_other_projects', '即Claude'}
        apps_folders = sorted([e for e in entries
                   if not e.startswith('.') and e not in exclude
                   and os.path.isdir(os.path.join(APPS_DIR, e))], key=str.lower)
        # マイドライブ直下の_other-projects内のサブフォルダ
        other_folders = []
        if os.path.isdir(OTHER_PROJECTS_DIR):
            other_folders = sorted([e for e in os.listdir(OTHER_PROJECTS_DIR)
                        if not e.startswith('.') and os.path.isdir(os.path.join(OTHER_PROJECTS_DIR, e))],
                       key=str.lower)
        logging.debug(f"get_folders: apps={len(apps_folders)}件, other={len(other_folders)}件")
        return apps_folders, other_folders
    except Exception:
        logging.error(f"get_folders でエラー:\n{traceback.format_exc()}")
        return [], []


def resolve_folder_path(name):
    """フォルダ名からフルパスを解決（_other-projects内も探す）"""
    direct = os.path.join(APPS_DIR, name)
    if os.path.isdir(direct):
        return direct
    other = os.path.join(OTHER_PROJECTS_DIR, name)
    if os.path.isdir(other):
        return other
    return direct  # フォールバック


def _find_desktop_listview():
    """デスクトップのSysListView32ハンドルを取得（アイコン選択状態の確認用）"""
    user32 = ctypes.windll.user32
    # Progman > SHELLDLL_DefView > SysListView32 の階層
    progman = user32.FindWindowW("Progman", None)
    if progman:
        defview = user32.FindWindowExW(progman, 0, "SHELLDLL_DefView", None)
        if defview:
            lv = user32.FindWindowExW(defview, 0, "SysListView32", None)
            if lv:
                return lv
    # WorkerWフォールバック（壁紙スライドショー時はProgman直下にない）
    workerw = 0
    while True:
        workerw = user32.FindWindowExW(0, workerw, "WorkerW", None)
        if not workerw:
            break
        defview = user32.FindWindowExW(workerw, 0, "SHELLDLL_DefView", None)
        if defview:
            lv = user32.FindWindowExW(defview, 0, "SysListView32", None)
            if lv:
                return lv
    return 0


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


def _launch_one_keyboard():
    """透明キーボードを1つ起動（EXEはTcl同梱なので環境変数の影響を受けない）"""
    if os.path.exists(KB_EXE):
        subprocess.Popen([KB_EXE], cwd=KB_DIR,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    elif os.path.exists(KB_SCRIPT):
        env = os.environ.copy()
        env.pop('TCL_LIBRARY', None)
        env.pop('TK_LIBRARY', None)
        subprocess.Popen(['py', '-3.14', KB_SCRIPT], cwd=KB_DIR, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW)


def _close_one_keyboard(hwnd):
    """透明キーボードを1つ閉じる"""
    ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE


def _launch_keyboards_exact(target_count):
    """キーボードをぴったりtarget_count個にする（バックグラウンド用）"""
    n_kb = len(_find_kb_windows())
    need = target_count - n_kb
    logging.debug(f"キーボード同期: 現在{n_kb}個, 目標{target_count}個, 起動{max(need,0)}個")
    if need > 0:
        for _ in range(need):
            _launch_one_keyboard()
        # 揃うまで待つ（最大20秒）
        for _ in range(200):
            time.sleep(0.1)
            if len(_find_kb_windows()) >= target_count:
                break
    # 多すぎたら閉じる
    kb_hwnds = _find_kb_windows()
    excess = len(kb_hwnds) - target_count
    if excess > 0:
        logging.debug(f"キーボード過多: {len(kb_hwnds)}個 > {target_count}個, {excess}個閉じる")
        for i in range(excess):
            _close_one_keyboard(kb_hwnds[-(i + 1)])
    logging.debug(f"キーボード同期完了: {len(_find_kb_windows())}個")


def open_terminals(folder_names):
    """Windows Terminalウィンドウを起動し、透明キーボードも同時起動して整列"""
    if not folder_names:
        return

    # 起動後の合計WT数を事前計算
    before_hwnds = set(_find_wt_windows())
    target_wt = len(before_hwnds) + len(folder_names)
    n = len(folder_names)

    # 新しいターミナルを起動（タブタイトル設定 + Claude自動起動）
    for name in folder_names:
        full_path = resolve_folder_path(name)
        logging.debug(f"open_terminals: name={name!r}, path={full_path!r}, exists={os.path.isdir(full_path)}")
        env = os.environ.copy()
        env.pop('CLAUDECODE', None)
        env['CLAUDE_CODE_NO_FLICKER'] = '1'
        try:
            subprocess.Popen(['wt', '--title', name, '-d', full_path, 'cmd', '/k', 'claude --dangerously-skip-permissions'],
                             creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                             env=env)
            logging.debug(f"open_terminals: wt起動成功 {name!r}")
        except FileNotFoundError:
            logging.error("open_terminals: 'wt' が見つからない — フルパスで再試行")
            # Microsoft Store版WTのフルパス
            wt_path = os.path.join(os.environ.get('LOCALAPPDATA', ''),
                                   'Microsoft', 'WindowsApps', 'wt.exe')
            if os.path.exists(wt_path):
                subprocess.Popen([wt_path, '--title', name, '-d', full_path, 'cmd', '/k', 'claude --dangerously-skip-permissions'],
                                 creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                                 env=env)
                logging.debug(f"open_terminals: フルパスwt起動成功 {name!r}")
            else:
                logging.error(f"open_terminals: wt.exeが見つかりません: {wt_path}")
                raise
        except Exception:
            logging.error(f"open_terminals: 起動エラー:\n{traceback.format_exc()}")
            raise
        time.sleep(0.5)

    # 新しいウィンドウが出揃うのを待つ
    for _ in range(20):
        time.sleep(0.3)
        current = set(_find_wt_windows())
        new_hwnds = list(current - before_hwnds)
        if len(new_hwnds) >= n:
            break

    # ターミナルだけ先に整列（体感速度優先）
    _reposition_windows()

    # キーボードはバックグラウンドで目標数ぴったりに合わせる
    def _bg():
        _launch_keyboards_exact(target_wt)
        _reposition_windows()
    threading.Thread(target=_bg, daemon=True).start()


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
    """全WTウィンドウを再配置して最前面に出す（キーボード同期はバックグラウンド）"""
    _reposition_windows()
    user32 = ctypes.windll.user32
    hwnds = _find_wt_windows()
    target_wt = len(hwnds)
    for hwnd in reversed(hwnds):
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.05)
    # キーボードはバックグラウンドでWT数にぴったり合わせる
    def _bg():
        _launch_keyboards_exact(target_wt)
        _reposition_windows()
    threading.Thread(target=_bg, daemon=True).start()


def close_all_terminals():
    """全WTウィンドウ＋全キーボードを閉じる"""
    user32 = ctypes.windll.user32
    WM_CLOSE = 0x0010
    for hwnd in _find_wt_windows():
        user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
    for hwnd in _find_kb_windows():
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


# === デスクトップダブルクリック検出 ===

# Win32 API argtypes設定（64bit環境で正しく引数を渡す）
ctypes.windll.user32.WindowFromPoint.argtypes = [ctypes.wintypes.POINT]
ctypes.windll.user32.WindowFromPoint.restype = ctypes.wintypes.HWND
ctypes.windll.user32.CallNextHookEx.argtypes = [
    ctypes.wintypes.HHOOK, ctypes.c_int, ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM]
ctypes.windll.user32.CallNextHookEx.restype = ctypes.c_long


class DesktopClickDetector:
    """デスクトップの空白部分のダブルクリックを検出してコールバックを呼ぶ"""
    WH_MOUSE_LL = 14
    WM_LBUTTONDOWN = 0x0201

    class MSLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("pt", ctypes.wintypes.POINT),
            ("mouseData", ctypes.wintypes.DWORD),
            ("flags", ctypes.wintypes.DWORD),
            ("time", ctypes.wintypes.DWORD),
            ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
        ]

    def __init__(self, on_desktop_dblclick, on_any_click=None):
        self.on_desktop_dblclick = on_desktop_dblclick
        self.on_any_click = on_any_click
        self._last_click_time = 0
        self._last_click_pos = (0, 0)
        self._hook = None
        # フック→メインスレッド通信用フラグ（フック内では値セットのみ）
        self._pending_click = False
        self._pending_dblclick = None  # (x, y) or None
        # コールバック参照保持（GC防止）
        self._hook_proc = ctypes.WINFUNCTYPE(
            ctypes.c_long, ctypes.c_int,
            ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM
        )(self._low_level_mouse_proc)

    def _check_desktop_and_fire(self, x, y):
        """フック外でデスクトップ判定を行う（SendMessageWがブロックしてもフックに影響しない）"""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.WindowFromPoint(ctypes.wintypes.POINT(x, y))
            cls_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, cls_buf, 256)
            if cls_buf.value in ("WorkerW", "Progman", "SysListView32", "SHELLDLL_DefView"):
                # アイコン上ではないか判定（LVM_GETSELECTEDCOUNT）
                lv = _find_desktop_listview()
                if lv:
                    # タイムアウト付きでExplorerに問い合わせ（最大200ms）
                    result = ctypes.wintypes.DWORD(0)
                    ok = user32.SendMessageTimeoutW(
                        lv, 0x1032, 0, 0,
                        0x0002,  # SMTO_ABORTIFHUNG
                        200,     # タイムアウト200ms
                        ctypes.byref(result))
                    if ok and result.value == 0:
                        logging.debug(f"デスクトップダブルクリック検出: ({x}, {y})")
                        self.on_desktop_dblclick(x, y)
        except Exception:
            logging.error(f"デスクトップ判定エラー:\n{traceback.format_exc()}")

    def _low_level_mouse_proc(self, nCode, wParam, lParam):
        """フックコールバック — 最速でreturnする（重い処理は一切しない）"""
        if nCode >= 0 and wParam == self.WM_LBUTTONDOWN:
            ms = ctypes.cast(lParam, ctypes.POINTER(self.MSLLHOOKSTRUCT)).contents
            now = time.time()
            x, y = ms.pt.x, ms.pt.y

            # ダブルクリック判定（400ms以内、近い位置）
            dt = now - self._last_click_time
            dx = abs(x - self._last_click_pos[0])
            dy = abs(y - self._last_click_pos[1])

            if dt < 0.4 and dx < 10 and dy < 10:
                # フラグだけセット（処理はメインスレッドのポーリングで拾う）
                self._pending_dblclick = (x, y)
                self._last_click_time = 0
            else:
                self._pending_click = True
                self._last_click_time = now
                self._last_click_pos = (x, y)

        return ctypes.windll.user32.CallNextHookEx(self._hook, nCode, wParam, lParam)

    def start(self):
        """フック用スレッドを起動（独自メッセージループ必須）"""
        def hook_thread():
            self._hook = ctypes.windll.user32.SetWindowsHookExW(
                self.WH_MOUSE_LL, self._hook_proc, 0, 0
            )
            if not self._hook:
                logging.error(f"SetWindowsHookExW failed: {ctypes.GetLastError()}")
                return
            logging.debug("デスクトップダブルクリック検出フック設定完了")
            msg = ctypes.wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), 0, 0, 0):
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

        threading.Thread(target=hook_thread, daemon=True).start()


# === メインアプリ ===

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.icon = pystray.Icon("即ランチャー", make_icon(), "即ランチャー", self._build_menu())
        self.icon.HAS_DEFAULT_ACTION = False
        threading.Thread(target=self.icon.run, daemon=True).start()
        # デスクトップダブルクリック検出
        self._popup = None
        self._submenu = None
        self._popup_show_time = 0  # メニュー表示時刻（dismiss抑制用）
        self._detector = DesktopClickDetector(
            on_desktop_dblclick=lambda x, y: self.root.after(0, lambda: self._show_popup_menu(x, y)),
            on_any_click=lambda: self.root.after(100, self._safe_dismiss_popup)
        )
        self._detector.start()
        # フックからのイベントをポーリングで拾う（フック内は最速return）
        self._poll_hook_events()
        # WT数監視（3秒ごと、KBが多ければ閉じて再整列）
        self._last_wt_count = len(_find_wt_windows())
        self._poll_wt()

    def _poll_hook_events(self):
        """30msごとにフックからのイベントフラグをチェック（フック内を最速にするため）"""
        if self._detector._pending_click:
            self._detector._pending_click = False
            self._safe_dismiss_popup()
        if self._detector._pending_dblclick:
            x, y = self._detector._pending_dblclick
            self._detector._pending_dblclick = None
            threading.Thread(target=self._detector._check_desktop_and_fire,
                             args=(x, y), daemon=True).start()
        self.root.after(30, self._poll_hook_events)

    def _poll_wt(self):
        """3秒ごとにWT数を監視、減ったらKBも減らして再整列"""
        n_wt = len(_find_wt_windows())
        n_kb = len(_find_kb_windows())
        if n_wt != self._last_wt_count and n_kb > n_wt:
            logging.debug(f"WT数変化検出: WT={n_wt}, KB={n_kb} → KB削減")
            kb_hwnds = _find_kb_windows()
            for i in range(n_kb - n_wt):
                _close_one_keyboard(kb_hwnds[-(i + 1)])
            # 少し待ってから再整列（閉じるアニメーション分）
            self.root.after(300, _reposition_windows)
        self._last_wt_count = n_wt
        self.root.after(3000, self._poll_wt)

    def _open_single(self, folder_name):
        """シングル起動: 既存WT数チェック後、1つ起動して再配置"""
        logging.debug(f"_open_single 開始: {folder_name!r}")
        try:
            current_count = len(_find_wt_windows())
            if current_count >= MAX_TERMINALS:
                self.root.after(0, lambda: messagebox.showwarning("即ランチャー",
                    f"Already {current_count} terminals open (max {MAX_TERMINALS}).\n"
                    f"Close some terminals first."))
                return
            open_terminals([folder_name])
        except Exception:
            logging.error(f"_open_single でエラー:\n{traceback.format_exc()}")
            self.root.after(0, lambda: messagebox.showerror("即ランチャー",
                f"起動エラー: {traceback.format_exc()}"))

    def _safe_dismiss_popup(self):
        """メニュー表示直後のdismissを無視する（ダブルクリック2打目対策）"""
        if time.time() - self._popup_show_time < 0.5:
            return  # 表示から500ms以内は無視
        self._dismiss_popup()

    def _dismiss_popup(self):
        """ポップアップメニューを閉じる"""
        if self._popup:
            try:
                self._popup.destroy()
            except Exception:
                pass
            self._popup = None
        if self._submenu:
            try:
                self._submenu.destroy()
            except Exception:
                pass
            self._submenu = None

    def _show_popup_menu(self, x, y):
        """デスクトップダブルクリック時にカーソル位置にToplevelメニュー表示"""
        self._dismiss_popup()
        self._popup_show_time = time.time()

        FONT = ("Segoe UI", 10)
        BG = "#f0f0f0"
        BG_HOVER = "#0078d4"
        FG = "#1a1a1a"
        FG_HOVER = "#ffffff"
        SEP_COLOR = "#d0d0d0"
        PAD_X = 20
        PAD_Y = 4

        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.configure(bg=BG, highlightbackground="#999999", highlightthickness=1)

        def make_item(parent, label, command):
            lbl = tk.Label(parent, text=label, font=FONT, bg=BG, fg=FG,
                           anchor='w', padx=PAD_X, pady=PAD_Y, cursor='hand2')
            lbl.pack(fill='x')
            lbl.bind('<Enter>', lambda e: lbl.configure(bg=BG_HOVER, fg=FG_HOVER))
            lbl.bind('<Leave>', lambda e: lbl.configure(bg=BG, fg=FG))
            lbl.bind('<Button-1>', lambda e: (self._dismiss_popup(), command()))
            return lbl

        def make_separator(parent):
            tk.Frame(parent, height=1, bg=SEP_COLOR).pack(fill='x', padx=4, pady=2)

        def make_cascade(parent, label, items):
            lbl = tk.Label(parent, text=f"{label}  \u25b6", font=FONT, bg=BG, fg=FG,
                           anchor='w', padx=PAD_X, pady=PAD_Y, cursor='hand2')
            lbl.pack(fill='x')
            lbl.bind('<Enter>', lambda e: (lbl.configure(bg=BG_HOVER, fg=FG_HOVER),
                                           self._show_submenu(lbl, items)))
            lbl.bind('<Leave>', lambda e: lbl.configure(bg=BG, fg=FG))
            return lbl

        # OPEN → サブメニュー（Chatは除外）
        apps_folders, other_folders = get_folders()
        all_items = []
        for name in apps_folders:
            if name.lower() == 'chat':
                continue
            all_items.append(('item', name, lambda n=name: threading.Thread(
                target=lambda: self._open_single(n), daemon=True).start()))
        if other_folders:
            if all_items:
                all_items.append(('sep',))
            for name in other_folders:
                all_items.append(('item', name, lambda n=name: threading.Thread(
                    target=lambda: self._open_single(n), daemon=True).start()))

        make_cascade(win, "OPEN", all_items)
        make_separator(win)
        make_item(win, "Show All", lambda: bring_terminals_to_front())
        make_separator(win)
        make_item(win, "Chat", lambda: threading.Thread(
            target=lambda: self._open_single("Chat"), daemon=True).start())
        make_separator(win)
        make_item(win, "Refresh", lambda: self.root.after(0, self._rebuild_menu))
        make_item(win, "Close All", lambda: self._close_all())

        # 画面外にはみ出さない位置調整
        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        scr_w = win.winfo_screenwidth()
        scr_h = win.winfo_screenheight()
        if x + w > scr_w:
            x = scr_w - w
        if y + h > scr_h:
            y = scr_h - h
        win.geometry(f"+{x}+{y}")

        self._popup = win
        self._submenu = None

    def _show_submenu(self, anchor, items):
        """サブメニュー（OPENの中身）を表示"""
        if self._submenu:
            try:
                self._submenu.destroy()
            except Exception:
                pass

        FONT = ("Segoe UI", 10)
        BG = "#f0f0f0"
        BG_HOVER = "#0078d4"
        FG = "#1a1a1a"
        FG_HOVER = "#ffffff"
        SEP_COLOR = "#d0d0d0"
        PAD_X = 20
        PAD_Y = 4

        sub = tk.Toplevel(self.root)
        sub.overrideredirect(True)
        sub.attributes('-topmost', True)
        sub.configure(bg=BG, highlightbackground="#999999", highlightthickness=1)

        for item in items:
            if item[0] == 'sep':
                tk.Frame(sub, height=1, bg=SEP_COLOR).pack(fill='x', padx=4, pady=2)
            else:
                _, label, cmd = item
                lbl = tk.Label(sub, text=label, font=FONT, bg=BG, fg=FG,
                               anchor='w', padx=PAD_X, pady=PAD_Y, cursor='hand2')
                lbl.pack(fill='x')
                lbl.bind('<Enter>', lambda e, l=lbl: l.configure(bg=BG_HOVER, fg=FG_HOVER))
                lbl.bind('<Leave>', lambda e, l=lbl: l.configure(bg=BG, fg=FG))
                lbl.bind('<Button-1>', lambda e, c=cmd: (self._dismiss_popup(), c()))

        sub.update_idletasks()
        ax = anchor.winfo_rootx() + anchor.winfo_width()
        ay = anchor.winfo_rooty()
        scr_w = sub.winfo_screenwidth()
        sub_w = sub.winfo_reqwidth()
        if ax + sub_w > scr_w:
            ax = anchor.winfo_rootx() - sub_w
        sub.geometry(f"+{ax}+{ay}")
        self._submenu = sub

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
        apps_folders, other_folders = get_folders()
        items = []

        # OPEN → サブメニューでフォルダ一覧（apps + セパレータ + other-projects）
        open_items = []
        for name in apps_folders:
            logging.debug(f"メニュー項目追加(apps): {name!r}")
            open_items.append(pystray.MenuItem(name, self._make_single_callback(name)))
        if other_folders:
            if open_items:
                open_items.append(pystray.Menu.SEPARATOR)
            for name in other_folders:
                logging.debug(f"メニュー項目追加(other): {name!r}")
                open_items.append(pystray.MenuItem(name, self._make_single_callback(name)))
        if not open_items:
            open_items.append(pystray.MenuItem("(empty)", None, enabled=False))
        items.append(pystray.MenuItem("OPEN", pystray.Menu(*open_items)))
        items.append(pystray.Menu.SEPARATOR)

        # Show All
        items.append(pystray.MenuItem("Show All", lambda: bring_terminals_to_front()))
        items.append(pystray.Menu.SEPARATOR)

        # Refresh, Close All, Quit
        items.append(pystray.MenuItem("Refresh", lambda: self.root.after(0, self._rebuild_menu)))
        items.append(pystray.MenuItem("Close All", lambda: self._close_all()))
        items.append(pystray.MenuItem("Quit", lambda: self._quit()))
        return pystray.Menu(*items)

    def _make_single_callback(self, name):
        def callback():
            threading.Thread(target=lambda: self._open_single(name), daemon=True).start()
        return callback

    def _rebuild_menu(self):
        try:
            logging.debug("_rebuild_menu 開始")
            folders = get_folders()
            logging.debug(f"フォルダ一覧取得成功: {folders}")
            new_menu = self._build_menu()
            logging.debug("メニュー構築成功")
            self.icon.menu = new_menu
            logging.debug("メニュー設定完了")
        except Exception:
            logging.error(f"_rebuild_menu でエラー:\n{traceback.format_exc()}")

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
