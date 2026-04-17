# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: 2台とも **iTerm2 + ARM64 launcher** で安定動作中
- Windows版: 安定稼働中

## 今回の作業（セッション039）

### 透明キーボードのスクショ保存失敗バグを根本修正（別リポジトリ: transparent-keyboard）
「PrScrで範囲選択してもファイルが保存されないことがある」症状を追跡して、**Rosetta継承**が真犯人だと確定した。

- 症状: 透明キーボードのPrScrで範囲選択 → クロスヘア＆四角選択は普通に見えるのに、ファイルが保存されない
- 最初の切り分け:
  - `screencapture -x`（非対話）は成功、`-i`（対話）だけ失敗
  - Python自体に画面収録権限を与えても直らない
  - iTermから手動で `screencapture -i` 実行は成功
- 真因: 即ランチャー（親）が Hammerspoon/launchd チェーンで **x86_64 Rosetta** として起動されてた。子の透明キーボード→孫の screencapture までアーキテクチャ継承され、Rosetta経由のPythonからCoreGraphicsのrect captureを呼ぶと内部で失敗してた（エラー: `could not create image from rect`）
- 対処:
  - `folder_launcher.py` の `_launch_one_keyboard` を `['arch', '-arm64', 'python3', KB_SCRIPT]` に変更
  - `SokuLauncher.app/Contents/MacOS/launcher` の exec 行を `exec /usr/bin/arch -arm64 "/usr/bin/python3" ...` に変更
  - `install_mac.sh` のlauncherテンプレも同様に更新（次のMacセットアップで自動反映）
  - 透明キーボード側: `take_screenshot()` に診断ログ追加＋ファイル名衝突防止（マイクロ秒）＋撮影成功時の自動パスペースト
- 診断用知見: `lsof -p <PID> 2>/dev/null | grep -iE 'rosetta|oah'` で Rosetta 判定
- 動作確認: 2台のMac（appurunoMacBook-Air, KYO-YaguchinoMacBook-Air）で3連続スクショ成功＆自動パスペースト成功
- CLAUDE.md のハマりポイント #13 に全記録、プロジェクトMEMORYにも feedback として保存

### 別Mac への移行・動作確認
- チャット途中で KYO-YaguchinoMacBook-Air に移行
- `~/.claude/projects` が GDrive 同期フォルダへのシンボリックリンクなので、Claude Code セッションも自動同期されてる → `/resume` で即コンテキスト復帰できた
- このMacでも画面収録権限付与 → launcher+keyboard を ARM64 で再起動 → 動作確認OK

## 前回の作業（セッション038）
### iTerm2 導入＋透明キーボードのキー送信バグ修正
- `bash install_mac.sh` 実行でiTerm2、SF Monoフォント等を自動セットアップ
- 透明キーボードのテキスト送信を CGEventPost → osascript（System Events）経由に変更（TCCキャッシュ問題の回避）

## 次のアクション
- 特になし（terminal_copy / transparent-keyboard 両方とも安定稼働継続）
- 他に Apple Silicon Mac を増やすときは install_mac.sh 一発＋権限2つ（アクセシビリティ＋画面収録）で完了

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + **iTerm2** + tmux連携 + ゾンビ掃除 + **arch -arm64 キーボード起動**）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux・Hammerspoon・iTerm2・SF Mono Terminalフォント・**ARM64 launcher** 自動セットアップ、ログイン項目方式）
- `SokuLauncher.app` — ログイン項目用.appラッパー（`~/Library/Application Support/SokuLauncher/` に配置、**arch -arm64** で exec）

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
