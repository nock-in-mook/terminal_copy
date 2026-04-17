# 即ランチャー（terminal_copy）開発メモ

## アーキテクチャ

**2段構成（macOS 26以降はNSEvent.addGlobalMonitorが動かないため）：**
- **Hammerspoon** → クリック検知（`~/.hammerspoon/init.lua`）
- **Python** → メニュー表示（`folder_launcher.py`）
- 通信方式: Hammerspoonが `/tmp/sokulauncher_trigger` にマウス座標を書く → Pythonが0.1秒ポーリングで読んでメニュー表示

## 新しいMacにセットアップするとき

ユーザーから「新しいMacにセットアップして」「別Macで使いたい」等と言われたら、以下を順に案内する。

### Step 1: 一発インストール
```bash
bash install_mac.sh
```
Homebrewが必須。スクリプトが tmux / Hammerspoon / **iTerm2** を自動インストールし、ログイン項目に登録する。

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
デスクトップをダブルクリック → メニュー表示 → フォルダ選択 → iTerm2 で新ウィンドウ起動。マウスホイールでClaude Code履歴が遡れればOK。

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

## ファイル構成

| ファイル | 説明 |
|---------|------|
| `folder_launcher.py` | Pythonメイン（NSMenu表示、ターミナル起動） |
| `hammerspoon_init.lua` | Hammerspoon設定（クリック検知） |
| `install_mac.sh` | Mac版一発インストール |
| `folder_launcher_win.pyw` | Windows版メイン |
| `一発更新_即ランチャー.bat` | Windows版一発セットアップ |

## ログ場所
- stdout: `/tmp/sokulauncher_stdout.log`
- stderr: `/tmp/sokulauncher_stderr.log`
- クリックテスト: `/tmp/sokulauncher_trigger`（Hammerspoonが書く、Pythonが読んで削除）
