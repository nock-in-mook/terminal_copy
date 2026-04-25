# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 2台とも **iTerm2 + ARM64 launcher** で稼働
- Windows版: 安定稼働中
- TCC失効問題は根治済み（セッション042）
- メニュー表示位置の自動調整済み（セッション036）

## 今回の作業（セッション037: claude.json 0バイト化事故の調査と再発防止 hook）

### 経緯
- 別プロジェクト（session-recall）で別セッションの Claude が `sed -i 's/"autoUpdates": false/"autoUpdates": true/' ~/.claude.json` を実行 → ファイルが **0バイト化**
- 原因: グローバル `.claude.json` に `autoUpdates: false` キーが存在せず、Windows Git Bash の `sed -i` の一時ファイル→rename がパターン非マッチ時に破綻 → 0バイト
- 結果: Claude Code 自動再生成で `.claude.json` 自体は復活（28KB）。ただし起動回数・プロジェクト履歴・統計値は失われた
- ユーザーが見てた「ターミナルがバグってチャット表示されない」は、事故時に動いてた Claude Code プロセスが画面崩れたまま固まってたゾンビウィンドウ → ウィンドウを閉じて新規起動で解決

### 再発防止策（このプロジェクトの作業）
- `~/.claude/hooks/block_claude_json_write.sh` を新規作成
  - PreToolUse hook（matcher: `Bash`）
  - `.claude.json` を含まないコマンドは即スルー（高速パス）
  - 含む場合だけ Python で `tool_input.command` を抽出
  - 書き込み系パターン（`sed -i` / `>` `>>` redirect / `tee` / `cp` / `mv` / `install` / `dd of=`）を検知して `permissionDecision: "deny"` でハードブロック
  - `--dangerously-skip-permissions` モードでも効く
  - 既存 hook と同じく `bash ~/.claude/hooks/...` 方式
- `~/.claude/settings.json` に PreToolUse エントリを merge（既存の PermissionRequest / SessionStart は保持）
- pipe-test 12ケース（許可6 / ブロック6）全パス
- 注意: 現在のセッションでは settings watcher が `~/.claude/` を見てないため未反映。次回 Claude Code 起動から有効化される

## 次のアクション
- 特になし
- 次セッションから `.claude.json` への Bash 経由書き込みは自動ブロックされる
- もし誤検知やすり抜けがあれば `~/.claude/hooks/block_claude_json_write.sh` の `PATTERN` を調整
