# 引き継ぎメモ

## 現在の状況
- GitHubリポジトリ: https://github.com/nock-in-mook/terminal_copy
- Windows版フォルダランチャー（folder_launcher_win.pyw）完成・動作確認済み
- Mac版フォルダランチャー（folder_launcher.py）は旧版のまま（cdコピーのみ）

## Windows版の機能（folder_launcher_win.pyw）

### メニュー構成
```
[Show All]        ← 全WTウィンドウを最前面に
───────────
[1 single] →     ← サブメニューにフォルダ一覧（選ぶと即1つ起動）
[2 split]         ← tkinter選択UIで2つ選んでLaunch
[3 split]         ← tkinter選択UIで3つ選んでLaunch
───────────
Refresh           ← フォルダ一覧再読込
[Close All]       ← 確認2回で全WT閉じる
Quit
```

### 配置ロジック
- 最大3ウィンドウ制限（WT最小幅の制約）
- 幅は常に MAX_TERMINALS(3) 分割の固定幅（1つでも2つでも同じ幅）
- 画面幅の95%を使用、右寄せ配置
- 上下10%マージン
- 影の重なり補正 SHADOW_OVERLAP=14px（論理ピクセル）
- 追加起動時は全WTを自動で再配置

### 技術詳細
- pystray（トレイ）+ tkinter（選択UI）の組み合わせ
- **tkinterがメインスレッド、pystrayがサブスレッド**（逆だとtkinterが2回目以降クラッシュする）
- **DPI Awareは呼ばない**（論理座標でMoveWindowするとWTが指定幅を守る。物理座標だとWT最小幅制約で重なる）
- DPIスケール125%環境: 論理1536×864、物理1920×1080
- WT最小幅: 論理478px（物理598px）
- split-pane方式は描画崩壊するため独立ウィンドウ方式を採用
- CLAUDECODE環境変数をクリアしてclaude起動（ネスト防止）
- suppressApplicationTitle=true でタブタイトルにフォルダ名を維持
- スタートアップ + スタートメニューにショートカット登録済み

### 一発セットアップ（別のWindows PCで）
`launcher.bat` を実行するだけ:
1. Python自動検出（C:\Python314 → py コマンド）
2. pystray/pillow インストール
3. Windows Terminal インストール（未インストールなら）
4. WTにライトテーマ + suppressApplicationTitle 設定
5. スタートアップ/スタートメニューにショートカット作成
6. ランチャー起動

## 次のアクション: Mac版の改良

### 目標
Windows版と同等の機能をMac版にも実装する

### Windows版との対応表
| 機能 | Windows | Mac |
|------|---------|-----|
| トレイ/メニューバー | pystray | rumps |
| ターミナル | Windows Terminal (wt) | Terminal.app (AppleScript) |
| ウィンドウ操作 | MoveWindow API | AppleScript bounds |
| クリップボード | clip.exe | pbcopy |
| Dropboxパス | D:\Dropbox\_Apps2026 | ~/Library/CloudStorage/Dropbox/_Apps2026 |
| 選択UI | tkinter (メインスレッド) | 要検討（rumpsサブメニュー or 別プロセスtkinter） |

### 実装方針

#### 1. ターミナル起動（Terminal.appを使用）
```python
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
script = '''
tell application "Finder"
    get bounds of window of desktop
end tell
'''
result = subprocess.check_output(['osascript', '-e', script]).decode().strip()
# → "0, 0, 1920, 1080"
```

#### 4. 既存ウィンドウの検出と再配置
```python
script = '''
tell application "Terminal"
    count of windows
end tell
'''
# 各ウィンドウのboundsを取得してソート → 右寄せで再配置
```

### メニュー構成（Mac版）
```
[Show All]        ← 全Terminal.appウィンドウを最前面に
───────────
[1 single] →     ← サブメニューにフォルダ一覧
[2 split]         ← 選択UI（rumpsサブメニュー方式推奨）
[3 split]
───────────
Refresh
[Close All]
Quit
```

### Mac固有の注意点
- **rumps + tkinterの共存問題**: rumpsがメインスレッドを占有。tkinterをサブスレッドで動かすとmacOSで不安定。推奨: rumpsのサブメニューで選択UIを代替するか、別プロセスでtkinterを起動
- **最大3ウィンドウ**: Windows版と統一
- **固定幅**: 画面幅の95%÷3で固定、右寄せ
- **影の補正**: macOSでは不要かもしれない（要テスト）

### 代替アプローチ（rumps + tkinter が不安定な場合）
選択UIをrumpsのサブメニューで実装:
```
[3 split] → サブメニュー展開 → 1つ目を選択
  → 再度メニュー → 2つ目を選択
  → 再度メニュー → 3つ目を選択
  → 自動でターミナル起動
```

### テスト手順
1. `git pull` でWindows側の変更を取得
2. `folder_launcher.py` を改修
3. `python3 folder_launcher.py` で起動
4. [1 single] でターミナルが右端に1つ起動するか確認
5. [3 split] で3つ右寄せ配置されるか確認
6. 既存ターミナルがある状態で追加起動 → 再配置されるか確認

## 今セッションでの変更まとめ
- get_folders()にimages・textフォルダの除外フィルタを追加
- WTフォントをUDEV Gothicに変更（日本語の文字間スキマ解消）
- /end スキルとCLAUDE.mdのセッション名リネームを確認不要・全自動に変更
- 次: Mac版フォルダランチャーの改良（上記参照）
- 次: launcher.batにUDEV Gothicフォント自動インストール処理を追加するとベター
