#!/usr/bin/env python3
# folder_launcher_win.pyw
# Windows版フォルダランチャー：システムトレイ常駐
# - [1 single] サブメニューからフォルダ選択 → 即起動
# - [2 split] [3 split] → 選択UIで複数選択 → Launch
# - 最大3ウィンドウ制限、Show All、Close All

import os
import subprocess
import threading
import ctypes
import ctypes.wintypes
import time
import tkinter as tk
from tkinter import messagebox
import pystray
from PIL import Image, ImageDraw

# DPIスケーリング: 呼ばない方がMoveWindowの論理座標でWTを狭くできる

# 監視対象の親ディレクトリ
APPS_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "Dropbox", "_Apps2026")
if not os.path.isdir(APPS_DIR):
    APPS_DIR = r"D:\Dropbox\_Apps2026"

# 画面の何%をターミナルに使うか（右寄せ。残りが左端のアイコン用余白）
SCREEN_USE_RATIO = 0.95
# 上下マージン（画面高さに対する割合）
MARGIN_TOP_RATIO = 0.10
MARGIN_BOTTOM_RATIO = 0.10
# ウィンドウ影の重なり補正（論理ピクセル）
SHADOW_OVERLAP = 14
# 最大ウィンドウ数
MAX_TERMINALS = 3


def get_folders():
    """フォルダ一覧を取得"""
    try:
        entries = sorted(os.listdir(APPS_DIR), key=str.lower)
        # 除外フォルダ
        exclude = {'images', 'text'}
        return [e for e in entries
                if not e.startswith('.') and e not in exclude
                and os.path.isdir(os.path.join(APPS_DIR, e))]
    except OSError:
        return []


def _reposition_windows():
    """全WTウィンドウを右寄せで再配置"""
    user32 = ctypes.windll.user32
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)

    all_hwnds = _find_wt_windows()
    if not all_hwnds:
        return

    all_hwnds = all_hwnds[:MAX_TERMINALS]

    # x座標でソート
    rects = []
    rect = ctypes.wintypes.RECT()
    for hwnd in all_hwnds:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        rects.append((rect.left, hwnd))
    rects.sort(key=lambda r: r[0])

    # 配置計算（幅は常にMAX_TERMINALS分割時と同じ固定幅）
    total_count = len(rects)
    total_w = int(sw * SCREEN_USE_RATIO)
    win_w = (total_w + SHADOW_OVERLAP * (MAX_TERMINALS - 1)) // MAX_TERMINALS
    margin_top = int(sh * MARGIN_TOP_RATIO)
    win_h = sh - margin_top - int(sh * MARGIN_BOTTOM_RATIO)

    x = sw
    for i in range(total_count - 1, -1, -1):
        _, hwnd = rects[i]
        x -= win_w
        if i < total_count - 1:
            x += SHADOW_OVERLAP
        user32.MoveWindow(hwnd, x, margin_top, win_w, win_h, True)


def open_terminals(folder_names):
    """Windows Terminalウィンドウを起動し、全WT（既存含む）を右寄せで再配置"""
    if not folder_names:
        return

    # 起動前のWTウィンドウを記録
    before_hwnds = set(_find_wt_windows())
    n = len(folder_names)

    # 新しいターミナルを起動（タブタイトル設定 + Claude自動起動）
    for name in folder_names:
        full_path = os.path.join(APPS_DIR, name)
        env = os.environ.copy()
        env.pop('CLAUDECODE', None)
        subprocess.Popen(['wt', '--title', name, '-d', full_path, 'cmd', '/k', 'claude --dangerously-skip-permissions'],
                         creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                         env=env)
        time.sleep(0.5)

    # 新しいウィンドウが出揃うのを待つ
    for _ in range(20):
        time.sleep(0.3)
        current = set(_find_wt_windows())
        new_hwnds = list(current - before_hwnds)
        if len(new_hwnds) >= n:
            break

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
    """全WTウィンドウを最前面に出す"""
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
        self._build_split_window()
        self.icon = pystray.Icon("folder_launcher", make_icon(), "Folder Launcher", self._build_menu())
        self.icon.HAS_DEFAULT_ACTION = False
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _build_split_window(self):
        """ターミナル選択ウィンドウを構築（非表示状態で保持）"""
        w = tk.Toplevel(self.root)
        w.title("Open Terminals")
        w.attributes("-topmost", True)
        w.resizable(False, True)
        w.protocol("WM_DELETE_WINDOW", lambda: w.withdraw())
        self.split_win = w

        self.selected = []
        self.split_count = 2

        # 数ボタン
        count_frame = tk.Frame(w)
        count_frame.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(count_frame, text="Count:", font=("Segoe UI", 10)).pack(side="left")
        self.count_buttons = {}
        for n in [2, 3]:
            btn = tk.Button(count_frame, text=str(n), width=3,
                            font=("Segoe UI", 10, "bold"),
                            command=lambda n=n: self._set_count(n))
            btn.pack(side="left", padx=2)
            self.count_buttons[n] = btn

        # 選択済みリスト
        sel_frame = tk.LabelFrame(w, text="Selected (left to right)", font=("Segoe UI", 9))
        sel_frame.pack(fill="x", padx=8, pady=4)
        self.sel_listbox = tk.Listbox(sel_frame, height=3, font=("Segoe UI", 10),
                                       selectbackground="#ffcccc")
        self.sel_listbox.pack(fill="x", padx=4, pady=4)
        self.sel_listbox.bind("<Button-1>", self._on_sel_click)

        # フォルダ一覧（スクロール付き）
        folder_frame = tk.LabelFrame(w, text="Folders", font=("Segoe UI", 9))
        folder_frame.pack(fill="both", expand=True, padx=8, pady=4)
        folder_scroll = tk.Scrollbar(folder_frame)
        folder_scroll.pack(side="right", fill="y")
        self.folder_listbox = tk.Listbox(folder_frame, font=("Segoe UI", 10),
                                          selectbackground="#cce5ff",
                                          yscrollcommand=folder_scroll.set)
        self.folder_listbox.pack(fill="both", expand=True, padx=4, pady=4)
        folder_scroll.config(command=self.folder_listbox.yview)
        self.folder_listbox.bind("<Button-1>", self._on_folder_click)

        # ボタン
        btn_frame = tk.Frame(w)
        btn_frame.pack(fill="x", padx=8, pady=(4, 8))
        self.launch_btn = tk.Button(btn_frame, text="Launch", font=("Segoe UI", 10, "bold"),
                                     state="disabled", command=self._launch)
        self.launch_btn.pack(side="right", padx=4)
        tk.Button(btn_frame, text="Reset", font=("Segoe UI", 10),
                  command=self._reset).pack(side="right", padx=4)

        self.launch_btn.config(state="disabled")

        # ウィンドウサイズ・位置（右下寄り）
        w.update_idletasks()
        scr_w = w.winfo_screenwidth()
        scr_h = w.winfo_screenheight()
        ww, wh = 280, 700
        taskbar_h = 48
        w.geometry(f"{ww}x{wh}+{scr_w - ww}+{scr_h - wh - taskbar_h}")
        w.withdraw()

    def _show_split(self, count):
        self.root.after(0, lambda: self._show_split_main(count))

    def _show_split_main(self, count):
        # 既存WT数チェック
        current_count = len(_find_wt_windows())
        if current_count + count > MAX_TERMINALS:
            remaining = MAX_TERMINALS - current_count
            if remaining <= 0:
                messagebox.showwarning("Folder Launcher",
                    f"Already {current_count} terminals open (max {MAX_TERMINALS}).\n"
                    f"Close some terminals first.")
                return
            else:
                messagebox.showwarning("Folder Launcher",
                    f"Already {current_count} terminals open (max {MAX_TERMINALS}).\n"
                    f"Can only add {remaining} more.")
                count = remaining

        self.selected = []
        self.split_count = count
        self._highlight_count()
        self._refresh_folders()
        self._refresh_sel()
        self.split_win.deiconify()
        self.split_win.lift()

    def _open_single(self, folder_name):
        """シングル起動: 既存WT数チェック後、1つ起動して再配置"""
        current_count = len(_find_wt_windows())
        if current_count >= MAX_TERMINALS:
            self.root.after(0, lambda: messagebox.showwarning("Folder Launcher",
                f"Already {current_count} terminals open (max {MAX_TERMINALS}).\n"
                f"Close some terminals first."))
            return
        open_terminals([folder_name])

    def _refresh_folders(self):
        self.folder_listbox.delete(0, tk.END)
        for name in get_folders():
            self.folder_listbox.insert(tk.END, name)

    def _set_count(self, n):
        self.split_count = n
        if len(self.selected) > n:
            self.selected = self.selected[:n]
        self._highlight_count()
        self._refresh_sel()

    def _highlight_count(self):
        for num, btn in self.count_buttons.items():
            if num == self.split_count:
                btn.config(bg="#0078D4", fg="white")
            else:
                btn.config(bg="SystemButtonFace", fg="black")

    def _refresh_sel(self):
        self.sel_listbox.delete(0, tk.END)
        for i in range(self.split_count):
            if i < len(self.selected):
                self.sel_listbox.insert(tk.END, f"{i+1}. {self.selected[i]}")
            else:
                self.sel_listbox.insert(tk.END, f"{i+1}. ---")
        if len(self.selected) == self.split_count:
            self.launch_btn.config(state="normal")
        else:
            self.launch_btn.config(state="disabled")

    def _on_folder_click(self, event):
        self.folder_listbox.after(50, self._add_selected)

    def _add_selected(self):
        sel = self.folder_listbox.curselection()
        if not sel:
            return
        name = self.folder_listbox.get(sel[0])
        if len(self.selected) < self.split_count and name not in self.selected:
            self.selected.append(name)
            self._refresh_sel()

    def _on_sel_click(self, event):
        self.sel_listbox.after(50, self._remove_selected)

    def _remove_selected(self):
        sel = self.sel_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx < len(self.selected):
            self.selected.pop(idx)
            self._refresh_sel()

    def _reset(self):
        self.selected = []
        self._refresh_sel()

    def _launch(self):
        if self.selected:
            folders = list(self.selected)
            self.split_win.withdraw()
            self.selected = []
            threading.Thread(target=lambda: open_terminals(folders), daemon=True).start()

    def _close_all(self):
        """Close All: 確認2回してから全WT閉じる"""
        def do_close():
            count = len(_find_wt_windows())
            if count == 0:
                messagebox.showinfo("Folder Launcher", "No terminals open.")
                return
            r1 = messagebox.askyesno("Folder Launcher",
                f"Close all {count} terminal(s)?")
            if not r1:
                return
            r2 = messagebox.askyesno("Folder Launcher",
                f"Are you sure? All unsaved work will be lost.")
            if not r2:
                return
            close_all_terminals()
        self.root.after(0, do_close)

    # === トレイメニュー ===

    def _build_menu(self):
        folders = get_folders()
        items = []

        # Show All（一番上）
        items.append(pystray.MenuItem("[Show All]", lambda: bring_terminals_to_front()))
        items.append(pystray.Menu.SEPARATOR)

        # [1 single] → サブメニューでフォルダ一覧
        single_items = []
        for name in folders:
            single_items.append(pystray.MenuItem(name, self._make_single_callback(name)))
        items.append(pystray.MenuItem("[1 single]", pystray.Menu(*single_items)))

        # [2 split] [3 split] → 選択UI
        items.append(pystray.MenuItem("[2 split]", lambda: self._show_split(2)))
        items.append(pystray.MenuItem("[3 split]", lambda: self._show_split(3)))
        items.append(pystray.Menu.SEPARATOR)

        # Refresh, Close All, Quit
        items.append(pystray.MenuItem("Refresh", lambda: self._rebuild_menu()))
        items.append(pystray.MenuItem("[Close All]", lambda: self._close_all()))
        items.append(pystray.MenuItem("Quit", lambda: self._quit()))
        return pystray.Menu(*items)

    def _make_single_callback(self, name):
        def callback():
            threading.Thread(target=lambda: self._open_single(name), daemon=True).start()
        return callback

    def _rebuild_menu(self):
        self.icon.menu = self._build_menu()

    def _quit(self):
        self.icon.stop()
        self.root.after(0, self.root.destroy)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()
