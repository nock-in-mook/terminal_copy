-- 即ランチャー: デスクトップダブルクリック検知
-- Hammerspoonがクリックを検知 → /tmp/sokulauncher_trigger に座標を書く
-- Python側がそれを読んでメニューを表示する

local TRIGGER_FILE = "/tmp/sokulauncher_trigger"
local lastClickTime = 0
local lastClickX = 0
local lastClickY = 0
local DOUBLE_CLICK_THRESHOLD = 0.4  -- 秒
local MOVE_THRESHOLD = 5            -- ピクセル

-- 透明キーボードの位置ファイル（NSPanelはhs.windowで見えないため別途チェック）
local KB_BOUNDS_FILE = "/tmp/transparent_keyboard_bounds.json"

-- デスクトップクリックかどうか判定（クリック座標にウィンドウがなければデスクトップ）
local function isDesktopClick(x, y)
    -- 通常ウィンドウのチェック
    for _, win in ipairs(hs.window.orderedWindows()) do
        local f = win:frame()
        if x >= f.x and x <= f.x + f.w and y >= f.y and y <= f.y + f.h then
            return false  -- ウィンドウの上をクリックしている
        end
    end
    -- 透明キーボード（NSPanel）のチェック
    local f = io.open(KB_BOUNDS_FILE, "r")
    if f then
        local content = f:read("*a")
        f:close()
        local ok, data = pcall(hs.json.decode, content)
        if ok and data then
            for _, bounds in pairs(data) do
                if x >= bounds.x and x <= bounds.x + bounds.w
                   and y >= bounds.y and y <= bounds.y + bounds.h then
                    return false  -- 透明キーボードの上をクリックしている
                end
            end
        end
    end
    return true  -- どのウィンドウにも当たらない = デスクトップ
end

-- マウスイベント監視（グローバル変数でGC回収を防ぐ）
SokuClickWatcher = hs.eventtap.new({hs.eventtap.event.types.leftMouseDown}, function(event)
    local now = hs.timer.secondsSinceEpoch()
    local pos = hs.mouse.absolutePosition()
    local timeDiff = now - lastClickTime
    local dx = math.abs(pos.x - lastClickX)
    local dy = math.abs(pos.y - lastClickY)

    if timeDiff < DOUBLE_CLICK_THRESHOLD and dx < MOVE_THRESHOLD and dy < MOVE_THRESHOLD then
        -- ダブルクリック判定
        if isDesktopClick(pos.x, pos.y) then
            local f = io.open(TRIGGER_FILE, "w")
            if f then
                f:write(pos.x .. "," .. pos.y)
                f:close()
            end
            lastClickTime = 0
            return false
        end
    end

    lastClickTime = now
    lastClickX = pos.x
    lastClickY = pos.y
    return false
end)

SokuClickWatcher:start()
hs.alert.show("即ランチャー: 待機中")

-- watchdog: 5秒ごとにeventtapが動いているか確認して止まってたら再起動（タイマーもグローバルで保持）
SokuWatchdogTimer = hs.timer.doEvery(5, function()
    if SokuClickWatcher and not SokuClickWatcher:isEnabled() then
        hs.alert.show("即ランチャー: 再起動")
        SokuClickWatcher:start()
    end
end)

-- GDrive上のinit.luaが変わったら自動コピー＆リロード
local GDRIVE_LUA = os.getenv("HOME") .. "/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026/terminal_copy/hammerspoon_init.lua"
local LOCAL_LUA = os.getenv("HOME") .. "/.hammerspoon/init.lua"

SokuConfigWatcher = hs.pathwatcher.new(GDRIVE_LUA, function(paths, flagTables)
    -- GDriveからローカルにコピーしてリロード
    hs.execute("cp '" .. GDRIVE_LUA .. "' '" .. LOCAL_LUA .. "'")
    hs.alert.show("即ランチャー: 設定更新 → リロード")
    hs.timer.doAfter(0.5, function() hs.reload() end)
end):start()

-- ===================================================================
-- launcher / 透明キーボードの起動・自動復旧管理
-- Hammerspoon の子プロセスとして起動することで、TCC chain を安定化する。
-- （open -a SokuLauncher.app 経由 = LaunchServices 由来の起動だと、
--   長時間経過後に screencapture -i の TCC 判定が失効する現象があるため）
-- ===================================================================
local LAUNCHER_PY_LOCAL = os.getenv("HOME") .. "/Library/Application Support/SokuLauncher/folder_launcher.py"
local LAUNCHER_PY_GDRIVE = os.getenv("HOME") .. "/Library/CloudStorage/GoogleDrive-yagukyou@gmail.com/マイドライブ/_Apps2026/terminal_copy/folder_launcher.py"
local RESTART_TRIGGER = "/tmp/sokulauncher_restart_requested"

local function _spawn_log(msg)
    local f = io.open("/tmp/hs_spawn.log", "a")
    if f then f:write(string.format("[%s] %s\n", os.date("%Y-%m-%d %H:%M:%S"), msg)); f:close() end
end

function spawn_launcher()
    _spawn_log("spawn_launcher: start")
    os.execute("mkdir -p '" .. os.getenv("HOME") .. "/Library/Application Support/SokuLauncher'")
    os.execute("cp '" .. LAUNCHER_PY_GDRIVE .. "' '" .. LAUNCHER_PY_LOCAL .. "' 2>/dev/null")
    -- AppleScript 経由で iTerm 配下の shell から launcher を起動する。
    -- Hammerspoon（LSUIElement）由来の spawn だと screencapture -i の TCC が通らない
    -- 問題を回避するため、前景アプリ iTerm の responsible chain を使う。
    -- iTerm session 内で nohup & disown し、直後に exit で session を畳む。
    -- launcher 側は _SOKU_DAEMONIZED フラグで subprocess.Popen 自己再起動して独立する。
    -- 1行で launcher + 1秒後 --show-all + exit をまとめて shell に投入。
    -- delay を AppleScript に持たせず一瞬で AppleScript を完了させる（Hammerspoon を blockしない）。
    local cmd = string.format(
        "(nohup /usr/bin/arch -arm64 /usr/bin/python3 '%s' " ..
        ">/tmp/sokulauncher_stdout.log 2>/tmp/sokulauncher_stderr.log </dev/null & " ..
        "sleep 2; nohup /usr/bin/arch -arm64 /usr/bin/python3 '%s' --show-all " ..
        ">/dev/null 2>&1 </dev/null &); exit",
        LAUNCHER_PY_LOCAL, LAUNCHER_PY_LOCAL)
    local applescript = string.format([[
tell application "iTerm"
    set newWindow to (create window with default profile)
    tell current session of newWindow to write text "%s"
end tell
]], cmd:gsub('"', '\\"'))
    local ok, err = hs.osascript.applescript(applescript)
    _spawn_log(string.format("applescript ok=%s err=%s", tostring(ok), tostring(err)))
end

local function restart_launcher_and_keyboards()
    -- pkill -f は hs.execute 由来の bash プロセス自身も巻き込んでしまうため、
    -- ps→awk でPIDを抽出してから kill する。
    hs.execute("ps auxww | awk '/[P]ython .*folder_launcher.py/ {print $2}' | xargs -r kill -9 2>/dev/null")
    hs.execute("ps auxww | awk '/[P]ython .*transparent_keyboard_mac.py/ {print $2}' | xargs -r kill -9 2>/dev/null")
    os.remove(RESTART_TRIGGER)
    hs.timer.doAfter(1.0, function()
        spawn_launcher()
        -- --show-all で透明キーボードも同時に復元（常駐運用の場合）
        hs.timer.doAfter(2.0, function()
            hs.execute("( /usr/bin/arch -arm64 /usr/bin/python3 '" .. LAUNCHER_PY_LOCAL .. "' --show-all >/dev/null 2>&1 < /dev/null & )")
        end)
    end)
    hs.alert.show("即ランチャー: 再起動")
    local f = io.open("/tmp/sokulauncher_launch.log", "a")
    if f then
        f:write(string.format("[%s] hammerspoon: restart_launcher_and_keyboards\n", os.date("%Y-%m-%d %H:%M:%S")))
        f:close()
    end
end

-- Hammerspoon 起動時: launcher が動いてなければ spawn
-- 注: `pgrep -f folder_launcher.py` は hs.execute が bash 経由で走らせる際、
-- bash 自身のコマンドラインが "folder_launcher.py" を含むためマッチしてしまう。
-- そのため `ps | grep '[f]older_launcher.py'` の自己除外パターンを使う。
_spawn_log("init.lua reached launcher-check section")
local pgrep_out = hs.execute("ps auxww | grep '[P]ython .*folder_launcher.py' | head -1") or ""
_spawn_log(string.format("check result: len=%d content=%q", #pgrep_out, pgrep_out:sub(1, 200)))
if pgrep_out:match("%S") == nil then
    spawn_launcher()
else
    _spawn_log("existing launcher detected, skip spawn")
end

-- 毎日4:00 に予防的再起動（TCC陳腐化対策）
SokuDailyRestartTimer = hs.timer.doAt("04:00", "1d", restart_launcher_and_keyboards)

-- /tmp/sokulauncher_restart_requested を透明キーボードが touch すると復旧発火
SokuRestartTriggerPoll = hs.timer.doEvery(3, function()
    if hs.fs.attributes(RESTART_TRIGGER) then
        restart_launcher_and_keyboards()
    end
end)
