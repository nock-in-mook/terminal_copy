# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- ブランチ `feature/mac-keyboard-sync` で作業中
- 透明キーボードを即ランチャーに完全統合済み
- **Mac版メニューをWindows版と統一済み**

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — pythonw.exeコピー+アイコン・バージョン情報書き換え済み
- `app.ico` — アイコン（トレイ・exe・ショートカット共通）
- `python3.dll` / `python314.dll` / `python314._pth` — exe用ランタイム
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（即ランチャーEXE + 透明キーボードEXE両方ビルド）
- `_build_exe.py` — exe生成スクリプト
- `_setup_shortcuts.py` — ショートカット作成＆起動（透明キーボードのスタートアップ削除も実行）
- `_setup_wt.py` — WT設定

## デスクトップダブルクリックメニュー（Windows版）
- WH_MOUSE_LLフック + LVM_GETSELECTEDCOUNT でデスクトップ空白ダブルクリック検出
- **Toplevelウィンドウで自作メニュー**（tk_popupは外クリックで閉じないため廃止）
- on_any_clickコールバックで任意クリック時にdismiss（メニュー+サブメニュー両方destroy）
- メニュー構成: OPEN▶ / Show All / Chat / Refresh / Close All
- ChatはOPENサブメニューから独立、トップレベルに配置
- Quit項目は削除（誤爆防止）
- DPI Aware有効化（Per-Monitor V2）でくっきり表示

## デスクトップダブルクリックメニュー（Mac版）
- NSEvent globalMonitor + CGWindowListCopyWindowInfo でデスクトップ空白ダブルクリック検出
- NSMenuのpopUpMenuでネイティブメニュー表示（外クリックで自動的に閉じる）
- メニュー構成: OPEN▶ / Show All / Chat(ellipsis.messageアイコン) / Refresh(arrow.clockwiseアイコン) / Close All
- ChatはOPENサブメニューから独立、トップレベルに配置（SF Symbolsアイコン付き）
- Quit項目は削除（誤爆防止）
- 3秒ポーリングでターミナル閉じたらKBも自動削減+再整列

## 透明キーボード統合
- 透明キーボードは即ランチャーの一部（単体起動なし）
- `一発更新_即ランチャー.bat` で透明キーボードEXEもPyInstallerで自動ビルド
- キーボード起動数は `_launch_keyboards_exact(target_count)` で一元管理
- WT数3秒ポーリングでターミナル閉じたらKBも自動削減+再整列
- **透明キーボード.exeはPyInstaller onefile — .pyを修正してもEXE再ビルド必須**

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu）
- `install_mac.sh` — Mac版インストールスクリプト

## 次のアクション
- feature/mac-keyboard-sync ブランチをmainにマージするか判断
- UDEV Gothicフォント自動インストールをbatに組み込むとベター
