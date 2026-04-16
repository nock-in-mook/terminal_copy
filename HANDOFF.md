# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（自動起動をログイン項目方式に変更済み）
- Windows版: 安定稼働中

## 今回の作業（セッション035）
### Mac版の自動起動をログイン項目方式に変更

**問題**:
1. LaunchAgentのstart.shが `nohup python3 &` + `exit 0` → launchdが子プロセスを刈り取り → 起動失敗
2. LaunchAgentから直接 `exec python3` に修正 → 起動はするがGUI権限不足でAppleScript（Terminal操作）が動かない
3. Hammerspoonがログイン項目に未登録 → クリック検知が起動しない

**対応**:
1. LaunchAgent（plist）方式を廃止、plist削除済み
2. SokuLauncher.app（ログイン項目）の中身を `exec python3` に書き換え（GDriveからの最新コピー付き）
3. Hammerspoonもログイン項目に登録済み
4. install_mac.shも同じログイン項目方式に更新

**ポイント**: ログイン項目はGUIセッションとして起動されるため、AppleScriptやsubprocessでのGUI操作が正常に動く

## 次のアクション
- 再起動して自動起動が正常に動くか確認する

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
