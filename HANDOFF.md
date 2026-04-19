# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 2台とも **iTerm2 + ARM64 launcher** で稼働
- Windows版: 安定稼働中
- **長年の「1日経つと透明キーボードのPrScrが無言失敗する」問題を根治**（セッション042）

## 今回の作業（セッション042）

### スクショ TCC 失効問題の根治: Hammerspoon → AppleScript → iTerm 経由 spawn
朝、透明キーボードの PrScr が即失敗する症状が再発。前セッション（041）の「TCC陳腐化」対処（kill → 再起動）では一時しのぎで、**翌日また失敗する** ことが判明。根本原因と恒久対策を探った。

**原因の切り分け**:
- シェル直接 `screencapture -x/-R/-i` は全部成功 → TCC target（Python.app）の権限は生きてる
- 透明キーボード経由 `-i` だけ失敗 → プロセス側の **responsible chain 陳腐化**
- `open -a SokuLauncher.app`（ログイン項目起動）経由だと LaunchServices responsible chain で長時間後に失効する、と判明
- Hammerspoon 直接 spawn も失敗 → Hammerspoon は LSUIElement（Dock非表示のバックグラウンドアプリ）なので、子プロセスの `screencapture -i` overlay UI が却下される模様
- **前景アプリ iTerm 配下で起動した launcher 配下の透明キーボードは通る** ことを確認

**解決設計**:
- **SokuLauncher.app のログイン項目登録を廃止**。Hammerspoon をログイン項目に登録
- Hammerspoon 起動時に `hs.osascript.applescript` で iTerm にコマンド投入:
  ```
  tell application "iTerm"
      set newWindow to (create window with default profile)
      tell current session of newWindow to write text "(nohup arch -arm64 python3 folder_launcher.py ... & sleep 2; nohup arch -arm64 python3 folder_launcher.py --show-all ... &); exit"
  end tell
  ```
- iTerm session で `& disown` + `exit` → iTerm window は即 close、launcher は独立
- launcher 側は `_SOKU_DAEMONIZED` フラグ + `subprocess.Popen` 自己 re-exec で完全独立（iTerm から切れても生き残る）

**自動復旧と早朝予防**:
- 透明キーボード `_trigger_recovery()` は失敗検知で `/tmp/sokulauncher_restart_requested` を touch するだけに変更
- Hammerspoon が 3 秒ポーリングでそれを検知 → 全 kill → 同じ AppleScript 経路で再 spawn
- `hs.timer.doAt("04:00", "1d", ...)` で毎日4時に予防的再起動

**重要な発見（daemonize の罠）**:
AppKit import 済みの Python で `os.fork()` すると Apple Silicon 上で `NSResponder initialize ... fork() called ... Crashing` で即クラッシュする（Objective-C runtime と pthread の競合）。daemonize には必ず **`subprocess.Popen` で exec し直す方式** を使う。CLAUDE.md #15 に記載。

### コミット
- `e916cdb` Hammerspoon経由launcher管理に再設計: open-a起動によるTCC chain陳腐化を根治（最初の実装、後で AppleScript 経由に上書き）
- `8357c48` launcher を AppleScript 経由で iTerm から spawn する方式に変更（最終形）
- 透明キーボード側: `ded348c` PrScr失敗時の自動復旧を Hammerspoon 依頼方式に変更

## 次のアクション
- **再起動後も効くか次回ログイン時に検証**（Hammerspoon が起動時に AppleScript で iTerm 経由で launcher spawn する流れ）
- もう一台の Mac も GDrive 同期で `hammerspoon_init.lua` / `folder_launcher.py` が伝わる。次回起動時から新方式が効く
- 何かおかしくなったら `/tmp/hs_spawn.log`、`/tmp/sokulauncher_stdout.log`、`/tmp/sokulauncher_stderr.log` を見る

## 動作確認済み事項
- Hammerspoon 再起動 → iTerm 経由で launcher 56516 + 透明キーボード 3 つ自動 spawn
- その配下で PrScr 成功（`ss_20260419_172513_733143.png`、タスクリスト画面が正しく撮れた）
- iTerm window は exit で即 close、ユーザー視点のウィンドウ総数±0

## Mac版の構成（2026-04-19 更新）
- `folder_launcher.py` — メイン（**_SOKU_DAEMONIZED フラグによる subprocess.Popen 自己 re-exec 付き**）
- `hammerspoon_init.lua` — Hammerspoon 設定:
  - デスクトップダブルクリック検知（従来通り）
  - **launcher の管理（AppleScript 経由で iTerm に spawn 依頼）**
  - 毎日 04:00 の予防的再起動
  - `/tmp/sokulauncher_restart_requested` の 3 秒ポーリングで自動復旧
- `install_mac.sh` — **Hammerspoon のみログイン項目に登録**（SokuLauncher.app 登録は削除済み）
- `restart_launcher.sh` — 手動復旧用の薄いラッパー（`touch /tmp/sokulauncher_restart_requested` するだけ）
- `SokuLauncher.app` — 手動起動用の wrapper は残す（緊急時の Finder ダブルクリック用）

## 新規Macセットアップ手順
1. GDrive（Google Drive for Desktop）インストール＋同期
2. `cd /Users/.../マイドライブ/_Apps2026/terminal_copy && git pull && bash install_mac.sh`
3. システム設定 → プライバシーとセキュリティ:
   - **アクセシビリティ**: Hammerspoon.app + Python.app（Xcode.app内）+ **iTerm** を ON
   - **画面収録**: Python.app（Xcode.app内）+ **iTerm** を ON
   - **オートメーション**: Hammerspoon → iTerm を許可（AppleScript 経由でコマンド打つため）
4. iTerm2 Profile設定（CLAUDE.md Step 3 参照）
5. Hammerspoon 起動すれば launcher 自動 spawn → 動作確認

## 診断の勘どころ
- ランチャーが立ち上がらない: `/tmp/hs_spawn.log` → AppleScript の ok/err / pgrep 判定結果を見る
- スクショ失敗が再発: シェル直 `screencapture -i /tmp/x.png` が通るか確認
  - 通る: 透明キーボードプロセス特有 → `touch /tmp/sokulauncher_restart_requested` で復旧
  - 通らない: TCC の target 側の問題 → システム設定で画面収録権限を再確認
- iTerm window が画面に残ってる: AppleScript の `exit` がうまく効いてない → Profile の「When the session ends」を「Close the session」に設定

## Windows版の構成（変更なし）
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — `%LOCALAPPDATA%\即ランチャー\` に配置
- `一発更新_即ランチャー.bat` — 1クリックセットアップ
