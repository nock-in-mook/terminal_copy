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
- `install_mac.sh` — Mac版インストールスクリプト（.app作成+LaunchAgent登録）
- `/Applications/即ランチャー.app` — インストール先
- `~/Library/Application Support/SokuLauncher/folder_launcher.py` — ローカルコピー（GDrive権限問題回避）
- `~/Library/LaunchAgents/com.sokulauncher.agent.plist` — 自動起動+KeepAlive
- メニューバーにカスタムアイコン（フォルダ+キーボード）で表示
- Keyboardトグルメニュー追加

## Mac版インストール仕様（セッション016で追加）
- `install_mac.sh` 1つで全自動: .appバンドル作成 → LaunchAgent登録 → 起動
- **自動起動**: RunAtLoad（Mac起動時に自動起動）
- **自動復帰**: KeepAlive（落ちても5秒後に自動再起動）
- **自動更新**: 起動時にGoogleドライブから最新版をローカルにコピー
- ログ: `/tmp/sokulauncher_stdout.log`, `/tmp/sokulauncher_stderr.log`
- Pythonパス: `/Applications/Xcode.app/Contents/Developer/usr/bin/python3`（rumpsインストール済み）

## フォルダ探索の仕様
- `_Apps2026` 直下のフォルダを表示
- 除外: `images`, `text`, `テレパシーワード`, `others`, `_other_projects`, `即Claude`
- マイドライブ直下の `_other-projects`（ハイフン）内のサブフォルダも表示対象
- Win版・Mac版ともに対応済み

## 右クリック/メニュー構成
- OPEN → フォルダ一覧サブメニュー（1つ選んで即起動）
- Show All（再配置＋前面表示）
- ⌨ Keyboard（トグル）
- Refresh / Close All / Quit

## 多重起動防止
- Windows: Mutex（SokuLauncher_Mutex）
- Mac: なし（rumpsの制約）

## 次のアクション
- 透明キーボードMac版の横幅をターミナル幅に揃える（後で調整予定）
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
- folder_launcher.pyにカスタムアイコン+Keyboardトグルが追加された（ユーザーが手動で変更）ので、次回install_mac.sh実行時にローカルコピーにも反映される
