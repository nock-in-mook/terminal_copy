# 引き継ぎメモ

## 現在の状況
- Mac側のGit環境構築完了（git config + gh CLI + GitHub認証）
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- GitHub情報はグローバルMEMORY.md + shared-envに保存済み（全セッション共通）
- `/remote-control` 実行時のSlack URL通知がMacでも動作するようになった
  - `remote_url_monitor_mac.sh` を新規作成
  - `start_remote_monitor.sh` のmacOS分岐を修正
  - `~/.claude/slack_webhook_url` のsymlinkを修正
- フォルダランチャー（folder_launcher.py）完成・常駐化済み
  - メニューバーに📂アイコンで常駐
  - _Apps2026内のフォルダ一覧を表示、クリックでcdコマンドをクリップボードにコピー
  - LaunchAgentで自動起動設定済み

## 次のアクション
- Windows版フォルダランチャーの作成（システムトレイ常駐）
- 必要に応じて機能追加（アイコンカスタマイズ等）
