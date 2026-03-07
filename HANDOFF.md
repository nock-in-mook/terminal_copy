# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Windows版フォルダランチャー（folder_launcher_win.pyw）完成・動作確認済み
- Mac版フォルダランチャー（folder_launcher.py）大幅簡素化・動作確認済み

## Mac版の変更点（今セッション）
- AppKitでDock幅を動的取得し、左マージンに反映
- ウィンドウ幅を画面幅の20%（1/5）に変更
- split系メニュー（2/3/4 split）を廃止し、[OPEN]サブメニュー一本に簡素化
- MAX_TERMINALS を4に変更
- フォルダ大量時（44個テスト済み）もスクロールで問題なし
- close_allの確認ダイアログを1回に簡素化

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
- デバッグログ（logging）を本番では削除 or 無効化を検討
- launcher.batにUDEV Gothicフォント自動インストール処理を追加するとベター
- Terminal.appフルスクリーン問題: Ctrl+Command+F で手動解除が必要
