#!/usr/bin/env python3
# folder_launcher_win.pyw
# Windows版フォルダランチャー：システムトレイ常駐
# アイコンクリック → フォルダ一覧メニュー → クリックでcdコマンドをクリップボードにコピー

import os
import subprocess
import pystray
from PIL import Image, ImageDraw, ImageFont

# 監視対象の親ディレクトリ
APPS_DIR = os.path.join(os.environ.get("USERPROFILE", ""), "Dropbox", "_Apps2026")
if not os.path.isdir(APPS_DIR):
    APPS_DIR = r"D:\Dropbox\_Apps2026"


def get_folders():
    """フォルダ一覧を取得"""
    try:
        entries = sorted(os.listdir(APPS_DIR), key=str.lower)
        return [e for e in entries
                if not e.startswith('.') and os.path.isdir(os.path.join(APPS_DIR, e))]
    except OSError:
        return []


def open_terminal(folder_name):
    """Windows Terminalでそのフォルダを開く"""
    full_path = os.path.join(APPS_DIR, folder_name)
    subprocess.Popen(['wt', '-d', full_path])


def make_icon():
    """トレイアイコン画像を生成（高解像度）"""
    size = 256
    img = Image.new('RGBA', (size, size), (0, 120, 212, 255))
    draw = ImageDraw.Draw(img)
    # フォルダアイコンを描画
    s = size / 64  # スケール係数
    draw.rectangle([int(8*s), int(20*s), int(56*s), int(52*s)],
                    fill=(255, 200, 50, 255), outline=(200, 150, 0, 255), width=int(3*s))
    draw.rectangle([int(8*s), int(14*s), int(28*s), int(24*s)],
                    fill=(255, 200, 50, 255), outline=(200, 150, 0, 255), width=int(3*s))
    return img


def make_callback(folder_name):
    """クロージャでフォルダ名を確定"""
    def callback():
        open_terminal(folder_name)
    return callback


def build_menu():
    """メニュー構築"""
    folders = get_folders()
    items = []
    for name in folders:
        items.append(pystray.MenuItem(name, make_callback(name)))
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Refresh", lambda: rebuild_menu()))
    items.append(pystray.MenuItem("Quit", lambda: icon.stop()))
    return pystray.Menu(*items)


def rebuild_menu():
    """メニューを再構築"""
    icon.menu = build_menu()


icon = pystray.Icon("folder_launcher", make_icon(), "Folder Launcher", build_menu())
# 左クリックでもメニューを表示（pystray Win32バックエンド）
icon.HAS_DEFAULT_ACTION = False
icon.run()
