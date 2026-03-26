# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: tmux復帰機能＋ゾンビ掃除追加済み、Hammerspoon自動リロード追加済み、安定動作中
- Windows版: マウスフック完全軽量化済み（セッション019）

## 今回の変更（セッション029）
### 透明キーボード上のダブルクリックで即ランチャーが開く問題を修正
- **原因**: NSPanel（透明キーボードのウィンドウ）はHammerspoonの`hs.window.orderedWindows()`に列挙されない → キーボード上のクリックが「デスクトップ」と誤判定
- **修正**: 透明キーボードが自分の位置を`/tmp/transparent_keyboard_bounds.json`に書き出し、Hammerspoonの`isDesktopClick`でそのファイルを読んで除外判定
- ファイルロック付きで複数インスタンスの競合を防止
- ドラッグ移動後にも位置を更新するようにした

### 透明キーボードのキーが反応しない問題（未解決）
- **症状**: mouseDown_がNSViewに一切届かない。NSButton、NSWindow、NSPanelいずれでも同じ
- **調査結果**: Python 3.9 + PyObjC 12.0、Python 3.12 + PyObjC 12.1の両方で再現。PyObjCのバージョン問題ではない
- **推定原因**: macOS 26のウィンドウサーバーまたはTCCデーモンの一時的な不具合
- **対処**: Mac再起動で治る可能性が高い → ユーザーが再起動予定

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
- **Mac再起動後に透明キーボードのキー入力が復活するか確認**（最優先）
- 復活しなければ、PyObjCのmouseDown_ではなくNSEvent.addLocalMonitorを使うアプローチを検討
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
