# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: tmux復帰機能追加済み、安定動作中
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション025）
### tmux復帰機能の追加
- **目的**: Terminal.appが落ちてもClaude Codeセッションを復帰できるようにする
- **仕組み**: 即ランチャーがtmux内でclaude起動。ターミナルが落ちても tmuxセッションは裏で生き続ける
- **変更ファイル**:
  - `folder_launcher.py` — `open_terminal()`でtmuxセッション内にclaude起動。同名セッションが生きていれば自動再接続
  - `install_mac.sh` — tmuxの自動インストールを追加
  - `透明キーボード/mac/transparent_keyboard_mac.py` — 左下の「Term」ボタンを「tmux」復帰ボタンに変更（`tmux a` を入力）

### 復帰の流れ
1. ターミナルが落ちた場合、即ランチャーで同じフォルダを選ぶだけで自動復帰
2. 素のTerminalを開いた場合は透明キーボードの「tmux」ボタンで復帰

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 次のアクション
- もう一台のMacで `bash install_mac.sh` を実行してtmux導入（or 即ランチャー再起動だけでOK）
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
- フック軽量化後の動作確認（ダブルクリックでカクカクしないか）
