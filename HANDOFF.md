# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Mac版: **iTerm2** で安定動作中（複数Macでセットアップ完了）
- Windows版: 安定稼働中
- 透明キーボード: Screen Recording 権限 + ARM64 強制起動で**スクショ機能が完全復活**

## 今回の作業（セッション039）

### 透明キーボードのPrScr（スクショボタン）を完全に直した

**長年の症状**: 「範囲を囲んでも保存されない」「一度ダメになると戻らない」

**真犯人**: **Rosetta 2 (x86_64) 継承**
- launcher (folder_launcher.py) が Hammerspoon/launchd 経由で x86_64 Rosetta として起動していた
- 子の透明キーボード、さらに孫の `screencapture -i` までアーキテクチャ継承
- Rosetta 経由だと screencapture の画面取得APIが失敗し、`stderr='could not create image from rect'` で rc=1 終了

**対策**:
1. `folder_launcher.py` の `_launch_one_keyboard` で `arch -arm64 python3 ...` を前置（commit `38d4cf2`）
2. `install_mac.sh` が生成する SokuLauncher.app 内の launcher スクリプトも `arch -arm64` に変更（commit `38d4cf2`）
3. 既存インストール済みの `~/Library/Application Support/SokuLauncher/SokuLauncher.app/Contents/MacOS/launcher` も同様に手動更新（このMacのみ、次Macでは install_mac.sh 再実行で反映）

**透明キーボード側の改善**（別リポジトリ: transparent-keyboard）:
- `take_screenshot()` を診断ログ付き・ファイル名にマイクロ秒・別スレッド実行に変更（commit `4d5c904`）
- 撮影成功時に自動でファイルパスをアクティブアプリ（ターミナル想定）へ `type_text` 経由でペースト（commit `18947c8`）
- 撮影中はキーボードウィンドウを orderOut → 完了後に orderFront（Rosetta切分中に入れた保険、残しておく。commit `95a3444`）
- subprocess は Popen + `start_new_session=True` で親から切り離し
- スクショ保存先: `/var/folders/.../T/claude_screenshots/` （macOSのユーザーtempdir）
- 診断ログ: 同フォルダ内 `_screenshot.log` に毎回 rc/saved/size/stderr 記録

### 別Macへの反映手順
1. GDrive で git pull（terminal_copy と 透明キーボード 両方）
2. `bash install_mac.sh` で launcher スクリプトの arch -arm64 化反映
3. **手動必須: Screen Recording 権限付与**
   - システム設定 → プライバシーとセキュリティ → 画面収録
   - `/Applications/Xcode.app/Contents/Developer/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app` を追加 → トグルON
4. launcher/キーボード全kill → SokuLauncher.app 再起動
5. デスクトップダブルクリックで新ターミナル起動 → PrScr で動作確認（毎回成功するはず）

## 前回の作業（セッション038）

### 1. iTerm2 導入完了
Terminal.app → iTerm2 移行でClaude Code履歴がマウスホイールで遡れるように

### 2. 透明キーボードのキー送信バグを根本修正
CGEventPost→osascript 切替。TCC キャッシュ問題の回避。

## Mac版の構成
- `folder_launcher.py` — メイン（NSApplication + iTerm2 + tmux連携 + **arch -arm64 でキーボード起動**）
- `hammerspoon_init.lua` — Hammerspoon設定
- `install_mac.sh` — **launcher テンプレに arch -arm64 を含む**
- `SokuLauncher.app/Contents/MacOS/launcher` — **arch -arm64 /usr/bin/python3 ... で folder_launcher.py を起動**

## 透明キーボードの構成（別リポジトリ transparent-keyboard）
- `mac/transparent_keyboard_mac.py` — メイン。テキスト送信は osascript 経由、スクショは診断ログ付き

## iTerm2 Profile設定（セットアップ後の手動作業）
- Terminal タブ: Save lines to scrollback in alternate screen mode ON
- General タブ: Title を Session Name、Applications in terminal may change the title OFF
- Text タブ: SF Mono Terminal Regular 12pt

## Windows版の構成
- `folder_launcher_win.pyw` / `即ランチャー.exe` / `一発更新_即ランチャー.bat` 構成は変更なし
