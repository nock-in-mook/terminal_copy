# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（Hammerspoon自動起動設定済み）
- Windows版: 安定稼働中
- Claude Code: v2.1.91にアップデート済み

## 今回の変更（セッション021）
### CLAUDE_CODE_NO_FLICKER検証
- Xで話題の `CLAUDE_CODE_NO_FLICKER=1`（マウス操作対応）を即ランチャーに組み込んで検証
- Windows Terminalでは効果なし（フルスクリーンモード自体が動かなかった）
- 設定を追加→削除のコミット2つ

### 経理バッチ作成
- `amazon_auto` フォルダでClaude起動＋`/keiri`スキル自動実行するバッチを作成
- Amazonアイコン付きショートカット(.lnk)としてデスクトップに配置
- ユーザーがリネーム済み

### Claude Codeアップデート
- v2.1.79 → v2.1.91にアップデート

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
- 特に緊急のタスクなし、安定稼働中
