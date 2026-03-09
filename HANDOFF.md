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
- `launcher.bat` — 1クリックセットアップ（exe生成・WT設定・ショートカット・起動を全自動）
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

## 最新の変更（セッション011）
- ショートカット作成をPythonスクリプト(_setup_shortcuts.py)に移行（launcher.batの日本語パス変数展開問題を修正）
- Win版: _other-projects（ハイフン、マイドライブ直下）を正しく参照するよう修正
- othersを除外リストに追加
- プロセス名が「即ランチャー」として正しく表示されることを確認

## 次のアクション
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
- 別PCでlauncher.bat実行して動作確認する
