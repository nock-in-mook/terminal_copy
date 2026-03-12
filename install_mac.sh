#!/bin/bash
# 即ランチャー Mac版インストールスクリプト
# - GDriveからスクリプトをローカルにコピー
# - Terminal.app経由で起動（GDriveアクセス権を継承）
# - ログイン項目に登録して自動起動
# 使い方: bash install_mac.sh

set -e

BUNDLE_ID="com.sokulauncher.agent"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$HOME/Library/Application Support/SokuLauncher"
LOCAL_PY="$LOCAL_DIR/folder_launcher.py"
STARTER_SH="$LOCAL_DIR/start.sh"
PLIST_PATH="$HOME/Library/LaunchAgents/${BUNDLE_ID}.plist"
PYTHON="/usr/bin/python3"

echo "=== 即ランチャー Mac版インストール ==="

# 既存のLaunchAgentを停止・削除
if launchctl list "$BUNDLE_ID" &>/dev/null; then
    echo "既存のLaunchAgentを停止..."
    launchctl bootout "gui/$(id -u)/$BUNDLE_ID" 2>/dev/null || true
    sleep 1
fi
rm -f "$PLIST_PATH"

# 既存プロセスを停止
pkill -f "folder_launcher.py" 2>/dev/null || true
sleep 0.5

# スクリプトをローカルにコピー
echo "スクリプトをローカルにコピー: $LOCAL_DIR"
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

# バックグラウンドで起動し、このターミナルウィンドウを閉じる
nohup "$PYTHON" "\$LOCAL_PY" > /tmp/sokulauncher_stdout.log 2> /tmp/sokulauncher_stderr.log &

# ターミナルウィンドウを閉じる
osascript -e 'tell application "Terminal" to close front window' 2>/dev/null || true
ENDSCRIPT
chmod +x "$STARTER_SH"

echo "起動スクリプト作成完了"

# ログイン項目に登録（osascript経由）
echo "ログイン項目に登録..."
osascript -e "
tell application \"System Events\"
    -- 既存の登録を削除
    try
        delete login item \"SokuLauncher\"
    end try
    -- Terminal.appでstart.shを実行するように登録
    make login item at end with properties {name:\"SokuLauncher\", path:\"$STARTER_SH\", hidden:true}
end tell
" 2>/dev/null || true

# 今すぐ起動（Terminal.app経由）
echo "即ランチャーを起動..."
open -a Terminal "$STARTER_SH"

echo ""
echo "=== インストール完了 ==="
echo "- ローカルコピー: $LOCAL_PY"
echo "- 起動スクリプト: $STARTER_SH"
echo "- 自動起動: ON（ログイン時にTerminal.app経由で起動）"
echo "- 自動更新: ON（起動時にGoogleドライブから最新版をコピー）"
echo "- ログ: /tmp/sokulauncher_stdout.log, /tmp/sokulauncher_stderr.log"
echo ""
echo "デスクトップをダブルクリックしてメニューが出ればOKです。"
