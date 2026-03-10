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
- 除外: `images`, `text`, `テレパシーワード`, `others`, `_other_projects`, `即Claude`
- マイドライブ直下の `_other-projects`（ハイフン）内のサブフォルダも表示対象
- Win版・Mac版ともに対応済み

## 右クリック/メニュー構成
- OPEN → フォルダ一覧サブメニュー（1つ選んで即起動）
- Show All（再配置＋前面表示）
- Refresh / Close All / Quit

## 多重起動防止
- Windows: Mutex（SokuLauncher_Mutex）
- Mac: なし（rumpsの制約）

## 最新の変更（セッション015）
- Mac版をWindows版に合わせて大幅改良
  - フォルダ探索パスを`_other-projects`（ハイフン、マイドライブ直下）に修正
  - 除外フォルダに`others`、`即Claude`追加
  - Show Allでキーボード同期+再配置+activate
  - Close Allで確認2回+キーボードも全閉じ
  - 透明キーボード同期機能追加（ターミナル数=キーボード数）
  - `--show-all`コマンドラインオプション追加
- ターミナル高さを75%に変更（下25%キーボード領域）
- ターミナル真下に透明キーボードを密着配置（macOS座標系変換・メニューバー高さ補正）
- 透明キーボードMac版に`--x`/`--y`引数で初期位置指定対応
- 透明キーボードMac版の起動上限を3に変更（flock排他→3スロット制）

## 次のアクション
- Windows版で一発更新bat実行してビルド＆動作確認
- 透明キーボードMac版の横幅をターミナル幅に揃える（後で調整予定）
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
