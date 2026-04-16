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

# --- Step 3: Hammerspoon設定をコピー ---
echo "[3/5] Hammerspoon設定をセットアップ..."
mkdir -p "$HOME/.hammerspoon"
cp "$SCRIPT_DIR/hammerspoon_init.lua" "$HS_CONFIG"
echo "OK"

# --- Step 4: Pythonスクリプトをローカルにコピー ---
echo "[4/5] スクリプトをローカルにコピー..."
pkill -f "folder_launcher.py" 2>/dev/null || true
sleep 0.5
mkdir -p "$LOCAL_DIR"
cp "$SCRIPT_DIR/folder_launcher.py" "$LOCAL_PY"

# 起動スクリプト作成（GDriveから最新版をコピーしてから起動）
cat > "$STARTER_SH" << ENDSCRIPT
#!/bin/bash
GDRIVE_PY="$SCRIPT_DIR/folder_launcher.py"
LOCAL_PY="$LOCAL_PY"

# Googleドライブ版が存在すれば最新版をコピー
if [ -f "\$GDRIVE_PY" ]; then
    cp "\$GDRIVE_PY" "\$LOCAL_PY" 2>/dev/null || true
fi
# Hammerspoon設定も最新版をコピー
if [ -f "$SCRIPT_DIR/hammerspoon_init.lua" ]; then
    cp "$SCRIPT_DIR/hammerspoon_init.lua" "$HS_CONFIG" 2>/dev/null || true
fi

nohup "$PYTHON" "\$LOCAL_PY" > /tmp/sokulauncher_stdout.log 2> /tmp/sokulauncher_stderr.log &
disown
osascript -e 'tell application "Terminal" to close front window' 2>/dev/null &
exit 0
ENDSCRIPT
chmod +x "$STARTER_SH"
echo "OK"

# --- Step 5: LaunchAgentで自動起動を登録 ---
echo "[5/5] LaunchAgentを登録..."

LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.nock.folder-launcher.plist"

# 既存のLaunchAgentをアンロード
launchctl bootout "gui/$(id -u)/com.nock.folder-launcher" 2>/dev/null || true

cat > "$LAUNCH_AGENT" << PLISTEOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.nock.folder-launcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>cp "$SCRIPT_DIR/folder_launcher.py" "$LOCAL_PY" 2>/dev/null; cp "$SCRIPT_DIR/hammerspoon_init.lua" "$HS_CONFIG" 2>/dev/null; exec "$PYTHON" "$LOCAL_PY"</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/sokulauncher_launchagent.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/sokulauncher_launchagent.log</string>
</dict>
</plist>
PLISTEOF

# 旧ログイン項目を削除（残骸クリーンアップ）
osascript -e "
tell application \"System Events\"
    try
        delete login item \"SokuLauncher\"
    end try
end tell
" 2>/dev/null || true

echo "OK"

# --- Hammerspoonをログイン項目に登録 ---
echo "Hammerspoonをログイン項目に登録..."
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
open -a Terminal "$STARTER_SH"

echo ""
echo "=== インストール完了 ==="
echo ""
echo "【重要】次の2つをシステム設定で許可してください："
echo "  システム設定 → プライバシーとセキュリティ → アクセシビリティ"
echo "  → Hammerspoon.app を追加してON"
echo "  → /Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework"
echo "    /Versions/3.9/Resources/Python.app を追加してON"
echo ""
echo "許可ダイアログが自動で出る場合はそのまま「許可」を押してください。"
echo ""
echo "設定後、デスクトップをダブルクリックしてメニューが出ればOKです。"
