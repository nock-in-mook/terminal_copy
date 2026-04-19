# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 2台とも **iTerm2 + ARM64 launcher** で安定動作中
- Windows版: 安定稼働中
- 直近で **ランチャー無反応バグ（NSLog未import）** と **スクショTCC陳腐化** の2件を根本解決

## 今回の作業（セッション041）

### スクショTCCキャッシュ陳腐化問題の対処
前セッション（040）でランチャー無反応バグ修正後、同日夕方に透明キーボードのPrScrが再び失敗するようになった。

**症状**: 透明キーボード PrScrで `could not create image from rect` が連発。シェルから直接 `screencapture -x` を試しても `could not create image from display` で失敗。

**原因特定の流れ**:
- プロセスの Rosetta チェック → 全部 ARM64（`lsof | grep -iE 'rosetta|oah'` で0件）
- なので Rosetta は犯人じゃない
- シェルから直接 `screencapture -x` もダメ → **画面収録権限自体が効いてない**状態
- システム設定を開いて確認 → **iTerm の画面収録権限が無かった**（ユーザー操作で追加＆ON）
- Python.app は最初から ON

**対処**:
- iTerm の画面収録権限を追加＆ON
- 透明キーボードを kill → 再起動（TCC キャッシュ再読込）
  ```
  pkill -f transparent_keyboard_mac.py
  arch -arm64 /usr/bin/python3 "/Users/nock_re/Library/Application Support/SokuLauncher/folder_launcher.py" --show-all
  ```

**動作確認**: PrScr 2連続成功（16:33:17 rc=0 saved=True size=92217、16:34:11 rc=0 saved=True size=33969）

**CLAUDE.mdハマりポイント#13に予防策として追記**: 「TCCキャッシュ陳腐化」パターンの識別方法（シェルから `-x` も失敗したらこれ）＋対処コマンド。

### コミット
- `1ffcd85` ハマりポイント#13に追記: TCCキャッシュ陳腐化で同エラー再発するパターン

## 前セッションの作業（セッション040）

### 即ランチャー無反応バグ（約50%の確率で開かない）を根本修正
真犯人は `_cleanup_zombie_tmux_sessions()` 内の `NSLog` が未import で NameError。デタッチ tmux 有時のみ発動。対処: `NSLog` → `_log()` 置換、`_run_applescript` に10秒タイムアウト、診断ログ `/tmp/sokulauncher_launch.log` 整備。CLAUDE.mdハマりポイント#14 に記録。コミット: `5e1addf`。

## 次のアクション
- 特になし（terminal_copy は安定稼働継続）
- もう一台の Mac への反映は **launcher 再起動だけ**でOK（GDrive 経由で `folder_launcher.py` が自動同期される仕組み）
  ```
  pkill -f folder_launcher.py
  open -a "/Users/nock_re/Library/Application Support/SokuLauncher/SokuLauncher.app"
  ```
- もしもう一台の Mac で同じ TCC 陳腐化が出たら、上のpkill手順を参考に透明キーボードも再起動する

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
   - **画面収録**: Python.app（Xcode.app内） + **iTerm** を ON ← iTerm も必要
4. iTerm2 Profile設定（CLAUDE.md Step 3 参照）
5. SokuLauncher.app ダブルクリック起動 → デスクトップダブルクリックで動作確認

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — `%LOCALAPPDATA%\即ランチャー\` に配置（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される

## 診断の勘どころ
- ランチャー系の症状（無反応、固まる、等）: **`/tmp/sokulauncher_launch.log`** を最初に見る
- スクショ系: **`/var/folders/.../T/claude_screenshots/_screenshot.log`**（透明キーボード側）
- スクショ失敗時:
  1. `lsof -p <PID> 2>/dev/null | grep -iE 'rosetta|oah'` → 何か出たら Rosetta 継承問題（#13）
  2. シェルから `screencapture -x /tmp/test.png` → `could not create image from display` なら TCC 陳腐化（#13 追記）→ iTerm/Python.app 権限確認＋透明キーボード再起動
  3. `-x` 成功するが `-i` だけ失敗なら、別の原因を調査
