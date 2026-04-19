#!/bin/bash
# 即ランチャー Mac版インストールスクリプト
# - Hammerspoon（クリック検知）+ Python（メニュー表示）の2段構成
# - GDriveからスクリプトをローカルにコピー
# - ログイン項目に登録して自動起動
# 使い方: bash install_mac.sh

BUNDLE_ID="com.sokulauncher.agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$HOME/Library/Application Support/SokuLauncher"
LOCAL_PY="$LOCAL_DIR/folder_launcher.py"
STARTER_SH="$LOCAL_DIR/start.sh"
HS_CONFIG="$HOME/.hammerspoon/init.lua"
PYTHON="/usr/bin/python3"

echo "=== 即ランチャー Mac版インストール ==="

# --- Step 1: pyobjc インストール ---
echo "[1/5] pyobjcを確認..."
"$PYTHON" -c "import objc" 2>/dev/null || {
    echo "pyobjcをインストール中..."
    "$PYTHON" -m pip install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz --quiet
}
echo "OK"

# --- Step 1.5: tmux インストール ---
echo "[1.5/5] tmuxを確認..."
if ! command -v tmux &>/dev/null; then
    echo "tmuxをインストール中..."
    if command -v brew &>/dev/null; then
        brew install tmux
    else
        echo "ERROR: Homebrewが見つかりません。https://brew.sh からインストールしてください"
        exit 1
    fi
fi
echo "OK"

# --- Step 2: Hammerspoon インストール ---
echo "[2/5] Hammerspoonを確認..."
if [ ! -d "/Applications/Hammerspoon.app" ]; then
    echo "Hammerspoonをインストール中..."
    if command -v brew &>/dev/null; then
        brew install --cask hammerspoon
    else
        echo "ERROR: Homebrewが見つかりません。https://brew.sh からインストールしてください"
        exit 1
    fi
fi
echo "OK"

# --- Step 2.5: iTerm2 インストール（Terminal.appではalt screenのscrollback保存ができないため） ---
echo "[2.5/5] iTerm2を確認..."
if [ ! -d "/Applications/iTerm.app" ]; then
    echo "iTerm2をインストール中..."
    if command -v brew &>/dev/null; then
        brew install --cask iterm2
    else
        echo "ERROR: Homebrewが見つかりません。https://brew.sh からインストールしてください"
        exit 1
    fi
fi
echo "OK"

# --- Step 2.6: SF Mono Terminal フォントを ~/Library/Fonts へコピー ---
# Terminal.app 同梱の SFMono-Terminal.ttf はプライベートフォントで、
# そのままだと iTerm2 の Font パネルに表示されない。ユーザーフォントとして登録する。
echo "[2.6/5] SF Mono Terminal フォントを確認..."
TERM_FONT_DIR="/System/Applications/Utilities/Terminal.app/Contents/Resources/Fonts"
USER_FONT_DIR="$HOME/Library/Fonts"
mkdir -p "$USER_FONT_DIR"
for f in SFMono-Terminal.ttf SFMonoItalic-Terminal.ttf; do
    if [ -f "$TERM_FONT_DIR/$f" ] && [ ! -f "$USER_FONT_DIR/$f" ]; then
        cp "$TERM_FONT_DIR/$f" "$USER_FONT_DIR/"
        echo "  コピー: $f"
    fi
done
echo "OK"

# --- Step 3: Hammerspoon設定をコピー ---
echo "[3/5] Hammerspoon設定をセットアップ..."
mkdir -p "$HOME/.hammerspoon"
cp "$SCRIPT_DIR/hammerspoon_init.lua" "$HS_CONFIG"
echo "OK"

# --- Step 4: Pythonスクリプトとランチャー.appをセットアップ ---
echo "[4/4] スクリプトとランチャーをセットアップ..."
pkill -f "folder_launcher.py" 2>/dev/null || true
sleep 0.5
mkdir -p "$LOCAL_DIR"
cp "$SCRIPT_DIR/folder_launcher.py" "$LOCAL_PY"

# SokuLauncher.app を作成（手動起動用の.appラッパー。
# 通常は Hammerspoon が launcher を spawn するので不要だが、
# Finder からダブルクリックで起動したい場合や、緊急手動起動用に残す）
APP_DIR="$LOCAL_DIR/SokuLauncher.app/Contents/MacOS"
mkdir -p "$APP_DIR"

cat > "$APP_DIR/../Info.plist" << 'INFOPLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.sokulauncher.agent</string>
    <key>CFBundleName</key>
    <string>SokuLauncher</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
INFOPLIST

cat > "$APP_DIR/launcher" << LAUNCHEREOF
#!/bin/bash
# GDriveから最新版をコピーしてからpython3を直接起動
GDRIVE_PY="$SCRIPT_DIR/folder_launcher.py"
GDRIVE_HS="$SCRIPT_DIR/hammerspoon_init.lua"
LOCAL_PY="$LOCAL_PY"
HS_CONFIG="$HS_CONFIG"

cp "\$GDRIVE_PY" "\$LOCAL_PY" 2>/dev/null
cp "\$GDRIVE_HS" "\$HS_CONFIG" 2>/dev/null

# Apple Silicon で Rosetta(x86_64) 継承を避ける。親がRosettaだと子のscreencapture -iが失敗する。
exec /usr/bin/arch -arm64 "$PYTHON" "\$LOCAL_PY" > /tmp/sokulauncher_stdout.log 2>/tmp/sokulauncher_stderr.log
LAUNCHEREOF
chmod +x "$APP_DIR/launcher"
echo "OK"

# --- ログイン項目: Hammerspoon のみ登録（launcher は Hammerspoon が spawn する） ---
# 旧仕組みの掃除: SokuLauncher.app のログイン項目登録と launchd plist を削除する
#   （open -a 経由の起動 / launchd 経由の再起動は、TCC chain が LaunchServices 由来に
#   なって screencapture -i が長時間後に失効する現象を引き起こすため）
osascript -e '
tell application "System Events"
    try
        delete login item "SokuLauncher"
    end try
end tell' 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.nock.folder-launcher" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.nock.folder-launcher.plist" 2>/dev/null || true
launchctl bootout "gui/$(id -u)/com.nock.sokulauncher.daily" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.nock.sokulauncher.daily.plist" 2>/dev/null || true

# Hammerspoon をログイン項目に登録（これ1本が launcher/透明キーボード/早朝再起動を管理）
osascript -e '
tell application "System Events"
    if not (exists login item "Hammerspoon") then
        make login item at end with properties {path:"/Applications/Hammerspoon.app", hidden:true}
    end if
end tell' 2>/dev/null || true
echo "OK (Hammerspoon が launcher を管理する方式)"

# --- 起動（Hammerspoon 起動時に launcher も自動 spawn される） ---
echo ""
echo "Hammerspoonを起動中（起動時に即ランチャーも自動で立ち上がります）..."
pkill -f "folder_launcher.py" 2>/dev/null || true
pkill -x Hammerspoon 2>/dev/null || true
sleep 0.5
open -a Hammerspoon

echo ""
echo "=== インストール完了 ==="
echo ""
echo "【重要1】アクセシビリティ許可："
echo "  システム設定 → プライバシーとセキュリティ → アクセシビリティ"
echo "  → Hammerspoon.app を追加してON"
echo "  → /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework"
echo "    /Versions/3.9/Resources/Python.app を追加してON"
echo ""
echo "【重要2】iTerm2のProfile設定（Claude Code会話履歴をマウスホイールで遡れるようにする）："
echo "  iTerm2 → Settings (Cmd+,) → Profiles → Default を選択"
echo "  - Terminal タブ:"
echo "      ☑ Save lines to scrollback in alternate screen mode （肝）"
echo "      ☑ Save lines to scrollback when an app status bar is present"
echo "      Scrollback Lines: Unlimited scrollback ON"
echo "  - General タブ → Title セクション:"
echo "      Title: Session Name を選択"
echo "      ☐ Applications in terminal may change the title （チェックを外す）"
echo "  - Text タブ: Change Font で好みのフォント（Menlo Regular 14pt 等）"
echo ""
echo "設定後、デスクトップをダブルクリックしてメニューが出ればOKです。"
