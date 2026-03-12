# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- ブランチ `feature/mac-keyboard-sync` で作業中
- 透明キーボードを即ランチャーに完全統合済み

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（即ランチャーEXE + 透明キーボードEXE両方ビルド）
- `_build_exe.py` — exe生成スクリプト（Win32 UpdateResourceW APIでバージョン情報書き換え）
- `_setup_shortcuts.py` — ショートカット作成＆即ランチャー起動（透明キーボードのスタートアップ削除も実行）
- `_setup_wt.py` — WT設定（ライトテーマ・UDEV Gothic・タイトル維持）

## 透明キーボード統合
- 透明キーボードは即ランチャーの一部（単体起動なし）
- `一発更新_即ランチャー.bat` で透明キーボードEXEもPyInstallerで自動ビルド
- 透明キーボードのスタートアップ登録は `_setup_shortcuts.py` で削除
- 透明キーボードの自動起動ロジック（スロット0が追加インスタンス起動）は削除済み
- キーボード起動数は即ランチャーの `_launch_keyboards_exact(target_count)` で一元管理
- WT数ポーリング（3秒ごと）でターミナル閉じたらKBも自動削減+再整列
- **透明キーボード.exeはPyInstaller onefile — .pyを修正してもEXE再ビルド必須**

## デスクトップダブルクリック（Windows版）
- WH_MOUSE_LLフックでマウスクリックを監視
- ダブルクリック判定（400ms以内、10px以内）
- WindowFromPoint → クラス名がWorkerW/Progman/SysListView32/SHELLDLL_DefViewか判定
- LVM_GETSELECTEDCOUNT（0x1032）でアイコン選択中ならスルー
- 空白ダブルクリック → tkinterポップアップメニューをカーソル位置に表示
- 64bit環境: WindowFromPoint/CallNextHookExのargtypes設定必須

## DPI Aware
- `SetProcessDpiAwareness(2)` Per-Monitor DPI Aware V2
- SHADOW_OVERLAP/SHADOW_INSETはDPI_SCALEで自動スケーリング
- tkinterポップアップもくっきり表示

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent、デスクトップダブルクリック方式）
- `install_mac.sh` — Mac版インストールスクリプト（Terminal.app経由ログイン項目登録）
- `~/Library/Application Support/SokuLauncher/` — ローカルコピー置き場

## フォルダ探索の仕様
- `_Apps2026` 直下のフォルダを表示
- 除外: `images`, `text`, `テレパシーワード`, `others`, `_other_projects`, `即Claude`
- マイドライブ直下の `_other-projects`（ハイフン）内のサブフォルダも表示対象

## 多重起動防止
- Windows: Mutex（SokuLauncher_Mutex）
- Mac: PIDファイル（/tmp/sokulauncher.pid）

## 次のアクション
- feature/mac-keyboard-sync ブランチをmainにマージするか判断
- UDEV Gothicフォント自動インストールをbatに組み込むとベター
