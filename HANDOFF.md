# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中
- Windows版: 安定稼働中

## 今回の作業（セッション034）
### ビルド成果物をローカル出力に変更（複数PC対応）

**問題**:
- 新しいPCで即ランチャーが起動しない
- 起動時に毎回「発行元が不明」警告が出る

**原因**:
- `即ランチャー.exe` / `python3xx.dll` / `_pth` をGドライブに置いていた
- `_pth` にはビルドしたPCの `sys.executable` パスが焼き込まれる仕様（`_build_exe.py`）
- 別PCでbatを走らせると、そのPCのPythonパスが `_pth` に書かれてGドライブ経由で同期
- 他PCで同じEXEを起動すると、存在しないパスを参照してpythonw.exeが無言で落ちる
- さらにGドライブ上の未署名EXEはSmartScreenが毎回警告を出す

**対応**:
1. `_build_exe.py` の出力先を `%LOCALAPPDATA%\即ランチャー\` に変更
2. `_setup_shortcuts.py` もローカルEXEを指すように変更（PYWはGドライブのまま→コード編集は即反映）
3. `一発更新_即ランチャー.bat` に Python 3.14 の winget 自動インストールを追加
4. Gドライブ上の古いビルド成果物（`即ランチャー.exe` / `python3.dll` / `python314.dll` / `python310.dll` / `python314._pth` / `python310._pth`）を削除
5. `.gitignore` に `python3*.dll` / `python3*._pth` を追加
6. `CLAUDE.md` のハマりポイント「8」に経緯を追記

**このPCでの動作確認完了**:
- Python: `C:\Users\msp\AppData\Local\Programs\Python\Python314\python.exe`
- EXE: `C:\Users\msp\AppData\Local\即ランチャー\即ランチャー.exe`
- `_pth` はこのPCのPython 3.14を正しく参照
- スタートアップ/スタートメニューのショートカットも新パスに更新済み
- プロセス起動確認済み

## ★ 他PCでやること（リモート作業）
**このセッションで他PCにリモート接続して作業すること:**

1. `cd G:\マイドライブ\_Apps2026\terminal_copy`
2. `git pull`（最新コミット 4bcd4f1 を取り込む）
3. エクスプローラで `一発更新_即ランチャー.bat` をダブルクリック
   - Python 3.14 が無ければwingetで自動インストールされる
   - `%LOCALAPPDATA%\即ランチャー\` にEXEが作られる
   - ショートカットも自動更新
   - 即ランチャーが起動する
4. タスクトレイに即ランチャーアイコンが出たら成功

**なぜ必要か**:
- コミット4bcd4f1でGドライブ上の `即ランチャー.exe` 等が削除された
- 他PCでは現状、既存ショートカットがGドライブ上のEXE（もう消えた）を指してる
- このままだと次回起動時に即ランチャーが動かなくなる
- batを走らせればローカルに再ビルドされて復活する

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む、LaunchAgent方式）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — **`%LOCALAPPDATA%\即ランチャー\` に配置**（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される
