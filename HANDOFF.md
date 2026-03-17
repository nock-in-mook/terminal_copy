# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- 新しいMacで即ランチャーが動かない問題を修正済み
- メニューバーにフォルダアイコンを追加済み

## 今回の変更（セッション024）
### 修正: Hammerspoon GC問題
- `local clickWatcher` → `SokuClickWatcher`（グローバル変数化）
- `hs.timer.doEvery` の戻り値も `SokuWatchdogTimer` でグローバル保持
- LuaのGCにeventtapが回収されて時間経過で止まる問題を解消
- watchdogのnilチェック追加

### 追加: メニューバーフォルダアイコン
- `NSStatusItem` でメニューバーにフォルダアイコン（folder.fill）を設置
- クリックするとOPEN/ShowAll/Chat/Refresh/CloseAllの同じメニューが出る
- Hammerspoonが止まったときでもメニューバーから操作できるフォールバック
- `_build_menu()` に共通化し、ダブルクリック・メニューバー両方で使用
- Refresh押すとメニューバーのフォルダ一覧も再構築

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み）
- `install_mac.sh` — Mac版インストールスクリプト

## Mac版自動起動（SokuLauncher.app方式）
- `~/Library/Application Support/SokuLauncher/SokuLauncher.app` をログイン項目に登録
- start.sh起動時にGDriveから最新の `folder_launcher.py` と `hammerspoon_init.lua` を自動コピー
- 新しいMac: `bash install_mac.sh` 一発でOK

## 安定性
- 再起動時: SokuLauncher.appがログイン項目から自動起動
- GC問題: グローバル変数化で解消済み
- 万が一の時: メニューバーアイコンからフォールバック操作可能

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
