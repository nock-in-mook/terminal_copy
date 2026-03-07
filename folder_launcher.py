#!/usr/bin/env python3
# folder_launcher.py
# Mac版フォルダランチャー：メニューバー常駐
# - [1 single] サブメニューからフォルダ選択 → 即起動
# - [2 split] [3 split] → サブメニューで順番に選択 → 自動起動
# - 最大3ウィンドウ制限、Show All、Close All
# - 左寄せ配置（Dockが左にあるため）

import os
import subprocess
import time
import rumps

# 監視対象の親ディレクトリ
APPS_DIR = os.path.expanduser("~/Library/CloudStorage/Dropbox/_Apps2026")

# 画面の何%をターミナルに使うか（左寄せ）
SCREEN_USE_RATIO = 0.95
# 上下マージン（画面高さに対する割合）
MARGIN_TOP_RATIO = 0.10
MARGIN_BOTTOM_RATIO = 0.10
# 最大ウィンドウ数
MAX_TERMINALS = 3


def get_folders():
    """フォルダ一覧を取得"""
    try:
        entries = sorted(os.listdir(APPS_DIR), key=str.lower)
        exclude = {'images', 'text'}
        return [e for e in entries
                if not e.startswith('.') and e not in exclude
                and os.path.isdir(os.path.join(APPS_DIR, e))]
    except OSError:
        return []


def _run_applescript(script):
    """AppleScriptを実行して結果を返す"""
    result = subprocess.run(['osascript', '-e', script],
                            capture_output=True, text=True)
    return result.stdout.strip()


def _get_screen_size():
    """画面サイズを取得（メニューバー・Dock考慮なしの全体サイズ）"""
    script = 'tell application "Finder" to get bounds of window of desktop'
    result = _run_applescript(script)
    # "0, 0, 1920, 1080" の形式
    parts = [int(x.strip()) for x in result.split(',')]
    return parts[2], parts[3]  # width, height


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
    """全Terminal.appウィンドウを左寄せで再配置"""
    sw, sh = _get_screen_size()
    win_count = _get_terminal_window_count()
    if win_count == 0:
        return

    win_count = min(win_count, MAX_TERMINALS)

    # 配置計算（幅は常にMAX_TERMINALS分割時と同じ固定幅）
    total_w = int(sw * SCREEN_USE_RATIO)
    win_w = total_w // MAX_TERMINALS
    margin_top = int(sh * MARGIN_TOP_RATIO)
    win_h = sh - margin_top - int(sh * MARGIN_BOTTOM_RATIO)

    # 左寄せで配置（ウィンドウ番号は新しい順=逆順に並んでいるので注意）
    for i in range(win_count):
        x = i * win_w
        # AppleScriptのboundsは {左, 上, 右, 下}
        # ウィンドウiは左からi番目に配置
        # Terminal.appのwindow indexは1始まり、新しい順
        # 左から並べるために逆順でアクセス
        win_idx = win_count - i
        script = f'''
tell application "Terminal"
    if (count of windows) >= {win_idx} then
        set bounds of window {win_idx} to {{{x}, {margin_top}, {x + win_w}, {margin_top + win_h}}}
    end if
end tell'''
        _run_applescript(script)


def open_terminals(folder_names):
    """Terminal.appウィンドウを起動し、全ターミナルを左寄せで再配置"""
    if not folder_names:
        return

    for name in folder_names:
        full_path = os.path.join(APPS_DIR, name)
        # Terminal.appで新しいウィンドウを開き、cdしてclaude起動
        # CLAUDECODE環境変数をクリアしてネスト防止
        script = f'''
tell application "Terminal"
    do script "unset CLAUDECODE; cd \\"{full_path}\\" && echo -ne \\"\\\\033]0;{name}\\\\007\\" && claude --dangerously-skip-permissions"
    activate
end tell'''
        _run_applescript(script)
        time.sleep(0.5)

    # ウィンドウが出揃うのを少し待つ
    time.sleep(1.0)
    _reposition_windows()


def bring_terminals_to_front():
    """全Terminal.appウィンドウを最前面に出す"""
    script = '''
tell application "Terminal"
    activate
end tell'''
    _run_applescript(script)


def close_all_terminals():
    """全Terminal.appウィンドウを閉じる"""
    script = '''
tell application "Terminal"
    close every window
end tell'''
    _run_applescript(script)


class FolderLauncher(rumps.App):
    def __init__(self):
        super().__init__("📂", quit_button=None)
        # split選択の状態管理
        self._selecting_count = 0  # 0=選択中でない, 2or3=選択中
        self._selected = []
        self.menu = self._build_menu()

    def _build_menu(self):
        folders = get_folders()
        items = []

        # [1 single] → サブメニューでフォルダ一覧
        single_menu = rumps.MenuItem("[1 single]")
        for name in folders:
            item = rumps.MenuItem(name, callback=self._on_single_click)
            single_menu.add(item)
        items.append(single_menu)

        # [2 split] / [3 split]
        if self._selecting_count > 0:
            # 選択中: 現在の状態を表示
            progress = f"[{self._selecting_count} split] ({len(self._selected)}/{self._selecting_count})"
            split_menu = rumps.MenuItem(progress)
            for name in folders:
                if name in self._selected:
                    # 選択済みは番号付きで表示
                    idx = self._selected.index(name) + 1
                    item = rumps.MenuItem(f"✓ {idx}. {name}")
                    split_menu.add(item)
                else:
                    item = rumps.MenuItem(name, callback=self._on_split_click)
                    split_menu.add(item)
            # キャンセルボタン
            split_menu.add(rumps.separator)
            split_menu.add(rumps.MenuItem("Cancel", callback=self._cancel_split))
            items.append(split_menu)
        else:
            items.append(rumps.MenuItem("[2 split]", callback=self._start_split_2))
            items.append(rumps.MenuItem("[3 split]", callback=self._start_split_3))

        items.append(rumps.separator)
        # Show All
        items.append(rumps.MenuItem("[Show All]", callback=self._show_all))
        items.append(rumps.separator)

        # Refresh, Close All, Quit
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

    def _on_single_click(self, sender):
        """シングル起動"""
        current = _get_terminal_window_count()
        if current >= MAX_TERMINALS:
            rumps.alert(f"{current}個のターミナルが開いています（最大{MAX_TERMINALS}）。\n先に閉じてください。")
            return
        open_terminals([sender.title])

    def _start_split_2(self, _):
        self._start_split(2)

    def _start_split_3(self, _):
        self._start_split(3)

    def _start_split(self, count):
        """split選択を開始"""
        current = _get_terminal_window_count()
        if current + count > MAX_TERMINALS:
            remaining = MAX_TERMINALS - current
            if remaining <= 0:
                rumps.alert(f"{current}個のターミナルが開いています（最大{MAX_TERMINALS}）。\n先に閉じてください。")
                return
            rumps.alert(f"{current}個のターミナルが開いています（最大{MAX_TERMINALS}）。\nあと{remaining}個しか追加できません。")
            count = remaining

        self._selecting_count = count
        self._selected = []
        self._rebuild_menu()
        rumps.notification("Folder Launcher", "", f"フォルダを{count}個選んでください")

    def _on_split_click(self, sender):
        """split選択中にフォルダをクリック"""
        name = sender.title
        if name in self._selected:
            return

        self._selected.append(name)

        if len(self._selected) >= self._selecting_count:
            # 選択完了 → 起動
            folders = list(self._selected)
            self._selecting_count = 0
            self._selected = []
            self._rebuild_menu()
            open_terminals(folders)
        else:
            # まだ選択中 → メニュー更新
            self._rebuild_menu()
            remaining = self._selecting_count - len(self._selected)
            rumps.notification("Folder Launcher", "", f"あと{remaining}個選んでください")

    def _cancel_split(self, _):
        """split選択をキャンセル"""
        self._selecting_count = 0
        self._selected = []
        self._rebuild_menu()

    def _refresh(self, _):
        """フォルダ一覧を再読み込み"""
        self._rebuild_menu()
        rumps.notification("Folder Launcher", "", "フォルダ一覧を更新しました")

    def _close_all(self, _):
        """全ターミナルを閉じる（確認付き）"""
        count = _get_terminal_window_count()
        if count == 0:
            rumps.alert("開いているターミナルはありません。")
            return
        r1 = rumps.alert(f"{count}個のターミナルを全て閉じますか？",
                         ok="閉じる", cancel="キャンセル")
        if r1 != 1:
            return
        r2 = rumps.alert("本当に閉じますか？保存していない作業は失われます。",
                         ok="閉じる", cancel="キャンセル")
        if r2 != 1:
            return
        close_all_terminals()

    def _quit(self, _):
        rumps.quit_application()


if __name__ == "__main__":
    FolderLauncher().run()
