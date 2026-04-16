# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（自動起動問題を修正済み）
- Windows版: 安定稼働中

## 今回の作業（セッション034）
### LaunchAgent自動起動の修正

**問題**:
- Mac再起動後に即ランチャーが自動起動しなかった（2つの原因）

**原因1: start.shのバックグラウンド起動が刈り取られる**
- plistが `start.sh` を呼ぶ → start.shが `nohup python3 &` + `exit 0` → launchdが子プロセスを刈り取り
- **修正**: plistから `bash -c "cp ...; exec python3 ..."` で直接起動。`exec`でbashがpython3に置き換わるため、launchdが監視するプロセス＝python3本体になる

**原因2: Hammerspoonがログイン項目に登録されていなかった**
- クリック検知はHammerspoonが担当しているが、ログイン項目に入っていなかった
- **修正**: osascriptでログイン項目に追加。install_mac.shにも同処理を追加

## 次のアクション
- 特になし。次回再起動で自動起動が正常に動くか確認する

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む、LaunchAgent方式、Hammerspoonログイン項目登録）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — **`%LOCALAPPDATA%\即ランチャー\` に配置**（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される
