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

# --- Step 3: Hammerspoon設定をコピー ---
echo "[3/5] Hammerspoon設定をセットアップ..."
mkdir -p "$HOME/.hammerspoon"
cp "$SCRIPT_DIR/hammerspoon_init.lua" "$HS_CONFIG"
echo "OK"

# --- Step 4: Pythonスクリプトとランチャー.appをセットアップ ---
echo "[4/5] スクリプトとランチャーをセットアップ..."
pkill -f "folder_launcher.py" 2>/dev/null || true
sleep 0.5
mkdir -p "$LOCAL_DIR"
cp "$SCRIPT_DIR/folder_launcher.py" "$LOCAL_PY"

# SokuLauncher.app を作成（ログイン項目用の.appラッパー）
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

exec "$PYTHON" "\$LOCAL_PY" > /tmp/sokulauncher_stdout.log 2>/tmp/sokulauncher_stderr.log
LAUNCHEREOF
chmod +x "$APP_DIR/launcher"
echo "OK"

# --- Step 5: ログイン項目に登録（LaunchAgentは使わない） ---
echo "[5/5] ログイン項目を登録..."

# 旧LaunchAgentがあれば削除
launchctl bootout "gui/$(id -u)/com.nock.folder-launcher" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.nock.folder-launcher.plist" 2>/dev/null || true

# SokuLauncherをログイン項目に登録
SOKU_APP="$LOCAL_DIR/SokuLauncher.app"
osascript -e "
tell application \"System Events\"
    try
        delete login item \"SokuLauncher\"
    end try
    make login item at end with properties {path:\"$SOKU_APP\", hidden:true}
end tell" 2>/dev/null || true

# Hammerspoonもログイン項目に登録
osascript -e '
tell application "System Events"
    if not (exists login item "Hammerspoon") then
        make login item at end with properties {path:"/Applications/Hammerspoon.app", hidden:true}
    end if
end tell' 2>/dev/null || true
echo "OK"

# --- 起動 ---
echo ""
echo "Hammerspoonを起動中..."
pkill -x Hammerspoon 2>/dev/null || true
sleep 0.5
open -a Hammerspoon

echo "即ランチャーを起動中..."
sleep 1
open "$SOKU_APP"

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
