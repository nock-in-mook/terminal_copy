#!/usr/bin/env python3
# folder_launcher.py
# Mac版フォルダランチャー：デスクトップダブルクリックでポップアップメニュー
# - デスクトップの空白部分をダブルクリック → メニュー表示
# - [OPEN] サブメニューからフォルダ選択 → ターミナル起動
# - 最大4ウィンドウ、左寄せ配置（Dock幅分マージン）
# - 透明キーボード同期（ターミナル数 = キーボード数）

import os
import sys
import subprocess
import time

import objc
from Foundation import NSObject, NSMakePoint, NSTimer
from AppKit import (
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSEvent,
    NSLeftMouseDownMask,
    NSScreen,
    NSMenu,
    NSMenuItem,
    NSAlert,
    NSAlertFirstButtonReturn,
    NSImage,
)
from Quartz import (
    CGWindowListCopyWindowInfo,
    kCGWindowListOptionOnScreenOnly,
    kCGNullWindowID,
)

# 監視対象の親ディレクトリ
APPS_DIR = os.path.expanduser("~/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026")
GDRIVE_DIR = os.path.dirname(APPS_DIR)  # マイドライブ直下
OTHER_PROJECTS_DIR = os.path.join(GDRIVE_DIR, "_other-projects")

# ウィンドウ幅（画面幅に対する割合）
WIN_WIDTH_RATIO = 0.20
# マージン（画面高さに対する割合）- 下25%はキーボード領域
MARGIN_TOP_RATIO = 0.0
MARGIN_BOTTOM_RATIO = 0.25
# 最大ウィンドウ数
MAX_TERMINALS = 4

# 透明キーボードのパス
KB_DIR = os.path.join(APPS_DIR, "透明キーボード", "mac")
KB_SCRIPT = os.path.join(KB_DIR, "transparent_keyboard_mac.py")

# tty → フォルダ名のマッピング（タイトル維持用）
_tty_titles = {}


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
        other_folders = []
        if os.path.isdir(OTHER_PROJECTS_DIR):
            other_folders = sorted([e for e in os.listdir(OTHER_PROJECTS_DIR)
                        if not e.startswith('.') and os.path.isdir(os.path.join(OTHER_PROJECTS_DIR, e))],
                       key=str.lower)
        return apps_folders, other_folders
    except OSError as e:
        import sys
        print(f"get_folders ERROR: {e}", file=sys.stderr, flush=True)
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
    """全Terminal.appウィンドウを左寄せで再配置し、キーボードをその真下に配置"""
    sw, sh, dock_margin, menubar_h = _get_screen_info()
    win_count = _get_terminal_window_count()
    if win_count == 0:
        return

    win_count = min(win_count, MAX_TERMINALS)

    win_w = int(sw * WIN_WIDTH_RATIO)
    margin_top = int(sh * MARGIN_TOP_RATIO)
    win_h = sh - margin_top - int(sh * MARGIN_BOTTOM_RATIO)

    # キーボードサイズ: ターミナルと同じ幅、下の残りスペースを使う
    kb_w = win_w
    kb_h = (sh - menubar_h) - (margin_top + win_h)

    kb_positions = []
    kb_titles = []
    for i in range(win_count):
        x = dock_margin + i * win_w
        win_idx = win_count - i
        # ターミナル配置＆tty取得
        script = f'''
tell application "Terminal"
    if (count of windows) >= {win_idx} then
        set bounds of window {win_idx} to {{{x}, {margin_top}, {x + win_w}, {margin_top + win_h}}}
        return tty of tab 1 of window {win_idx}
    end if
end tell'''
        tty = _run_applescript(script)

        # ttyからフォルダ名を取得
        title = _tty_titles.get(tty, '') if tty else ''
        kb_titles.append(title)

        # キーボード位置を計算（macOS座標系: 左下原点）
        kb_x = x
        kb_y = sh - menubar_h - (margin_top + win_h)
        kb_positions.append((kb_x, kb_y))

    # キーボードを同期配置（ターミナルと同じ幅、残りスペースの高さ）
    _sync_keyboards_with_positions(kb_positions, kb_w=kb_w, kb_h=kb_h, titles=kb_titles)


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


def _launch_one_keyboard(x=None, y=None, width=None, height=None, slot=0, title=''):
    """透明キーボードを1つ起動（位置・サイズ・スロット・タイトル指定）"""
    if os.path.exists(KB_SCRIPT):
        cmd = ['python3', KB_SCRIPT]
        if x is not None and y is not None:
            cmd += ['--x', str(x), '--y', str(y)]
        if width is not None:
            cmd += ['--width', str(width)]
        if height is not None:
            cmd += ['--height', str(height)]
        cmd += ['--slot', str(slot)]
        if title:
            cmd += ['--title', title]
        subprocess.Popen(
            cmd,
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


def _sync_keyboards_with_positions(positions, kb_w=None, kb_h=None, titles=None):
    """キーボードを全て閉じてから、指定位置に必要数だけ起動し直す
    positions: [(x, y), ...] ターミナル真下の座標リスト（macOS座標系）
    kb_w: キーボード幅, kb_h: キーボード高さ
    titles: [str, ...] 各スロットのフォルダ名
    """
    if titles is None:
        titles = [''] * len(positions)
    # 既存を全て閉じる
    _close_all_keyboards()
    time.sleep(0.3)
    # 必要数だけ起動（スロット番号でテーマを分ける）
    for slot, (x, y) in enumerate(positions):
        title = titles[slot] if slot < len(titles) else ''
        _launch_one_keyboard(x=x, y=y, width=kb_w, height=kb_h, slot=slot, title=title)
        time.sleep(0.2)


def _close_all_keyboards():
    """全ての透明キーボードを閉じる"""
    for pid in _find_kb_pids():
        _close_one_keyboard(pid)


# === メイン関数 ===

def open_terminal(folder_name):
    """Terminal.appウィンドウを1つ起動し、再配置（キーボード同期含む）"""
    full_path = resolve_folder_path(folder_name)
    # 起動してttyを取得し、タイトルマッピングに登録
    script = f'''
tell application "Terminal"
    do script "unset CLAUDECODE; cd \\"{full_path}\\" && claude --dangerously-skip-permissions"
    tell tab 1 of front window
        set custom title to "{folder_name}"
        set title displays custom title to true
        set title displays device name to false
        set title displays shell path to false
        set title displays window size to false
        set title displays file name to false
    end tell
    set ttyPath to tty of tab 1 of front window
    activate
    return ttyPath
end tell'''
    tty = _run_applescript(script)
    if tty:
        _tty_titles[tty] = folder_name
    time.sleep(1.5)
    _reposition_windows()


def _refresh_titles():
    """全ターミナルのタイトルをフォルダ名で上書き（Claude Codeの上書きを防ぐ）"""
    if not _tty_titles:
        return
    for tty, title in list(_tty_titles.items()):
        script = f'''
tell application "Terminal"
    repeat with w in windows
        repeat with t in tabs of w
            if tty of t is "{tty}" then
                set custom title of t to "{title}"
            end if
        end repeat
    end repeat
end tell'''
        _run_applescript(script)


def bring_terminals_to_front():
    """全Terminal.appウィンドウを再配置＋最前面（キーボード同期含む）"""
    _reposition_windows()
    _run_applescript('tell application "Terminal" to activate')


def close_all_terminals():
    """全Terminal.appウィンドウ＋全キーボードを閉じる"""
    _run_applescript('tell application "Terminal" to close every window')
    _close_all_keyboards()


# === デスクトップダブルクリック検知 ===

def _is_desktop_click(x, y):
    """クリック座標がデスクトップの空白部分かどうか判定
    CGWindowListCopyWindowInfoで画面上のウィンドウを前面から順にチェックし、
    通常のアプリウィンドウ（layer 0）がクリック位置になければデスクトップと判定
    """
    windows = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID
    )
    if not windows:
        return False

    # 除外するオーナー（システム系・リモートデスクトップのオーバーレイ等）
    IGNORE_OWNERS = {'Dock', 'Window Server', 'WindowManager', 'AnyDesk',
                     'Control Center', 'SystemUIServer'}

    for win in windows:
        layer = win.get('kCGWindowLayer', -1)
        # 通常ウィンドウ層（layer 0）のみチェック
        if layer != 0:
            continue

        owner = win.get('kCGWindowOwnerName', '')
        # システム系のウィンドウは無視
        if owner in IGNORE_OWNERS:
            continue

        bounds = win.get('kCGWindowBounds')
        if not bounds:
            continue

        wx = bounds.get('X', 0)
        wy = bounds.get('Y', 0)
        ww = bounds.get('Width', 0)
        wh = bounds.get('Height', 0)

        # クリック座標がこのウィンドウ内か
        if wx <= x <= wx + ww and wy <= y <= wy + wh:
            # 通常アプリのウィンドウが被ってる → デスクトップではない
            return False

    # layer 0 の通常ウィンドウが被ってない → デスクトップ
    return True


class _Invoker(NSObject):
    """NSTimerコールバック用ヘルパー"""
    def initWithBlock_(self, block):
        self = objc.super(_Invoker, self).init()
        if self is None:
            return None
        self._block = block
        return self

    def invoke_(self, timer):
        if self._block:
            self._block()


class DesktopLauncher(NSObject):
    """デスクトップダブルクリックでポップアップメニューを表示するランチャー"""

    def init(self):
        self = objc.super(DesktopLauncher, self).init()
        if self is None:
            return None
        self._last_click_time = 0
        self._last_click_x = 0
        self._last_click_y = 0
        return self

    def start(self):
        """イベント監視を開始"""
        NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
            NSLeftMouseDownMask,
            self._on_global_click
        )
        # 3秒ごとにターミナルタイトルをフォルダ名で上書き
        invoker = _Invoker.alloc().initWithBlock_(_refresh_titles)
        self._title_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            3.0, invoker, "invoke:", None, True
        )
        print("即ランチャー起動: デスクトップダブルクリック待機中", flush=True)

    @objc.python_method
    def _on_global_click(self, event):
        """グローバルマウスクリックハンドラ"""
        # クリック座標（macOS座標: 左下原点）
        loc = NSEvent.mouseLocation()
        # CGWindowListは左上原点なので変換
        screen = NSScreen.mainScreen()
        screen_h = screen.frame().size.height
        cg_x = loc.x
        cg_y = screen_h - loc.y

        now = time.time()
        dx = abs(cg_x - self._last_click_x)
        dy = abs(cg_y - self._last_click_y)

        # ダブルクリック判定: 0.4秒以内、5px以内
        if now - self._last_click_time < 0.4 and dx < 5 and dy < 5:
            # ダブルクリック検出 → デスクトップか判定
            if _is_desktop_click(cg_x, cg_y):
                self._show_menu(loc)
            self._last_click_time = 0  # リセット
        else:
            self._last_click_time = now
            self._last_click_x = cg_x
            self._last_click_y = cg_y

    @objc.python_method
    def _show_menu(self, location):
        """ポップアップメニューを表示"""
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)

        menu = NSMenu.alloc().initWithTitle_("即ランチャー")
        menu.setAutoenablesItems_(False)

        # --- OPEN サブメニュー（Chatは除外） ---
        apps_folders, other_folders = get_folders()

        open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "OPEN", None, "")
        open_item.setEnabled_(True)
        open_submenu = NSMenu.alloc().initWithTitle_("OPEN")
        open_submenu.setAutoenablesItems_(False)

        for name in apps_folders:
            if name.lower() == 'chat':
                continue
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                name, "openFolder:", "")
            item.setTarget_(self)
            item.setEnabled_(True)
            open_submenu.addItem_(item)

        if other_folders and apps_folders:
            open_submenu.addItem_(NSMenuItem.separatorItem())

        for name in other_folders:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                name, "openFolder:", "")
            item.setTarget_(self)
            item.setEnabled_(True)
            open_submenu.addItem_(item)

        open_item.setSubmenu_(open_submenu)
        menu.addItem_(open_item)

        # --- セパレータ ---
        menu.addItem_(NSMenuItem.separatorItem())

        # --- Show All ---
        show_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Show All", "showAll:", "")
        show_item.setTarget_(self)
        show_item.setEnabled_(True)
        menu.addItem_(show_item)

        # --- セパレータ ---
        menu.addItem_(NSMenuItem.separatorItem())

        # --- Chat（トップレベルに独立配置） ---
        chat_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Chat", "openFolder:", "")
        chat_item.setTarget_(self)
        chat_item.setEnabled_(True)
        chat_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "ellipsis.message", None)
        if chat_icon:
            chat_item.setImage_(chat_icon)
        menu.addItem_(chat_item)

        # --- セパレータ ---
        menu.addItem_(NSMenuItem.separatorItem())

        # --- Refresh ---
        refresh_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Refresh", "refresh:", "")
        refresh_item.setTarget_(self)
        refresh_item.setEnabled_(True)
        refresh_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_(
            "arrow.clockwise", None)
        if refresh_icon:
            refresh_item.setImage_(refresh_icon)
        menu.addItem_(refresh_item)

        # --- Close All ---
        close_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Close All", "closeAll:", "")
        close_item.setTarget_(self)
        close_item.setEnabled_(True)
        menu.addItem_(close_item)

        # メニューをクリック位置に表示
        menu.popUpMenuPositioningItem_atLocation_inView_(
            None, location, None
        )

    # === メニューアクション（ObjCセレクタ） ===

    def openFolder_(self, sender):
        """フォルダを選んでターミナル起動"""
        name = sender.title()
        current = _get_terminal_window_count()
        if current >= MAX_TERMINALS:
            alert = NSAlert.alloc().init()
            alert.setMessageText_(f"{current}個のターミナルが開いています（最大{MAX_TERMINALS}）。\n先に閉じてください。")
            alert.runModal()
            return
        open_terminal(name)

    def showAll_(self, sender):
        bring_terminals_to_front()

    def refresh_(self, sender):
        """フォルダ一覧は毎回メニュー表示時に取得するので何もしない"""
        pass

    def closeAll_(self, sender):
        """全ターミナル＋キーボードを閉じる（確認2回）"""
        count = _get_terminal_window_count()
        if count == 0:
            alert = NSAlert.alloc().init()
            alert.setMessageText_("開いているターミナルはありません。")
            alert.runModal()
            return

        alert1 = NSAlert.alloc().init()
        alert1.setMessageText_(f"{count}個のターミナルを全て閉じますか？")
        alert1.addButtonWithTitle_("閉じる")
        alert1.addButtonWithTitle_("キャンセル")
        if alert1.runModal() != NSAlertFirstButtonReturn:
            return

        alert2 = NSAlert.alloc().init()
        alert2.setMessageText_("本当に閉じますか？\n保存していない作業は失われます。")
        alert2.addButtonWithTitle_("閉じる")
        alert2.addButtonWithTitle_("キャンセル")
        if alert2.runModal() == NSAlertFirstButtonReturn:
            close_all_terminals()


# === ターミナル数ポーリング（3秒ごとにKB自動削減） ===

def _poll_terminal_count(launcher):
    """3秒ごとにターミナル数を監視、減ったらKBも減らして再整列"""
    wt_count = _get_terminal_window_count()
    kb_pids = _find_kb_pids()
    kb_count = len(kb_pids)
    if kb_count > wt_count:
        # 余分なKBを閉じる（後ろから）
        excess = kb_count - wt_count
        for i in range(excess):
            _close_one_keyboard(kb_pids[-(i + 1)])
        # 0.3秒後に再整列（メインスレッドをブロックしない）
        if wt_count > 0:
            reposition_invoker = _Invoker.alloc().initWithBlock_(_reposition_windows)
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.3, reposition_invoker, "invoke:", None, False
            )
    # 次のポーリングをスケジュール
    invoker = _Invoker.alloc().initWithBlock_(lambda: _poll_terminal_count(launcher))
    NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
        3.0, invoker, "invoke:", None, False
    )


if __name__ == "__main__":
    # --show-all モード: 再配置＋最前面に出して終了
    if "--show-all" in sys.argv:
        bring_terminals_to_front()
        sys.exit(0)
    # --open <フォルダ名> モード: 指定フォルダでターミナル起動して終了
    if "--open" in sys.argv:
        idx = sys.argv.index("--open")
        if idx + 1 < len(sys.argv):
            open_terminal(sys.argv[idx + 1])
        sys.exit(0)

    # 多重起動防止（PIDファイル方式）
    import signal
    pidfile = "/tmp/sokulauncher.pid"
    if os.path.exists(pidfile):
        try:
            old_pid = int(open(pidfile).read().strip())
            os.kill(old_pid, 0)  # プロセス存在チェック
            # まだ動いてる → 古い方を終了
            os.kill(old_pid, signal.SIGTERM)
            time.sleep(0.5)
        except (ProcessLookupError, ValueError, PermissionError):
            pass  # 既に死んでる
    with open(pidfile, "w") as f:
        f.write(str(os.getpid()))

    # NSApplicationベースのバックグラウンド常駐
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)  # Dock非表示

    launcher = DesktopLauncher.alloc().init()
    launcher.start()

    # ターミナル数ポーリング開始（3秒ごと）
    _poll_terminal_count(launcher)

    # クラッシュ保護
    try:
        app.run()
    except Exception as e:
        import traceback; traceback.print_exc()
        raise
