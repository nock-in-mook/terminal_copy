#!/bin/bash
# 即ランチャー Mac版インストールスクリプト
# - スクリプトをローカルにコピー（Googleドライブ権限問題回避）
# - /Applications に .app バンドルを作成
# - LaunchAgent でログイン時自動起動 + 落ちたら自動復帰（KeepAlive）
# 使い方: bash install_mac.sh

set -e

APP_NAME="即ランチャー"
BUNDLE_ID="com.sokulauncher.agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$HOME/Library/Application Support/SokuLauncher"
LOCAL_PY="$LOCAL_DIR/folder_launcher.py"
APP_PATH="/Applications/${APP_NAME}.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${BUNDLE_ID}.plist"
PYTHON="/Applications/Xcode.app/Contents/Developer/usr/bin/python3"

echo "=== 即ランチャー Mac版インストール ==="

# 既存のLaunchAgentを停止
if launchctl list "$BUNDLE_ID" &>/dev/null; then
    echo "既存のLaunchAgentを停止..."
    launchctl bootout "gui/$(id -u)/$BUNDLE_ID" 2>/dev/null || true
    sleep 1
fi

# 既存プロセスを停止
pkill -f "folder_launcher.py" 2>/dev/null || true
sleep 0.5

# スクリプトをローカルにコピー（Googleドライブの権限問題を回避）
echo "スクリプトをローカルにコピー: $LOCAL_DIR"
mkdir -p "$LOCAL_DIR"
cp "$SCRIPT_DIR/folder_launcher.py" "$LOCAL_PY"

# .app バンドル作成
echo ".appバンドルを作成: $APP_PATH"
rm -rf "$APP_PATH"
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# 起動スクリプト（Googleドライブからスクリプトを更新してから起動）
cat > "$APP_PATH/Contents/MacOS/launcher" << 'ENDSCRIPT'
#!/bin/bash
GDRIVE_PY="GDRIVE_PY_PLACEHOLDER"
LOCAL_PY="LOCAL_PY_PLACEHOLDER"
PYTHON_BIN="PYTHON_PLACEHOLDER"

# Googleドライブ版が存在すれば最新版をコピー（アクセスできなければローカル版で起動）
if [ -f "$GDRIVE_PY" ]; then
    cp "$GDRIVE_PY" "$LOCAL_PY" 2>/dev/null || true
fi

exec "$PYTHON_BIN" "$LOCAL_PY"
ENDSCRIPT

# プレースホルダーを実際のパスに置換
sed -i '' "s|GDRIVE_PY_PLACEHOLDER|$SCRIPT_DIR/folder_launcher.py|" "$APP_PATH/Contents/MacOS/launcher"
sed -i '' "s|LOCAL_PY_PLACEHOLDER|$LOCAL_PY|" "$APP_PATH/Contents/MacOS/launcher"
sed -i '' "s|PYTHON_PLACEHOLDER|$PYTHON|" "$APP_PATH/Contents/MacOS/launcher"
chmod +x "$APP_PATH/Contents/MacOS/launcher"

# Info.plist（LSUIElement=true でDockに表示しない）
cat > "$APP_PATH/Contents/Info.plist" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>${BUNDLE_ID}</string>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>LSUIElement</key>
    <true/>
</dict>
</plist>
PLIST

echo ".app作成完了"

# LaunchAgent plist 作成（KeepAlive で落ちたら自動復帰）
echo "LaunchAgent作成: $PLIST_PATH"
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${BUNDLE_ID}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${APP_PATH}/Contents/MacOS/launcher</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/sokulauncher_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/sokulauncher_stderr.log</string>
    <key>ThrottleInterval</key>
    <integer>5</integer>
</dict>
</plist>
PLIST

# LaunchAgent を登録＆起動
echo "LaunchAgentを登録..."
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"

echo ""
echo "=== インストール完了 ==="
echo "- アプリ: $APP_PATH"
echo "- ローカルコピー: $LOCAL_PY"
echo "- 自動起動: ON（ログイン時に自動で起動します）"
echo "- 自動復帰: ON（落ちても5秒後に自動で再起動します）"
echo "- 自動更新: ON（起動時にGoogleドライブから最新版をコピー）"
echo "- ログ: /tmp/sokulauncher_stdout.log, /tmp/sokulauncher_stderr.log"
echo ""
echo "メニューバーに 📂 が表示されていればOKです。"
