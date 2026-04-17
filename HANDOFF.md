# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: **iTerm2** で安定動作中（複数Macでセットアップ完了）
- Windows版: 安定稼働中

## 今回の作業（セッション038）

### 1. このMacにもiTerm2を導入
- 前セッション037（別Mac）で iTerm2 移行は完了していたが、このMacはまだ未移行だった
- `bash install_mac.sh` を実行 → Homebrew経由でiTerm2、SF Mono Terminalフォントコピー、Hammerspoon設定、ログイン項目登録まで全自動完了
- iTerm2 Profile設定（`Save lines to scrollback in alternate screen mode`、`Title=Session Name` 等）はユーザーが手動で実施
- 動作確認OK：デスクトップダブルクリック → 即ランチャー → iTerm2新ウィンドウ起動、Claude Code履歴がマウスホイールで遡れる

### 2. 透明キーボードのキー送信バグを根本修正（別リポジトリ）
長年再発していた「テキスト送信ボタン無反応、再起動でしか戻らない」症状を解消した。
- 症状: スクショボタンは動くが、テキスト送信系のボタンが軒並み反応しない
- 切り分け: スクショは `subprocess.Popen(['screencapture', ...])` で別プロセス起動、テキストは `CGEventPost` で同プロセスから送信。後者が無言で失敗していた
- 原因: macOS の TCC キャッシュ／code signature 問題で、Python（`com.apple.python3`）への CGEventPost 権限が不安定。TCC.db を更新してプロセス再起動しても直らないケースがあり、macOS再起動で一度だけ治る理由は TCC キャッシュ完全 clear だから
- 対策: `mac/transparent_keyboard_mac.py:83-103` の `type_text` / `send_key` を osascript（System Events）経由に切替。スクショと同じ別プロセス起動方式になり、Python 自身のアクセシビリティ権限が不要に
- リポジトリ: https://github.com/nock-in-mook/transparent-keyboard、コミット `b82746e` で push済み

## 前回の作業（セッション037、別Macで実施）
### Terminal.app → iTerm2 完全移行
- `folder_launcher.py` の全 AppleScript を iTerm2 対応に書き換え
- `install_mac.sh` に iTerm2 自動インストール（Step 2.5）＋ SF Mono Terminal フォント自動コピー（Step 2.6）追加
- 旧 `launcher` スクリプトが `open -a Terminal start.sh` 経由で現行ターミナルを閉じる危険があったので、python3 直接起動方式に戻した
- `CLAUDE.md` に別Macセットアップ手順＋ハマりポイント9〜12を追記

## 次のアクション
- 特になし（terminal_copy 側は安定稼働継続）

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
