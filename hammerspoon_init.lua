-- 即ランチャー: デスクトップダブルクリック検知
-- Hammerspoonがクリックを検知 → /tmp/sokulauncher_trigger に座標を書く
-- Python側がそれを読んでメニューを表示する

local TRIGGER_FILE = "/tmp/sokulauncher_trigger"
local lastClickTime = 0
local lastClickX = 0
local lastClickY = 0
local DOUBLE_CLICK_THRESHOLD = 0.4  -- 秒
local MOVE_THRESHOLD = 5            -- ピクセル

-- デスクトップクリックかどうか判定（クリック座標にウィンドウがなければデスクトップ）
local function isDesktopClick(x, y)
    for _, win in ipairs(hs.window.orderedWindows()) do
        local f = win:frame()
        if x >= f.x and x <= f.x + f.w and y >= f.y and y <= f.y + f.h then
            return false  -- ウィンドウの上をクリックしている
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
