#!/usr/bin/env python3
# folder_launcher.py
# メニューバー常駐アプリ：プロジェクトフォルダのcdコマンドをクリップボードにコピー

import os
import subprocess
import rumps

# 監視対象の親ディレクトリ
APPS_DIR = os.path.expanduser("~/Library/CloudStorage/Dropbox/_Apps2026")

class FolderLauncher(rumps.App):
    def __init__(self):
        super().__init__("📂", quit_button=None)
        self.menu = self._build_menu()

    def _get_folders(self):
        """フォルダ一覧を取得（ドットファイル・通常ファイルは除外）"""
        try:
            entries = sorted(os.listdir(APPS_DIR), key=str.lower)
            return [e for e in entries
                    if not e.startswith('.') and os.path.isdir(os.path.join(APPS_DIR, e))]
        except OSError:
            return []

    def _build_menu(self):
        folders = self._get_folders()
        items = []
        for name in folders:
            item = rumps.MenuItem(name, callback=self._on_click)
            items.append(item)
        items.append(rumps.separator)
        items.append(rumps.MenuItem("更新", callback=self._refresh))
        items.append(rumps.MenuItem("終了", callback=self._quit))
        return items

    def _on_click(self, sender):
        """フォルダ名クリック → cdコマンドをクリップボードにコピー"""
        full_path = os.path.join(APPS_DIR, sender.title)
        cmd = f'cd "{full_path}"'
        # pbcopyでクリップボードにコピー
        proc = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        proc.communicate(cmd.encode('utf-8'))
        rumps.notification("folder_launcher", "", f"{sender.title} をコピーしました")

    def _refresh(self, _):
        """フォルダ一覧を再読み込み"""
        self.menu.clear()
        for item in self._build_menu():
            self.menu.add(item)
        rumps.notification("folder_launcher", "", "フォルダ一覧を更新しました")

    def _quit(self, _):
        rumps.quit_application()

if __name__ == "__main__":
    FolderLauncher().run()
