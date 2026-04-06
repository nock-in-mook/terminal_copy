# 即ランチャー（terminal_copy）開発メモ

## アーキテクチャ

**2段構成（macOS 26以降はNSEvent.addGlobalMonitorが動かないため）：**
- **Hammerspoon** → クリック検知（`~/.hammerspoon/init.lua`）
- **Python** → メニュー表示（`folder_launcher.py`）
- 通信方式: Hammerspoonが `/tmp/sokulauncher_trigger` にマウス座標を書く → Pythonが0.1秒ポーリングで読んでメニュー表示

## 新しいMacにセットアップするとき

```bash
bash install_mac.sh
```

これだけでOK（Homebrew必須）。実行後に以下の権限許可が必要：

**システム設定 → プライバシーとセキュリティ → アクセシビリティ**
- `Hammerspoon.app` → ON
- `/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework/Versions/3.9/Resources/Python.app` → ON

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
