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

## 最新の変更（セッション013）
- ターミナル起動時に透明キーボードも自動同時起動
- 整列ロジックを透明キーボードの`_realign_all`と統一
  - MARGIN_BOTTOM 10%→20%（キーボード領域確保）
  - SHADOW_INSET=7（影補正）追加
  - タスクバー除外の作業領域ベース計算
  - キーボードウィンドウもターミナル真下に配置
- Show Allでもキーボード含めて整列
- launcher.batに既存プロセス停止を追加（他PC一発更新対応）

## 次のアクション
- 他のPCでlauncher.bat実行して動作確認する
- UDEV Gothicフォント自動インストールをlauncher.batに組み込むとベター
