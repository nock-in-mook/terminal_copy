# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- アプリ名を「即ランチャー」に統一済み
- Windows版（folder_launcher_win.pyw）: メニュー簡素化・アイコン統一完了
- Mac版（folder_launcher.py）: 簡素化済み

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `launcher.bat` — 1クリックセットアップ（exe生成・WT設定・ショートカット全自動）
- `_build_exe.py` — exe生成スクリプト（Win32 UpdateResourceW APIでバージョン情報書き換え）
- `_setup_wt.py` — WT設定（ライトテーマ・UDEV Gothic・タイトル維持）

## 今回の変更（ターミナル上端配置）
- MARGIN_TOP_RATIO を 0.10 → 0.0 に変更
- ターミナルが画面上端にぴったり張り付くようになった
- サイズは変わらず、下の隙間が広がるだけ

## 右クリックメニュー構成（Windows版）
- OPEN → フォルダ一覧サブメニュー（1つ選んで即起動）
- ---
- Show All
- ---
- Refresh / Close All / Quit（確認ダイアログ付き）

## 多重起動防止
- Windows Mutex（SokuLauncher_Mutex）で実装済み

## 次のアクション
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
- Mac版も「即ランチャー」名称に合わせるか検討
