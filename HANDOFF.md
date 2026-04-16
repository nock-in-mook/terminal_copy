# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（自動起動修復済み）
- Windows版: 安定稼働中

## 今回の作業（セッション033）
### Mac版の自動起動修復

**問題**:
- Mac再起動後に即ランチャーが自動起動していなかった
- LaunchAgentのplistファイル（`com.nock.folder-launcher.plist`）が `~/Library/LaunchAgents/` に存在していなかった
- install_mac.shはplistを書き出すが `launchctl bootstrap` を実行していなかったため、ファイルが消えると復旧できなかった

**対応**:
1. 手動でfolder_launcher.pyを起動（GDriveから最新版コピー後）
2. LaunchAgentのplistを再作成
3. `launchctl bootstrap` で登録 → 次回ログイン時から自動起動する

## 次のアクション
- 特になし。通常運用。
- install_mac.shに `launchctl bootstrap` を追加する改修は未実施（必要なら今後対応）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む、LaunchAgent方式）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — **`%LOCALAPPDATA%\即ランチャー\` に配置**（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される
