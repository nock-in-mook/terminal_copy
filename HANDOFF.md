# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（Hammerspoon自動起動設定済み）
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション030）
### Hammerspoon自動起動設定
- **症状**: Mac再起動後に即ランチャーが起動しない
- **原因**: Hammerspoonの「Launch at Login」がOFFだった → クリック検知が動かず即ランチャーが反応しない
- **修正**: `defaults write org.hammerspoon.Hammerspoon MJAutoLaunchKey -bool true` で自動起動をONに設定

### 透明キーボードのキー反応しない問題（解決）
- Mac再起動で解消。macOS 26の一時的な不具合だった（前回セッション029での推測どおり）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
- 特に緊急のタスクなし、安定稼働中
