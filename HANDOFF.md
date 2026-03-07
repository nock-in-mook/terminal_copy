# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Windows版フォルダランチャー（folder_launcher_win.pyw）完成・動作確認済み
- Mac版フォルダランチャー（folder_launcher.py）をWindows版と同等機能に改良済み（未テスト部分あり）

## Mac版の変更点（今セッション）
- cdコピーのみだった旧版を全面改修
- Terminal.app + AppleScriptでターミナル起動・配置
- **左寄せ配置**（Dockが左にあるため。Windows版は右寄せ）
- rumpsのサブメニューで2/3 split選択（tkinter不要）
- claude --dangerously-skip-permissions 自動起動
- images/textフォルダ除外
- メニュー構成: 1 single → 2 split → 3 split → (区切り) → Show All → (区切り) → Refresh / Close All / Quit

## Mac環境設定
- タイトルバーダブルクリック → 「何もしない」に変更済み（AppleActionOnDoubleClick=None）
- osascriptのキー操作送信は権限なし（アクセシビリティ未許可）

## Windows版の機能（folder_launcher_win.pyw）
- pystray + tkinter、トレイアイコン常駐
- WT最大3ウィンドウ、画面幅95%を3分割固定幅、右寄せ配置
- 影の重なり補正 SHADOW_OVERLAP=14px
- 一発セットアップ（launcher.bat）
- フォント: UDEV Gothic

## 次のアクション
- Mac版の動作テスト（1 single / 2 split / 3 split / Show All / Close All）
- ウィンドウ配置の微調整（影の補正が不要か確認、マージン調整）
- Terminal.appフルスクリーン問題: Ctrl+Command+F で手動解除が必要（osascriptキー操作は権限不足）
- launcher.batにUDEV Gothicフォント自動インストール処理を追加するとベター
