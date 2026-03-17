# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: GC問題修正済み、メニューバーアイコン追加済み、安定動作中
- Windows版: マウスフックブロック問題を修正済み（セッション018）

## 今回の変更（セッション018）
### 修正: Windows版マウスフックブロック問題
- デスクトップダブルクリック時にPCがカクカクになり即ランチャーが落ちる問題
- **原因**: `_low_level_mouse_proc`内で`SendMessageW`を呼んでいた → Explorerが重いとフックがブロック → Windows全体のマウス入力がフリーズ → Windowsがフックを強制解除
- **対策1**: デスクトップ判定処理をフック外の別スレッドに移動（フックは座標だけ取得して即座にreturn）
- **対策2**: `SendMessageW` → `SendMessageTimeoutW`（200msタイムアウト、SMTO_ABORTIFHUNG）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み）
- `install_mac.sh` — Mac版インストールスクリプト

## Mac版自動起動（SokuLauncher.app方式）
- `~/Library/Application Support/SokuLauncher/SokuLauncher.app` をログイン項目に登録
- start.sh起動時にGDriveから最新の `folder_launcher.py` と `hammerspoon_init.lua` を自動コピー
- 新しいMac: `bash install_mac.sh` 一発でOK

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
