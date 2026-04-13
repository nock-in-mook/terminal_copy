# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中
- Windows版: 安定稼働中

## 今回の作業（セッション035）
### claude起動時に --effort max を自動付加

**背景**:
- Opus 4.6のバグ検出精度が劣化しているとの報告（2026-04-12時点）
- `/effort max` で工数レベルを最高に設定することが推奨されている

**対応**:
1. `folder_launcher_win.pyw` — Windows版の `claude` 起動コマンド2箇所に `--effort max` を追加
2. `folder_launcher.py` — Mac版の `claude` 起動コマンド1箇所に `--effort max` を追加
3. コミット＆プッシュ済み

**結果**:
- 即ランチャー経由で開くすべてのターミナルで `claude --dangerously-skip-permissions --effort max` が実行される
- 既存ターミナルには影響なし、新規起動分から適用

## 次のアクション
- 特になし。通常運用。

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む、LaunchAgent方式）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — **`%LOCALAPPDATA%\即ランチャー\` に配置**（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される
