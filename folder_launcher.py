#!/usr/bin/env python3
# folder_launcher.py
# Mac版フォルダランチャー：メニューバー常駐
# - [OPEN] サブメニューからフォルダ選択 → ターミナル起動
# - 最大4ウィンドウ、左寄せ配置（Dock幅分マージン）
# - 透明キーボード同期（ターミナル数 = キーボード数）

import os
import sys
import subprocess
import time
import rumps
from AppKit import NSScreen

import logging
logging.basicConfig(filename='/tmp/launcher_debug.log', level=logging.DEBUG,
                    format='%(asctime)s %(message)s')

# 監視対象の親ディレクトリ
APPS_DIR = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026")
GDRIVE_DIR = os.path.dirname(APPS_DIR)  # マイドライブ直下
OTHER_PROJECTS_DIR = os.path.join(GDRIVE_DIR, "_other-projects")

# ウィンドウ幅（画面幅に対する割合）
WIN_WIDTH_RATIO = 0.20
# マージン（画面高さに対する割合）- 下20%はキーボード領域
MARGIN_TOP_RATIO = 0.0
MARGIN_BOTTOM_RATIO = 0.20
# 最大ウィンドウ数
MAX_TERMINALS = 4

# 透明キーボードのパス
KB_DIR = os.path.join(APPS_DIR, "透明キーボード", "mac")
KB_SCRIPT = os.path.join(KB_DIR, "transparent_keyboard_mac.py")


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


def _run_applescript(script):
    """AppleScriptを実行して結果を返す"""
    result = subprocess.run(['osascript', '-e', script],
                            capture_output=True, text=True)
    return result.stdout.strip()


def _get_screen_info():
    """画面サイズとDockマージンを取得（AppKit使用）"""
    screen = NSScreen.mainScreen()
    full = screen.frame()
    visible = screen.visibleFrame()
    dock_margin = int(visible.origin.x)
    menubar_h = int(full.size.height - visible.size.height - visible.origin.y)
    return int(full.size.width), int(full.size.height), dock_margin, menubar_h


def _get_terminal_window_count():
    """Terminal.appのウィンドウ数を取得"""
    script = '''
tell application "Terminal"
    if it is running then
        return count of windows
    else
        return 0
    end if
end tell'''
    result = _run_applescript(script)
    try:
        return int(result)
    except ValueError:
        return 0


def _reposition_windows():
    """全Terminal.appウィンドウを左寄せで再配置（Dock幅分のマージンあり）"""
    sw, sh, dock_margin, menubar_h = _get_screen_info()
    win_count = _get_terminal_window_count()
    if win_count == 0:
        return

    win_count = min(win_count, MAX_TERMINALS)

    win_w = int(sw * WIN_WIDTH_RATIO)
    margin_top = int(sh * MARGIN_TOP_RATIO)
    win_h = sh - margin_top - int(sh * MARGIN_BOTTOM_RATIO)

    for i in range(win_count):
        x = dock_margin + i * win_w
        win_idx = win_count - i
        script = f'''
tell application "Terminal"
    if (count of windows) >= {win_idx} then
        set bounds of window {win_idx} to {{{x}, {margin_top}, {x + win_w}, {margin_top + win_h}}}
    end if
end tell'''
        _run_applescript(script)


# === 透明キーボード同期 ===

def _find_kb_pids():
    """透明キーボードMac版のプロセスIDを全て取得"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'transparent_keyboard_mac.py'],
            capture_output=True, text=True
        )
        pids = [int(p) for p in result.stdout.strip().split('\n') if p.strip()]
        # 自分自身のPIDは除外
        my_pid = os.getpid()
        return [p for p in pids if p != my_pid]
    except (ValueError, OSError):
        return []


def _launch_one_keyboard():
    """透明キーボードを1つ起動"""
    if os.path.exists(KB_SCRIPT):
        subprocess.Popen(
            ['python3', KB_SCRIPT],
            cwd=KB_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )


def _close_one_keyboard(pid):
    """透明キーボードを1つ閉じる"""
    try:
        os.kill(pid, 15)  # SIGTERM
    except OSError:
        pass


def _sync_keyboards():
    """キーボード数をターミナル数に合わせる（増やす or 減らす）"""
    n_wt = _get_terminal_window_count()
    kb_pids = _find_kb_pids()
    n_kb = len(kb_pids)
    # 足りなければ追加
    for _ in range(n_wt - n_kb):
        _launch_one_keyboard()
        time.sleep(0.3)
    # 多ければ閉じる（後ろから）
    for i in range(n_kb - n_wt):
        _close_one_keyboard(kb_pids[-(i + 1)])


def _close_all_keyboards():
    """全ての透明キーボードを閉じる"""
    for pid in _find_kb_pids():
        _close_one_keyboard(pid)


# === メイン関数 ===

def open_terminal(folder_name):
    """Terminal.appウィンドウを1つ起動し、キーボード同期＆再配置"""
    full_path = resolve_folder_path(folder_name)
    script = f'''
tell application "Terminal"
    do script "unset CLAUDECODE; cd \\"{full_path}\\" && echo -ne \\"\\\\033]0;{folder_name}\\\\007\\" && claude --dangerously-skip-permissions"
    activate
end tell'''
    _run_applescript(script)
    time.sleep(1.5)
    _sync_keyboards()
    time.sleep(0.5)
    _reposition_windows()


def bring_terminals_to_front():
    """全Terminal.appウィンドウを再配置＋最前面（キーボード数も同期）"""
    _sync_keyboards()
    time.sleep(0.5)
    _reposition_windows()
    _run_applescript('tell application "Terminal" to activate')


def close_all_terminals():
    """全Terminal.appウィンドウ＋全キーボードを閉じる"""
    _run_applescript('tell application "Terminal" to close every window')
    _close_all_keyboards()


class FolderLauncher(rumps.App):
    def __init__(self):
        super().__init__("📂", quit_button=None)
        self.menu = self._build_menu()

    def _build_menu(self):
        folders = get_folders()
        items = []

        # [OPEN] → サブメニューでフォルダ一覧
        open_menu = rumps.MenuItem("[OPEN]")
        for name in folders:
            item = rumps.MenuItem(name, callback=self._on_open_click)
            open_menu.add(item)
        items.append(open_menu)

        items.append(rumps.separator)
        items.append(rumps.MenuItem("[Show All]", callback=self._show_all))
        items.append(rumps.separator)
        items.append(rumps.MenuItem("Refresh", callback=self._refresh))
        items.append(rumps.MenuItem("[Close All]", callback=self._close_all))
        items.append(rumps.MenuItem("Quit", callback=self._quit))

        return items

    def _rebuild_menu(self):
        """メニューを再構築"""
        self.menu.clear()
        for item in self._build_menu():
            self.menu.add(item)

    def _show_all(self, _):
        bring_terminals_to_front()

    def _on_open_click(self, sender):
        """フォルダを選んでターミナル起動"""
        current = _get_terminal_window_count()
        if current >= MAX_TERMINALS:
            rumps.alert(f"{current}個のターミナルが開いています（最大{MAX_TERMINALS}）。\n先に閉じてください。")
            return
        open_terminal(sender.title)

    def _refresh(self, _):
        """フォルダ一覧を再読み込み"""
        self._rebuild_menu()
        rumps.notification("Folder Launcher", "", "フォルダ一覧を更新しました")

    def _close_all(self, _):
        """全ターミナル＋キーボードを閉じる（確認2回）"""
        count = _get_terminal_window_count()
        if count == 0:
            rumps.alert("開いているターミナルはありません。")
            return
        r1 = rumps.alert(f"{count}個のターミナルを全て閉じますか？",
                         ok="閉じる", cancel="キャンセル")
        if r1 != 1:
            return
        r2 = rumps.alert("本当に閉じますか？\n保存していない作業は失われます。",
                         ok="閉じる", cancel="キャンセル")
        if r2 == 1:
            close_all_terminals()

    def _quit(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    # --show-all モード: 再配置＋最前面に出して終了
    if "--show-all" in sys.argv:
        bring_terminals_to_front()
        sys.exit(0)
    FolderLauncher().run()
