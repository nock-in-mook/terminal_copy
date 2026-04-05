# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中
- Windows版: 安定稼働中

## 今回の変更（セッション032）
### 透明キーボードMac版: 英/日キー → スクショフォルダ開くボタンに変更
- `透明キーボード/mac/transparent_keyboard_mac.py` 340行目
- 「英/日」(toggle_input_source) → 「📁SS」(open_screenshot_folder) に変更
- スクショの動作確認のため（スクショが時々うまく撮れない問題の調査用）

### スクショ関連の調査結果
- スクショ保存先: `/var/folders/kd/_w62d2390nn777kgzdyq8ysm0000gp/T/claude_screenshots/`（`/tmp` ではない）
- `paste_latest_screenshot()` 自体は正常動作を確認
- スクショが撮れない問題は未解決（再現せず）

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
- スクショが撮れない問題の再現待ち（📁SSボタンでフォルダ確認しながら調査）
- 英/日キーが不要か確認（不要なら📁SSのまま、必要なら別の場所に移動）
