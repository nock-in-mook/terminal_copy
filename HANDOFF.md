# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 2台とも **iTerm2 + ARM64 launcher** で安定動作中
- Windows版: 安定稼働中
- **今セッションで「即ランチャーからiTerm2を開いても50%くらい無反応」の長年バグを根本解決**

## 今回の作業（セッション040）

### 即ランチャーのフォルダ選択が約50%無反応だった問題を根本修正

**症状**: 即ランチャーのメニューからフォルダを選んでも、無反応でiTerm2ウィンドウが開かない。再現率は五分五分、条件不明だった。

**手順**: まず `folder_launcher.py` の `open_terminal` / `openFolder_` / `_run_applescript` に診断ログと AppleScript タイムアウト（10秒）を仕込み、`/tmp/sokulauncher_launch.log` に記録するようにした。ユーザーに再現してもらってログを取得 → 即座に真犯人判明。

**真犯人**: `_cleanup_zombie_tmux_sessions()` 内で `NSLog(...)` を呼んでいるが **`NSLog` は import されていない**。デタッチ済み tmux セッションがあるときだけ kill 通知で `NSLog` が走り、`NameError: name 'NSLog' is not defined` で例外。`except` 内でも再度 `NSLog` を呼んでいるため二重例外になり、`open_terminal` 全体が吹き飛んで iTerm2 ウィンドウが開かない。

**条件分岐の正体**: iTerm2 を ×で閉じた直後（＝デタッチ tmux セッション残存）だけ失敗。フレッシュな状態や、tmux 掃除対象がない場合は成功 → 再現率が「約50%」にばらついてた。

**対処**:
- `NSLog` を `_log()`（`/tmp/sokulauncher_launch.log` 書き込みヘルパー）に置換
- `_run_applescript` にタイムアウト10秒＋失敗ログを追加（iTerm2無反応時の無限待ち防止）
- `openFolder_` / `open_terminal` の各ステップを `/tmp/sokulauncher_launch.log` に記録
- CLAUDE.md ハマりポイント#14 として全記録

**動作確認**: 3連続成功、デタッチtmuxの kill 通知も `_log` 経由で正しく記録された（`デタッチ済みtmuxセッションをkill: Chat`）。

### コミット
- `5e1addf` ランチャー無反応バグ修正: NSLog未import + 診断ログ整備

## 前回の作業（セッション039）
- 透明キーボードのPrScrが Rosetta 継承で失敗していた問題を `arch -arm64` 明示で解決
- 2台の Apple Silicon Mac で動作確認済み

## 次のアクション
- 特になし（terminal_copy は安定稼働継続）
- もう一台の Mac への反映は **launcher 再起動だけ**でOK（GDrive 経由で `folder_launcher.py` が自動同期される仕組み）
  ```
  pkill -f folder_launcher.py
  open -a "/Users/nock_re/Library/Application Support/SokuLauncher/SokuLauncher.app"
  ```
- 急がなければ次の Mac 再起動時に自動反映

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + **iTerm2** + tmux連携 + ゾンビ掃除 + **arch -arm64 キーボード起動** + **診断ログ `/tmp/sokulauncher_launch.log`**）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux・Hammerspoon・iTerm2・SF Mono Terminalフォント・**ARM64 launcher** 自動セットアップ、ログイン項目方式）
- `SokuLauncher.app` — ログイン項目用.appラッパー（`~/Library/Application Support/SokuLauncher/` に配置、**arch -arm64** で exec、起動時に GDrive から最新 folder_launcher.py を自動コピー）

## 新規Macセットアップ手順
1. GDrive（Google Drive for Desktop）インストール＋同期
2. `cd /Users/.../マイドライブ/_Apps2026/terminal_copy && git pull && bash install_mac.sh`
3. システム設定 → プライバシーとセキュリティ:
   - **アクセシビリティ**: Hammerspoon.app + Python.app（Xcode.app内） をON
   - **画面収録**: Python.app（Xcode.app内） をON
4. iTerm2 Profile設定（CLAUDE.md Step 3 参照）
5. SokuLauncher.app ダブルクリック起動 → デスクトップダブルクリックで動作確認

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — `%LOCALAPPDATA%\即ランチャー\` に配置（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 診断の勘どころ
- 即ランチャー系の症状（無反応、固まる、等）が出たら **`/tmp/sokulauncher_launch.log`** を最初に見る
- 各ステップ（`openFolder_ clicked` → `open_terminal START` → `zombie cleanup dur=...` → `create_window dur=... tty='...'` → `open_terminal END`）が記録される
- 途中で途切れてたら、その直前が犯行現場
- スクショ系は `/tmp/claude_screenshots/_screenshot.log`（透明キーボード側）
- Rosetta 疑い: `lsof -p <PID> 2>/dev/null | grep -iE 'rosetta|oah'`
