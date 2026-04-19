# 即ランチャー（terminal_copy）開発メモ

## アーキテクチャ

**2段構成（macOS 26以降はNSEvent.addGlobalMonitorが動かないため）：**
- **Hammerspoon** →
  - デスクトップダブルクリック検知（`~/.hammerspoon/init.lua`）
  - **launcher プロセスの起動・監視・再起動** （#15 の TCC陳腐化対策として）
  - 毎日 04:00 の予防的再起動タイマー
  - `/tmp/sokulauncher_restart_requested` のポーリング監視（透明キーボードが PrScr 失敗時に touch する）
- **Python** → メニュー表示（`folder_launcher.py`）、透明キーボード（`transparent_keyboard_mac.py`）
- 通信方式:
  - クリック検知: Hammerspoonが `/tmp/sokulauncher_trigger` にマウス座標を書く → Pythonが0.1秒ポーリングで読んでメニュー表示
  - 自動復旧: 透明キーボードが `/tmp/sokulauncher_restart_requested` を touch → Hammerspoonが検知して launcher+透明キーボードを再spawn

**launcher 起動経路（超重要）:**
launcher は **Hammerspoon が hs.execute で直接 spawn** する。`open -a SokuLauncher.app` や launchd agent 経由で起動すると、LaunchServices 由来の TCC chain になって **長時間後に screencapture -i が無言失敗する**（#15）。SokuLauncher.app のログイン項目登録は 2026-04-19 に廃止済み。

## 新しいMacにセットアップするとき

ユーザーから「新しいMacにセットアップして」「別Macで使いたい」等と言われたら、以下を順に案内する。

### Step 1: 一発インストール
```bash
bash install_mac.sh
```
Homebrewが必須。スクリプトが tmux / Hammerspoon / **iTerm2** を自動インストールし、**Hammerspoon をログイン項目に登録**する（launcher の起動・管理は Hammerspoon が担う）。

### Step 2: アクセシビリティ許可
**システム設定 → プライバシーとセキュリティ → アクセシビリティ**
- `Hammerspoon.app` → ON
- `/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app` → ON

### Step 3: iTerm2のProfile設定（手動・マウス操作）
**これをやらないとClaude Codeの会話履歴がマウスホイールで遡れない。**

iTerm2 → `Settings` (Cmd+,) → `Profiles` タブ → 左で `Default` を選択:

- **`Terminal` タブ**:
  - ☑ **Save lines to scrollback in alternate screen mode** ← **肝**（これがないとalt screenの内容が保存されない）
  - ☑ Save lines to scrollback when an app status bar is present
  - Scrollback Lines: `Unlimited scrollback` ON（または 100000 以上）

- **`General` タブ → Title セクション**:
  - `Title:` ドロップダウンで **`Session Name`** を選択
  - ☐ **Applications in terminal may change the title**（**チェックを外す**）

- **`Text` タブ → Font**:
  - `Change Font` → **SF Mono Terminal Regular 12pt**（Terminal.appと同じ見た目）、または Menlo Regular 14pt 等
  - ※ SF Mono Terminal は install_mac.sh が `~/Library/Fonts/` へコピー済み。Font パネルを開き直すと出現する

### Step 4: 動作確認
Hammerspoon を起動（install_mac.sh 最後で自動起動する）すると、直後に launcher も自動 spawn される。デスクトップをダブルクリック → メニュー表示 → フォルダ選択 → iTerm2 で新ウィンドウ起動。マウスホイールでClaude Code履歴が遡れればOK。

## ハマりポイント（実体験）

### 1. install_mac.shがCRLF改行で動かない
- **原因**: Windows側で編集するとCRLFになる
- **症状**: `set: -: invalid option` エラー
- **対処**: `tr -d '\r' < install_mac.sh | bash` で実行、またはファイルのCRLFをLFに修正

### 2. NSEvent.addGlobalMonitorForEventsMatchingMask_handler_ がmacOS 26で動かない
- **原因**: macOS 26（Tahoe）でグローバルマウスイベント監視の仕様が変更された
- **症状**: モニターは作成される（オブジェクトが返る）が、クリックしても何も来ない
- **対処**: Hammerspoonの `hs.eventtap` を使ってクリック検知する

### 3. アクセシビリティ許可が効かない
- **原因**: `tccutil reset` でキャッシュが残っていた / 再起動前に設定した
- **症状**: `AXIsProcessTrusted()` がFalseを返す、またはTrueでもイベントが来ない
- **対処**: `tccutil reset Accessibility org.hammerspoon.Hammerspoon` → Hammerspoon再起動 → ダイアログで「許可」

### 4. Hammerspoonで「Is Accessibility enabled?」エラー
- **原因**: アクセシビリティ設定にHammerspoonを追加しても再起動されていない
- **対処**: Hammerspoon ConsoleからReload、またはTCCリセット後に再起動

### 5. メニューが上下反転した位置に出る
- **原因**: HammerspoonのY座標は左上原点（下方向が正）、AppKitのNSMakePointはY左下原点（上方向が正）
- **対処**: `y = screen_height - hs_y` で変換（Python側で実装済み）

### 6. isDesktopClick()がTerminal起動後に常にFalseを返す
- **原因**: 「最前面アプリがTerminalなら除外」という判定をすると、ターミナルを開いた後はデスクトップクリックが全部弾かれる
- **対処**: アプリ名ではなく**クリック座標にウィンドウが存在するか**で判定する（`hs.window.orderedWindows()`でループ）

### 7. start.shがGDriveから上書きコピーするので、ローカル修正が消える
- **原因**: 自動更新の仕組み上、起動時にGDriveから最新版をコピーする
- **対処**: GDriveのファイルを直接修正すること

### 8. Windows: 複数PCで共有するとビルド成果物が壊れる + 毎回SmartScreen警告
- **原因**: `即ランチャー.exe` / `python3xx.dll` / `_pth` をGドライブに置くと、別PCでビルドされた `_pth`（例: `C:\Python314\Lib`）が同期されて、このPCにその場所が無ければpythonw.exeが無言で落ちる。Gドライブ上の未署名EXEはSmartScreenが毎回警告も出す
- **対処**: ビルド成果物の出力先を `%LOCALAPPDATA%\即ランチャー\` に変更済み（`_build_exe.py` / `_setup_shortcuts.py`）。ソースの `.pyw` はGドライブのまま → コード編集は即反映。Python 3.14が無ければ `一発更新_即ランチャー.bat` がwingetで自動インストールする

### 9. Terminal.appではClaude Codeの会話履歴がマウスホイールで遡れない
- **原因**: Terminal.app はalt screen（Claude CodeのTUI）の内容を scrollback に保存しない仕様。設定で変更不可
- **症状**: 1画面分スクロールするとシェル起動時のログ（`Last login`, `tmux has-session`）に着地して、Claude Code の会話が一切見えない
- **対処**: iTerm2 に移行（`Save lines to scrollback in alternate screen mode` 設定あり）。folder_launcher.py を iTerm2 対応に書き換え済み（`tell application "iTerm"`, `current session of window`, `pgrep -x iTerm2` 等）

### 10. iTerm2でsessionのnameが"tmux"や"zsh"に勝手に書き換わる
- **原因**: Profile の `Title` 設定が `Job` になってると実行中プロセス名で自動更新される
- **対処**: Profile → General → `Title` を **`Session Name`** に、**`Applications in terminal may change the title`** を OFF。これで `set name of s to ...` で指定した値が固定される

### 11. launcher が start.sh 経由だと現在のターミナル（Claude Code）を閉じる危険
- **原因**: 旧 launcher は `open -a Terminal start.sh` で Terminal.app 経由で起動し、start.sh の最後が `tell application "Terminal" to close front window` で、今作業中のウィンドウを閉じてしまう
- **対処**: `SokuLauncher.app/Contents/MacOS/launcher` を install_mac.sh 正規版（python3 直接起動方式）に戻す。`bash install_mac.sh` 再実行で自動復旧する

### 12. SF Mono Terminal フォントが iTerm2 の Font パネルに出てこない
- **原因**: Terminal.app 同梱の `SFMono-Terminal.ttf` はプライベートフォント扱いで、他アプリからは選択不可
- **症状**: iTerm2 → Change Font で "SF" で検索しても候補に出ない
- **対処**: `/System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts/SFMono-Terminal.ttf` を `~/Library/Fonts/` にコピー → Font パネル開き直すと **SF Mono Terminal** として表示される。install_mac.sh の Step 2.6 で自動化済み
- **備考**: Regular ウェイトのみ。他ウェイト（Light/Medium/Bold）が欲しい場合は Xcode を入れる or Apple Developer サイトから SF Mono Family をダウンロード

### 13. Apple Silicon で透明キーボードのPrScr（screencapture -i）が "could not create image from rect" で失敗する
- **症状**: 透明キーボードのPrScrで範囲選択してもファイルが保存されない。`_screenshot.log` に `rc=1 stderr='could not create image from rect'` と記録される。`screencapture -x`（非対話）は成功するが `-i`（対話）だけ失敗。画面収録権限を与えても直らない
- **原因**: 即ランチャー（親）が Hammerspoon/launchd チェーンで **x86_64 Rosetta** として起動されてて、子の透明キーボード→孫の screencapture までアーキテクチャ継承される。Rosetta 経由の Python から CoreGraphics の rect capture を呼ぶと内部で失敗する（Python は Universal Binary なので arch 指定しないと親の arch を継承）
- **対処**: 
  - 子プロセス起動に `['arch', '-arm64', 'python3', KB_SCRIPT]` を明示（`folder_launcher.py` の `_launch_one_keyboard` で対応済み）
  - `SokuLauncher.app/Contents/MacOS/launcher` の exec 行も `exec /usr/bin/arch -arm64 "/usr/bin/python3" ...` に変更（install_mac.sh のテンプレでも対応済み）
- **診断コマンド**: `lsof -p <PID> 2>/dev/null | grep -iE 'rosetta|oah'` で Rosetta 判定（`/private/var/db/oah/...` や `/usr/libexec/rosetta/runtime` が出たら Rosetta）
- **予防**: Apple Silicon 向けに新しい login item / ランチャーを作るときは最初から `arch -arm64` を明示するのが安全。Python が Universal でも、親が x86_64 なら継承される
- **類似症状の別パターン（TCCキャッシュ陳腐化）**: Rosetta じゃないのに同じ `could not create image from rect` エラーが出る場合がある（前回成功から数時間〜翌日経って突然失敗、みたいに）。特徴: `screencapture -x`（非対話）を**シェルから直接**実行しても `could not create image from display` で失敗する。これは TCC の権限キャッシュが陳腐化してる症状。対処: iTerm や Python.app の画面収録トグル状態を確認（抜けてたら追加）→ 透明キーボードと launcher を kill して再起動するだけで直る（起動時に TCC を再読込するため）
  ```
  pkill -f transparent_keyboard_mac.py
  arch -arm64 /usr/bin/python3 "/Users/nock_re/Library/Application Support/SokuLauncher/folder_launcher.py" --show-all
  ```

### 14. 即ランチャーのフォルダ選択で iTerm2 が「50%くらいの確率で」開かない
- **症状**: 即ランチャーのメニューからフォルダを選んでも、無反応。ウィンドウが開かない。再現率は五分五分、条件不明
- **原因**: `_cleanup_zombie_tmux_sessions()` 内で `NSLog(...)` を呼んでいるが **`NSLog` が import されていない**。デタッチ済み tmux セッションがあるときだけ kill 通知で `NSLog` が走り、`NameError: name 'NSLog' is not defined` で例外。`except` 内でも再度 `NSLog` を呼んでいるため二重例外になり、`open_terminal` 全体が吹き飛んで iTerm2 ウィンドウが開かない
- **条件分岐の正体**: iTerm2 を ×で閉じた直後（＝デタッチ tmux セッション残存）だけ失敗。フレッシュな状態や、tmux 掃除対象がない場合は `NSLog` 呼び出しが走らないので成功する
- **対処**: `NSLog` を `_log()`（プロジェクト内の `/tmp/sokulauncher_launch.log` 書き込みヘルパー）に置換。`from Foundation import NSLog` で import し忘れてたら普通の `print` や `_log` で代用する
- **診断用**: `/tmp/sokulauncher_launch.log` に `openFolder_ clicked` → `open_terminal START` → `zombie cleanup dur=...` → `create_window dur=... tty='...'` → `open_terminal END` の流れが記録される。途中で途切れてたら、そこが犯行現場
- **予防**: `_run_applescript` には必ず **タイムアウト付き**（`timeout=10` 等）で呼ぶ。さもないと iTerm2 が無反応になった時に無限待ちでランチャー全体が固まる

### 15. 透明キーボードの PrScr が1日くらいで必ず無言失敗するようになる（LaunchServices経由起動の TCC chain 陳腐化）
- **症状**: 透明キーボードの PrScr ボタン → 範囲選択カーソル出ない／ダイアログも出ない／即 `could not create image from rect` でログに記録される。**シェルから直接 `screencapture -x` `screencapture -R` `screencapture -i` は全部成功**する（iTerm 経由なので）。透明キーボードプロセスから呼ぶ時だけ失敗。前日まで普通に使えてたのに、翌日起動中のまま突然失敗に変わる
- **真犯人**: ログイン項目 `SokuLauncher.app` からの起動は `open -a` 相当で走るため、**responsible process が LaunchServices 系**になる。長時間経過や macOS の TCC デーモンの何らかのタイミングで、この LaunchServices 由来 chain の画面収録権限が失効する。**target バイナリ（Python.app）の TCC は生きてるのに、responsible 側の判定で蹴られる**ので、ダイアログも出ずに即 `rc=1` で無言失敗
- **切り分け**（同じ症状に遭遇したら）:
  1. `screencapture -x /tmp/test.png` をシェルから実行 → 通るなら TCC 全面陳腐化ではない
  2. `screencapture -R0,0,300,300 /tmp/rect.png` → 通るなら rect capture 自体は可能
  3. iTerm から `arch -arm64 /usr/bin/python3 -c "import subprocess; subprocess.run(['screencapture','-i','/tmp/x.png'])"` → 通るなら Python.app の TCC も OK
  4. 透明キーボードからの `-i` だけ失敗 → responsible chain 陳腐化が確定
- **対処（2026-04-19 に根本解決）**:
  - **SokuLauncher.app のログイン項目登録を廃止**。代わりに **Hammerspoon が launcher を `hs.execute` で spawn** する方式に変更
  - Hammerspoon は普通のユーザー GUI アプリなので、そこから spawn した launcher は健全な TCC chain を持つ
  - 自動復旧: 透明キーボード側で `could not create image from rect` を検知したら `/tmp/sokulauncher_restart_requested` を touch（`_trigger_recovery()` in `transparent_keyboard_mac.py`）。Hammerspoon が 3 秒ポーリングで検知して launcher+透明キーボードを `pkill -9` → 再 spawn
  - 予防: Hammerspoon の `hs.timer.doAt("04:00", "1d", ...)` で毎日4時に予防的再起動
- **手動 fallback**: `bash restart_launcher.sh`（中身は `touch /tmp/sokulauncher_restart_requested` だけ。Hammerspoon が拾う）
- **診断用ログ**: `/tmp/sokulauncher_launch.log` に `hammerspoon: restart_launcher_and_keyboards` の記録が入る
- **してはいけない対処**: launchd agent から restart_launcher.sh を呼ぶ、`open -a SokuLauncher.app` で launcher を起こし直す。どちらも LaunchServices 由来 chain を再生産して同じ問題が再発する

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `folder_launcher.py` | Pythonメイン（NSMenu表示、ターミナル起動） |
| `hammerspoon_init.lua` | Hammerspoon設定（クリック検知 + launcher 管理 + 自動復旧 + 早朝再起動） |
| `install_mac.sh` | Mac版一発インストール |
| `restart_launcher.sh` | 手動復旧用シェルショートカット（`touch /tmp/sokulauncher_restart_requested` するだけ） |
| `folder_launcher_win.pyw` | Windows版メイン |
| `一発更新_即ランチャー.bat` | Windows版一発セットアップ |

## ログ場所
- stdout: `/tmp/sokulauncher_stdout.log`
- stderr: `/tmp/sokulauncher_stderr.log`
- launcher 動作ログ: `/tmp/sokulauncher_launch.log`（`openFolder_ clicked` などの詳細。Hammerspoon 復旧発火も記録）
- クリックテスト: `/tmp/sokulauncher_trigger`（Hammerspoonが書く、Pythonが読んで削除）
- 復旧依頼: `/tmp/sokulauncher_restart_requested`（透明キーボードが touch、Hammerspoon が拾う）
