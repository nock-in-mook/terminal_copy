# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- アプリ名を「即ランチャー」に統一済み
- DropboxからGoogleドライブへの移行対応完了（Win/Mac両方）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `launcher.bat` — 1クリックセットアップ（既存停止・exe生成・WT設定・ショートカット・起動を全自動）
- `_build_exe.py` — exe生成スクリプト（Win32 UpdateResourceW APIでバージョン情報書き換え）
- `_setup_shortcuts.py` — ショートカット作成＆即ランチャー起動（日本語パス対応）
- `_setup_wt.py` — WT設定（ライトテーマ・UDEV Gothic・タイトル維持）

## Mac版の構成
- `folder_launcher.py` — メイン（rumps + AppKit）
- メニューバー📂アイコンから操作

## フォルダ探索の仕様
- `_Apps2026` 直下のフォルダを表示
- 除外: `images`, `text`, `テレパシーワード`, `others`, `_other_projects`
- マイドライブ直下の `_other-projects`（ハイフン）内のサブフォルダも表示対象
- Win版・Mac版ともに対応済み

## 右クリック/メニュー構成
- OPEN → フォルダ一覧サブメニュー（1つ選んで即起動）
- Show All（再配置＋前面表示）
- Refresh / Close All / Quit

## 多重起動防止
- Windows: Mutex（SokuLauncher_Mutex）
- Mac: なし（rumpsの制約）

## 最新の変更（セッション014）
- 透明キーボードの起動をEXE優先に変更（PyInstallerビルド、Tcl同梱）
- EXEがない場合は`py -3.14`フォールバック（`py -3`は禁止ルール化）
- TCL_LIBRARY環境変数汚染の問題を修正（即ランチャーが3.10のTclパスを設定→子プロセスに伝播）
- 透明キーボードEXEを再ビルド（TCL_LIBRARY除去してビルド、tkinter同梱確認済み）
- ターミナル数とキーボード数の同期機能を追加
  - `_sync_keyboards()`: ターミナル数に合わせてキーボードを増減
  - ターミナル追加時・Show All時に同期
  - Close All時にキーボードも全て閉じる
- グローバルCLAUDE.mdに「`py -3`禁止、必ず`py -3.14`指定」ルールを追加

## 次のアクション
- 他のPCでlauncher.bat実行して動作確認する
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
