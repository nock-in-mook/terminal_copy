# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- 透明キーボードに「Claude」キーを追加済み（Mac版・Windows版両方）
- キーの機能: `claude --dangerously-skip-permissions` を入力してEnter

## 今回の変更（セッション022）
- 透明キーボードのRow 4（コマンド行）に「Claude」キーを追加
- Mac版: `透明キーボード/mac/transparent_keyboard_mac.py` — 幅比率を調整して5キー収容
- Windows版: `透明キーボード/transparent_keyboard.py` — 均等配分で5キー収容
- Windows版は `一発更新_即ランチャー.bat` で透明キーボードEXE再ビルドが必要

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（即ランチャーEXE + 透明キーボードEXE両方ビルド）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu）
- `install_mac.sh` — Mac版インストールスクリプト

## Mac版自動起動（SokuLauncher.app方式）
- `~/Library/Application Support/SokuLauncher/SokuLauncher.app` をログイン項目に登録
- .appの中身は `open -a Terminal start.sh` するだけのシェルスクリプト
- Terminal.app経由で起動するためGDriveアクセス権を継承できる

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド
- feature/mac-keyboard-sync ブランチをmainにマージするか判断
