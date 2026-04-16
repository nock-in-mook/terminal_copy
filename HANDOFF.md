# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（自動起動はログイン項目方式）
- Windows版: 安定稼働中

## 今回の作業（セッション036）
### ターミナル.appのスクロール挙動を修正

**問題**: Mac版でClaude Code利用中、マウスホイールを回すと入力履歴が循環してチャット本文をスクロールできなかった

**原因**: ターミナル.app「Clear Dark」プロファイルの「代替スクリーンをスクロール」設定がONになっていて、altscreenモードでスクロールが矢印キー扱いになっていた

**対応**: 設定 → プロファイル → Clear Dark → **キーボード**タブの「代替スクリーンをスクロール」チェックを外した（詳細タブではなくキーボードタブにあった。macOS 26 Tahoeでの位置）

**結果**: マウスホイールでチャット本文がスクロール可能に。プロファイル設定なので永続。

## 次のアクション
- 特になし（前回セッションの「再起動して自動起動確認」はまだ残ってる可能性あり）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む、ログイン項目方式）
- `SokuLauncher.app` — ログイン項目用.appラッパー（`~/Library/Application Support/SokuLauncher/` に配置）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — **`%LOCALAPPDATA%\即ランチャー\` に配置**（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される
