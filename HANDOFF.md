# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- アプリ名を「即ランチャー」に統一済み
- DropboxからGoogleドライブへの移行対応完了

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `launcher.bat` — 1クリックセットアップ（exe生成・WT設定・ショートカット全自動）
- `_build_exe.py` — exe生成スクリプト（Win32 UpdateResourceW APIでバージョン情報書き換え）
- `_setup_wt.py` — WT設定（ライトテーマ・UDEV Gothic・タイトル維持）

## 今回の変更（Googleドライブ移行対応）
- APPS_DIRをDropbox→Googleドライブのパスに変更（Win/Mac両方）
- `_other_projects` フォルダ内のサブフォルダもメニューに表示されるように対応
- `resolve_folder_path()` でフォルダ名→実パスを自動解決
- `テレパシーワード` を除外リストに追加
- ショートカット（スタートメニュー・スタートアップ）をGoogleドライブのパスに更新
- `launcher.bat` のショートカット作成を毎回上書き方式に変更

## 右クリックメニュー構成（Windows版）
- OPEN → フォルダ一覧サブメニュー（1つ選んで即起動）
- ---
- Show All（再配置＋前面表示）
- ---
- Refresh / Close All / Quit（確認ダイアログ付き）

## 多重起動防止
- Windows Mutex（SokuLauncher_Mutex）で実装済み

## 旧Dropbox残骸の状況
調査済み。以下が旧パスを参照したまま残っている（未修正）：
- スタートアップ/スタートメニュー: 即シェア君.lnk, 透明キーボード.lnk
- タスクバーピン留め: 透明キーボード.lnk
- デスクトップ: Dropbox.lnk, experiment.lnk, stock_data.lnk, 透明キーボード.lnk
- レジストリ: スタートメニュータイルキャッシュ（放置OK）

## 次のアクション
- 他プロジェクト（Data_Share, 透明キーボード等）のDropbox→Googleドライブ移行対応
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
