# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- デスクトップダブルクリック検知の誤検知バグを修正済み
- 透明キーボードに「Claude」キー追加済み（Mac版・Windows版両方）

## 今回の変更（セッション023）
- `_is_desktop_click` の判定ロジックを大幅改善
- 試行1: `NSWorkspace.frontmostApplication()` でFinderチェック → ターミナル経由だとFinderが最前面にならず失敗
- 試行2: AppleScriptの `insertion location is desktop` → オブジェクト比較が不一致で失敗
- 最終解: `insertion location` のPOSIXパスを `~/Desktop` と比較 → 成功
- これによりデスクトップの空白部分のみに反応し、フォルダウィンドウ内や他アプリ上では反応しなくなった

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（即ランチャーEXE + 透明キーボードEXE両方ビルド）

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu）
- `install_mac.sh` — Mac版インストールスクリプト

## Mac版自動起動（SokuLauncher.app方式）
- `~/Library/Application Support/SokuLauncher/SokuLauncher.app` をログイン項目に登録
- .appの中身は `open -a Terminal start.sh` するだけのシェルスクリプト
- Terminal.app経由で起動するためGDriveアクセス権を継承できる

## 次のアクション
- Windows側で一発更新バッチを実行して透明キーボードEXEを再ビルド（前回からの持ち越し）
