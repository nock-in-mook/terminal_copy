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
    NSStatusBar,
    NSVariableStatusItemLength,
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


def _is_terminal_running():
    """Terminal.appが起動しているかをpgrepで確認（AppleScriptを使わない）"""
    result = subprocess.run(['pgrep', '-x', 'Terminal'], capture_output=True, text=True)
    return result.returncode == 0


def _get_terminal_window_count():
    """Terminal.appのウィンドウ数を取得（Terminal未起動なら0を返す）"""
    if not _is_terminal_running():
        return 0
    script = '''
tell application "Terminal"
    return count of windows
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
    terminal_was_running = _is_terminal_running()
    # tmuxセッション名（ドットを除去、tmuxはドット入りセッション名を嫌う）
    tmux_session = folder_name.replace('.', '_')
    # tmuxセッションが生きていれば再接続、なければ新規作成（シングルクォートでエスケープ回避）
    tmux_cmd = (
        f"tmux has-session -t '{tmux_session}' 2>/dev/null "
        f"&& tmux attach -t '{tmux_session}' "
        f"|| tmux new-session -s '{tmux_session}' -c '{full_path}' "
        f"'unset CLAUDECODE; claude --dangerously-skip-permissions'"
    )
    # Terminal未起動の場合: activateでデフォルトウィンドウを作り、そこにdo scriptする
    # Terminal起動済みの場合: do scriptで新ウィンドウを作る
    if not terminal_was_running:
        script = f'''
tell application "Terminal"
    activate
    delay 0.5
    do script "{tmux_cmd}" in front window
    tell tab 1 of front window
        set custom title to "{folder_name}"
        set title displays custom title to true
        set title displays device name to false
        set title displays shell path to false
        set title displays window size to false
        set title displays file name to false
    end tell
    set ttyPath to tty of tab 1 of front window
    return ttyPath
end tell'''
    else:
        script = f'''
tell application "Terminal"
    do script "{tmux_cmd}"
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
    if not _tty_titles or not _is_terminal_running():
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
    if not _is_terminal_running():
        return
    _reposition_windows()
    _run_applescript('tell application "Terminal" to activate')


def close_all_terminals():
    """全Terminal.appウィンドウ＋全キーボードを閉じる"""
    if _is_terminal_running():
        _run_applescript('tell application "Terminal" to close every window')
    _close_all_keyboards()


# === デスクトップダブルクリック検知 ===

def _is_desktop_click(x, y):
    """クリック座標がデスクトップの空白部分かどうか判定
    CGWindowListでクリック位置のウィンドウを前面から順にチェック:
    - 通常アプリのウィンドウ(layer 0)が被ってたら → デスクトップではない
    - 被ってなければ → クリック位置に最初にヒットするのがFinderのデスクトップか確認
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
        owner = win.get('kCGWindowOwnerName', '')

        # システム系は無視
        if owner in IGNORE_OWNERS:
            continue
        # 通常ウィンドウ層（layer 0）のみチェック
        if layer != 0:
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
            # Finderのウィンドウが被ってる場合もデスクトップではない（フォルダウィンドウ）
            return False

    # layer 0のウィンドウが被ってない → デスクトップ領域の可能性
    # AppleScriptでFinderのinsertionLocationがデスクトップかチェック
    try:
        result = _run_applescript(
            'tell application "Finder" to return POSIX path of (insertion location as alias)')
        desktop_path = os.path.expanduser("~/Desktop")
        if result.rstrip('/') != desktop_path.rstrip('/'):
            return False  # Finderのフォーカスがデスクトップ以外 → 反応しない
    except Exception:
        return False

    # さらにFinderの選択状態をチェック（アイコン上のクリックを除外）
    try:
        result = _run_applescript(
            'tell application "Finder" to return count of (selection as alias list)')
        if result and int(result) > 0:
            return False  # アイコンが選択されている → 空白部分ではない
    except (ValueError, Exception):
        pass

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
        """イベント監視を開始（Hammerspoonからのトリガーをポーリング）"""
        # トリガーファイルを監視するタイマー（0.1秒ごと）
        invoker = _Invoker.alloc().initWithBlock_(self._check_trigger)
        self._trigger_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.1, invoker, "invoke:", None, True
        )
        # 3秒ごとにターミナルタイトルをフォルダ名で上書き
        invoker2 = _Invoker.alloc().initWithBlock_(_refresh_titles)
        self._title_timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            3.0, invoker2, "invoke:", None, True
        )
        # メニューバーアイコン
        self._setup_status_item()
        print("即ランチャー起動: デスクトップダブルクリック待機中（Hammerspoon連携）", flush=True)

    @objc.python_method
    def _setup_status_item(self):
        """メニューバーにアイコンを設置"""
        self._status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(
            NSVariableStatusItemLength
        )
        icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_("folder.fill", None)
        if icon:
            icon.setTemplate_(True)  # ダークモード対応
            self._status_item.button().setImage_(icon)
        self._status_item.button().setToolTip_("即ランチャー")
        self._rebuild_status_menu()

    @objc.python_method
    def _rebuild_status_menu(self):
        """ステータスアイテムのメニューを再構築"""
        self._status_item.setMenu_(self._build_menu())

    @objc.python_method
    def _check_trigger(self):
        """Hammerspoonが書いたトリガーファイルを監視してメニューを表示"""
        trigger = "/tmp/sokulauncher_trigger"
        if not os.path.exists(trigger):
            return
        try:
            with open(trigger, "r") as f:
                content = f.read().strip()
            os.remove(trigger)
            # 座標を読む（Hammerspoon座標: 左上原点、macOS AppKit座標: 左下原点）
            parts = content.split(",")
            if len(parts) == 2:
                x = float(parts[0])
                hs_y = float(parts[1])
                # HammerspoonはY軸が上から下、AppKitは下から上なので変換
                screen_h = NSScreen.mainScreen().frame().size.height
                y = screen_h - hs_y
                from Foundation import NSMakePoint
                loc = NSMakePoint(x, y)
                self._show_menu(loc)
        except Exception as e:
            print(f"trigger error: {e}", flush=True)

    @objc.python_method
    def _show_menu(self, location):
        """ポップアップメニューをクリック位置に表示"""
        app = NSApplication.sharedApplication()
        app.activateIgnoringOtherApps_(True)
        menu = self._build_menu()
        menu.popUpMenuPositioningItem_atLocation_inView_(None, location, None)

    # === メニューアクション（ObjCセレクタ） ===

    @objc.python_method
    def _build_menu(self):
        """ポップアップ用メニューを構築して返す（ダブルクリック・メニューバー共通）"""
        menu = NSMenu.alloc().initWithTitle_("即ランチャー")
        menu.setAutoenablesItems_(False)

        apps_folders, other_folders = get_folders()

        open_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("OPEN", None, "")
        open_item.setEnabled_(True)
        open_submenu = NSMenu.alloc().initWithTitle_("OPEN")
        open_submenu.setAutoenablesItems_(False)
        for name in apps_folders:
            if name.lower() == 'chat':
                continue
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(name, "openFolder:", "")
            item.setTarget_(self)
            item.setEnabled_(True)
            open_submenu.addItem_(item)
        if other_folders and apps_folders:
            open_submenu.addItem_(NSMenuItem.separatorItem())
        for name in other_folders:
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(name, "openFolder:", "")
            item.setTarget_(self)
            item.setEnabled_(True)
            open_submenu.addItem_(item)
        open_item.setSubmenu_(open_submenu)
        menu.addItem_(open_item)

        menu.addItem_(NSMenuItem.separatorItem())

        show_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Show All", "showAll:", "")
        show_item.setTarget_(self)
        show_item.setEnabled_(True)
        menu.addItem_(show_item)

        menu.addItem_(NSMenuItem.separatorItem())

        chat_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Chat", "openFolder:", "")
        chat_item.setTarget_(self)
        chat_item.setEnabled_(True)
        chat_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_("ellipsis.message", None)
        if chat_icon:
            chat_item.setImage_(chat_icon)
        menu.addItem_(chat_item)

        menu.addItem_(NSMenuItem.separatorItem())

        refresh_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Refresh", "refresh:", "")
        refresh_item.setTarget_(self)
        refresh_item.setEnabled_(True)
        refresh_icon = NSImage.imageWithSystemSymbolName_accessibilityDescription_("arrow.clockwise", None)
        if refresh_icon:
            refresh_item.setImage_(refresh_icon)
        menu.addItem_(refresh_item)

        close_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Close All", "closeAll:", "")
        close_item.setTarget_(self)
        close_item.setEnabled_(True)
        menu.addItem_(close_item)

        return menu

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
        """メニューバーのフォルダ一覧を再構築"""
        self._rebuild_status_menu()

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
