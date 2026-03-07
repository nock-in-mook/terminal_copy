# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Windows版フォルダランチャー（folder_launcher_win.pyw）完成・動作確認済み
- Mac版フォルダランチャー（folder_launcher.py）は旧版のまま（cdコピーのみ）

## Windows版の機能（folder_launcher_win.pyw）
1. **右クリックメニュー → フォルダ一覧** → `cd "パス"` をクリップボードにコピー
2. **[1 single] 〜 [4 split]** → 選択UIが開く → フォルダを順番に選択 → Launch
   - 独立したWindows Terminalウィンドウを起動
   - 右端に寄せて隙間なく配置（MoveWindow API）
   - 固定幅（画面の23%）、上下10%マージン
   - タブタイトルにフォルダ名を表示（`wt --title`）
   - 既存WTウィンドウも含めて全体を再配置
3. **技術詳細**
   - pystray（トレイ）+ tkinter（選択UI）の組み合わせ
   - tkinterがメインスレッド、pystrayがサブスレッド（逆だとtkinterが2回目以降クラッシュする）
   - DPIスケーリング対応（SetProcessDPIAware）
   - split-pane方式は描画崩壊するため独立ウィンドウ方式を採用

## 次のアクション: Mac版の改良

### 目標
Windows版と同等の機能をMac版にも実装する

### 実装方針

#### 1. ターミナル起動（Terminal.appを使用）
```python
# Terminal.appで指定フォルダを開く + タブタイトル設定
import subprocess
script = f'''
tell application "Terminal"
    do script "cd \\"{full_path}\\" && echo -ne \\"\\\\033]0;{folder_name}\\\\007\\""
    activate
end tell
'''
subprocess.Popen(['osascript', '-e', script])
```

#### 2. ウィンドウ配置（AppleScriptでbounds設定）
```python
# ウィンドウの位置・サイズを設定
# boundsは {左, 上, 右, 下} の形式
script = f'''
tell application "Terminal"
    set bounds of window 1 to {{{x}, {y}, {x + w}, {y + h}}}
end tell
'''
subprocess.Popen(['osascript', '-e', script])
```

#### 3. 画面サイズ取得
```python
# screenサイズの取得
script = '''
tell application "Finder"
    get bounds of window of desktop
end tell
'''
# → "0, 0, 1920, 1080" のような文字列が返る
result = subprocess.check_output(['osascript', '-e', script]).decode().strip()
```

#### 4. 既存ウィンドウの検出と再配置
```python
# Terminal.appのウィンドウ数を取得
script = '''
tell application "Terminal"
    count of windows
end tell
'''
# 各ウィンドウのboundsを取得してソート → 右寄せで再配置
```

### 変更対象ファイル
- `folder_launcher.py` を改修

### 変更内容（rumpsメニューの構成）
現在:
```
フォルダ名クリック → cdコピー
更新
終了
```

改良後:
```
フォルダ名クリック → cdコピー（変更なし）
---
[1 single] → tkinter選択UIを表示
[2 split]
[3 split]
[4 split]
---
更新
終了
```

### Mac固有の注意点
- **rumps + tkinterの共存**: rumpsがメインスレッドを占有するので、tkinterはサブスレッドで動かす必要がある。ただしmacOSのtkinterはサブスレッドで不安定な場合がある。代替案として `rumps.Window` のアラート機能を使うか、`subprocess` でtkinterを別プロセスとして起動する方法がある
- **pbcopy**: クリップボードコピーは `pbcopy` を使用（Windows版の `clip.exe` に相当）
- **Dropboxパス**: `~/Library/CloudStorage/Dropbox/_Apps2026`（Windows版の `D:\Dropbox\_Apps2026` に相当）
- **固定幅**: Windows版と同じく画面の23%、上下10%マージン
- **最大4つまで**

### 代替アプローチ（rumps + tkinter が不安定な場合）
選択UIをtkinterではなく、rumps のメニュー内サブメニューで実装する:
```
[3 split] → サブメニュー展開 → 1つ目を選択
  → 再度メニュー → 2つ目を選択
  → 再度メニュー → 3つ目を選択
  → 自動でターミナル起動
```
これなら外部UIライブラリ不要。ただし右クリック3回必要になる。

### テスト手順
1. `git pull` でWindows側の変更を取得
2. `folder_launcher.py` を改修
3. 単体テスト: `python3 folder_launcher.py` で起動
4. [1 single] でターミナルが右端に1つ起動するか確認
5. [3 split] で3つ右寄せ配置されるか確認
6. 既存ターミナルがある状態で追加起動 → 再配置されるか確認

## グローバル設定の変更（今セッションで実施済み）
- CLAUDE.md: remote_bat関連の自動作成ルールを削除
- CLAUDE.md: 透明キーボード確認ステップを削除
- CLAUDE.md: セッション開始処理を簡略化（Read 2回で完了）
- CLAUDE.md: セッション終了処理を最適化（リネーム提案を先に、並列実行）
- 全プロジェクトのremote_bat*/remote_start*ファイルを削除済み
