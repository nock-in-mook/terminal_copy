# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: **iTerm2** で安定動作中（自動起動はログイン項目方式）
- Windows版: 安定稼働中

## 今回の作業（セッション037）
### Terminal.app → iTerm2 完全移行

**きっかけ**: 前セッション036で「代替スクリーンをスクロール」をOFFにして治ったと思ったが、実は錯覚。Terminal.app は alt screen（Claude Code のTUI）の内容を scrollback に一切保存しない仕様で、マウスホイールで遡っても見えるのはシェル起動直後のログだけだった。

**解決**: iTerm2 に完全移行。iTerm2 には `Save lines to scrollback in alternate screen mode` という Terminal.app にない設定があり、これで Claude Code の会話履歴がそのまま scrollback に流れてマウスホイールで遡れるようになった。

**主な変更**:
- `folder_launcher.py` の全 AppleScript を iTerm2 対応に書き換え
- `install_mac.sh` に iTerm2 自動インストール（Step 2.5）＋ SF Mono Terminal フォント自動コピー（Step 2.6）追加
- 旧 `launcher` スクリプトが `open -a Terminal start.sh` 経由で現行ターミナルを閉じる危険があったので、python3 直接起動方式（install_mac.sh 正規版）に戻した
- `CLAUDE.md` に別Macセットアップ手順＋ハマりポイント9〜12を追記

## 次のアクション
- 別Macにセットアップする場合: ユーザーに「プロジェクトの `CLAUDE.md` を読んで、あとは頼む」と言ってもらい、Claudeが手順を案内する（`bash install_mac.sh` → アクセシビリティ許可 → iTerm2 Profile設定）
- 既存Mac側は移行完了、特になし

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + NSEvent + NSMenu + NSStatusItem + **iTerm2** + tmux連携 + ゾンビ掃除）
- `hammerspoon_init.lua` — Hammerspoon設定（グローバル変数でGC対策済み、GDrive監視で自動リロード、透明キーボード除外）
- `install_mac.sh` — Mac版インストールスクリプト（tmux・Hammerspoon・**iTerm2**・SF Mono Terminalフォント 自動セットアップ、ログイン項目方式）
- `SokuLauncher.app` — ログイン項目用.appラッパー（`~/Library/Application Support/SokuLauncher/` に配置）

## iTerm2 Profile設定（セットアップ後の手動作業）
- `Terminal` タブ: **Save lines to scrollback in alternate screen mode** ON（肝）
- `General` タブ: `Title` を `Session Name` に、`Applications in terminal may change the title` OFF
- `Text` タブ: Change Font → `SF Mono Terminal Regular 12pt`（Terminal.app時代と同じ見た目）

## Windows版の構成
- `folder_launcher_win.pyw` — メイン（pystray + tkinter + WH_MOUSE_LL）
- `即ランチャー.exe` — **`%LOCALAPPDATA%\即ランチャー\` に配置**（pythonw.exeコピー+アイコン書き換え済み）
- `一発更新_即ランチャー.bat` — 1クリックセットアップ（Python自動インストール対応）
- ショートカットは .pyw を引数で渡す方式なので、コード修正だけで反映される
