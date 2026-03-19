# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: tmux復帰機能＋ゾンビ掃除追加済み、Hammerspoon自動リロード追加済み、安定動作中
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション028）
### 透明キーボード 英/日トグル修正
- 英/日ボタンがCtrl+Spaceを送信→入力ソース選択ポップアップが出る問題を修正
- `defaults read` はキャッシュされてリアルタイムに反映しないことが判明
- 最終的にctypes経由でmacOSのTIS APIを直接呼び出し、現在の入力ソースをリアルタイム判定→英数(102)/かな(104)キーコードを送り分ける方式に
- ファイル: `透明キーボード/mac/transparent_keyboard_mac.py`

### GDrive直接実行＋一発更新sh
- `run.sh --install` がローカルコピーを使う問題を修正→GDriveから直接実行するLaunchAgentに変更
- `mac/一発更新_透明キーボード.sh` を新規作成（既存kill→LaunchAgent再登録→再起動）
- 他のMacではこのshを1回実行すればOK、以後はGDrive同期で最新版が使われる

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
- 他のMacで `一発更新_透明キーボード.sh` を実行してGDrive直接実行に切り替える
