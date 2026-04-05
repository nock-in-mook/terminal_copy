# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中
- Windows版: 安定稼働中

## 今回の変更（セッション031）
### Mac自動起動修正
- **原因**: LaunchAgent (`com.nock.folder-launcher.plist`) が旧Dropboxパスを指していた
  - 旧: `/Users/nock_re/Library/CloudStorage/Dropbox/_Apps2026/terminal_copy/folder_launcher.py`
  - 新: `/bin/bash` + `start.sh`（GDriveから最新版コピー→Python起動）
- `install_mac.sh` も「ログイン項目」方式から **LaunchAgent方式** に変更
- LaunchAgentのログ: `/tmp/sokulauncher_launchagent.log`

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む、LaunchAgent方式）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 次のアクション
- 特に緊急のタスクなし、安定稼働中
- 次回Mac再起動時にLaunchAgentで自動起動するか確認
