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

## 最新の変更（セッション016）
- **Refreshクラッシュ修正**: pystrayスレッドから直接メニュー再構築→クラッシュの問題を、`root.after(0, ...)`でメインスレッド委譲に変更
- **OPENメニュー仕切り線**: `_Apps2026`内フォルダと`_other-projects`内フォルダの間にセパレータ追加（Win/Mac両方）
- **`get_folders()`をタプル返却に変更**: `(apps_folders, other_folders)` で分けて返す
- **デバッグログ追加**: `launcher_debug.log` に記録（安定したら外す）
- **透明キーボード修正**（透明キーボードリポジトリ側）:
  - IME半角固定バグ修正（起動時にフォーカスを奪わないよう`SetForegroundWindow`で復元）
  - 常時topmost維持を廃止（起動・整列時に一瞬だけtopmost→即解除）

## 次のアクション
- 透明キーボードMac版の横幅をターミナル幅に揃える（後で調整予定）
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
