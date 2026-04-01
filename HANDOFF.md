# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 安定動作中（Hammerspoon自動起動設定済み）
- Windows版: 安定稼働中

## 今回の変更（セッション020）
### Snipping Toolスクショ自動保存設定
- **症状**: このPCだけWin+Shift+Sで範囲選択後にSnipping Toolの編集画面が消えず、自動保存もされない
- **原因**: Snipping Toolの設定で「元のスクリーンショットを自動的に保存」がOFFだった
- **解決**: Snipping Tool → 設定 → 「自動的に保存」をONにして解決
- 編集ウィンドウは残るが、自動保存はされるようになった
- コードの変更は不要だった（一時的にtake_and_paste_screenshot関数を追加したが元に戻した）

### 学んだこと
- 透明キーボードからsubprocess.runでPowerShellを呼ぶときはCREATE_NO_WINDOWが必要（ループで呼ぶとターミナルが大量に開く）
- Google DriveがEXEをロックする場合はos.replaceで差し替えると成功する

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
