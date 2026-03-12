# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- アプリ名を「即ランチャー」に統一済み
- DropboxからGoogleドライブへの移行対応完了（Win/Mac両方）
- ブランチ `feature/mac-keyboard-sync` で作業中

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
- `folder_launcher.py` — メイン（NSApplication + NSEvent、デスクトップダブルクリック方式）
- `install_mac.sh` — Mac版インストールスクリプト（Terminal.app経由ログイン項目登録）
- `~/Library/Application Support/SokuLauncher/` — ローカルコピー置き場
  - `folder_launcher.py` — GDriveからコピーされた最新版
  - `start.sh` — 起動スクリプト（GDrive→ローカルコピー→python3起動→ウィンドウ自動クローズ）
- デスクトップダブルクリック → ポップアップメニュー（OPENサブメニュー展開）
- Terminal.app経由起動でGDriveアクセス権を継承
- キーボード同期（ターミナル数 = キーボード数、同じ幅・真下密着）
- キーボードヘッダにフォルダ名を角丸枠付きで表示

## Mac版インストール仕様（セッション017で変更）
- `install_mac.sh` 1つで全自動: start.sh作成 → ログイン項目登録 → 起動
- **自動起動**: ログイン項目（Terminal.app経由）でMac起動時に自動起動
- **自動更新**: 起動時にGoogleドライブから最新版をローカルにコピー
- **GDriveアクセス**: Terminal.appの権限を継承（LaunchAgent方式はGDriveアクセス不可だった）
- **多重起動防止**: PIDファイル方式（/tmp/sokulauncher.pid）
- ログ: `/tmp/sokulauncher_stdout.log`, `/tmp/sokulauncher_stderr.log`
- Pythonパス: `/usr/bin/python3`（Xcode版Pythonにリダイレクト、PyObjCインストール済み）

## フォルダ探索の仕様
- `_Apps2026` 直下のフォルダを表示
- 除外: `images`, `text`, `テレパシーワード`, `others`, `_other_projects`, `即Claude`
- マイドライブ直下の `_other-projects`（ハイフン）内のサブフォルダも表示対象
- Win版・Mac版ともに対応済み

## メニュー構成（デスクトップダブルクリック）
- OPEN → サブメニュー展開でフォルダ一覧
- [Show All]（再配置＋前面表示）
- [Close All] / [Quit]

## タイトルバー維持
- tty → フォルダ名のマッピング（_tty_titles辞書）
- 3秒ごとにNSTimerで_refresh_titles()を呼び出し、AppleScriptでcustom titleを上書き
- Claude Codeがタイトルを上書きするため、せめぎ合いが発生する（仕様）
- キーボードヘッダにもフォルダ名を表示（こちらはチカチカしない）

## 透明キーボードMac版の変更（セッション017）
- yellowテーマ追加（7種統一）
- 📷↑を2行にまたがるボタンに変更、📁ボタン削除
- 📷↑とPrScrをアクセントカラーに
- 🪟🪟→Term表記に変更
- ヘッダ高さ倍増（18→36px）、角丸枠付きフォルダ名表示
- Alpha 0.8、起動時2秒だけフローティング→level 0に降格

## 多重起動防止
- Windows: Mutex（SokuLauncher_Mutex）
- Mac: PIDファイル（/tmp/sokulauncher.pid）

## 次のアクション
- feature/mac-keyboard-sync ブランチをmainにマージするか判断
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
- ターミナルタイトルのチカチカ問題は現状仕様（Claude Code側の制御が必要）
