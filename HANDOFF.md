# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: tmux復帰機能＋ゾンビ掃除追加済み、Hammerspoon自動リロード追加済み、安定動作中
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション027）
### tmuxゾンビセッション対策
- ×ボタンでターミナルを閉じるとtmuxセッションがデタッチ状態で残る問題に対応
- フォルダを開くたびに全tmuxセッションをスキャン、デタッチ状態（session_attached=0）のものを一括kill
- アタッチ中（作業中・入力待ち含む）のセッションは影響なし

### 透明キーボードのAPPSボタン → /exitボタンに変更
- Mac版・Windows版の両方で対応
- ボタンを押すとターミナルに `/exit` + Enter を送信 → Claude Code終了 → tmuxセッション自動消滅

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
