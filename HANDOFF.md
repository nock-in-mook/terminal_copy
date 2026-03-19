# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: tmux復帰機能追加済み、Hammerspoon自動リロード追加済み、安定動作中
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション026）
### Hammerspoon設定の自動リロード
- **問題**: 別Macでinit.luaを編集→GDrive同期→このMacのHammerspoonは古い設定のまま動き続ける
- **対策**: `hs.pathwatcher`でGDrive上の`hammerspoon_init.lua`を監視。変更検知→自動コピー→自動リロード
- **変更ファイル**: `hammerspoon_init.lua`

### 再起動時の注意（セッション026で判明）
- Claude Code内から`start.sh`を直接実行すると、start.sh内の`osascript close front window`でターミナルが閉じられてセッションが落ちる
- 再起動時はGDriveからコピー→nohupで直接起動すること

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + tmux連携）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード）
- `install_mac.sh` — Mac版インストールスクリプト（tmux自動インストール含む）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
