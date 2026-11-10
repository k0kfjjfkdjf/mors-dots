-- Мышь не уходит из окна в полном экране Super+F (fullscreen 2/2: игры, браузер без вкладок).
--
-- Основное — правило confine_pointer в windowrules.lua. Но Hyprland отпускает курсор, когда под ним
-- оказывается «дочерняя» поверхность окна (видео в браузере, оверлей игры) или мышь дёрнули резко —
-- и тогда можно доехать до соседнего монитора и кликнуть по чужому окну. Здесь страховка:
-- как только фокус ушёл на другой монитор или к окну на нём, курсор возвращается в ближайшую точку
-- окна в полном экране, фокус — ему.
--
-- Щит: пока игра в полном экране и в фокусе, остальные мониторы накрыты невидимым слоем
-- (scripts/input-shield.py) — клик по ним уходит в пустоту, даже если курсор успел туда заехать.
--
-- Намеренно уйти можно: с зажатым Super (Super+цифра, Super+стрелка — переход с клавиатуры) или
-- выключив полный экран (снова Super+F). Тогда и щит убирается. Если окно ушло на скрытый рабочий
-- стол — не держим.

local SUPER = { [133] = true, [134] = true }   -- Super_L / Super_R (keycode libinput + 8)
local SHIELD = "~/.config/hypr/scripts/input-shield.py"
local KILL_SHIELD = "pkill -f '[i]nput-shield.py'"   -- [i] — чтобы pkill не убил собственную оболочку
local locked = nil                             -- "address:0x…" окна в полном экране 2/2
local superDown = false
local busy = false

local function isLockMode(w)
    return w ~= nil and w.fullscreen == 2 and w.fullscreen_client == 2
end

-- окно, которое держим сейчас; nil — не держим
local function lockedWindow()
    if not locked then return nil end
    local w = hl.get_window(locked)
    if not isLockMode(w) then locked = nil; return nil end
    local mon, ws = w.monitor, w.workspace
    if not mon or not ws or not mon.active_workspace or mon.active_workspace.id ~= ws.id then
        return nil                                -- окно не на виду (другой рабочий стол)
    end
    return w
end

local function pullBack(w)
    if busy then return end
    busy = true
    local c = hl.get_cursor_pos()
    local x0, y0 = w.at.x, w.at.y
    local x1, y1 = x0 + w.size.x - 2, y0 + w.size.y - 2
    local x, y = x0 + w.size.x / 2, y0 + w.size.y / 2
    if c then                                     -- ближайшая точка внутри окна, а не центр — без рывка
        x = math.min(math.max(c.x, x0 + 1), x1)
        y = math.min(math.max(c.y, y0 + 1), y1)
    end
    hl.dispatch(hl.dsp.focus({ window = locked }))
    hl.dispatch(hl.dsp.cursor.move({ x = math.floor(x), y = math.floor(y) }))
    busy = false
end

-- щит: nil — убрать, иначе имя монитора с игрой (его не закрываем)
local shieldFor = false                         -- false — ещё не знаем (после перечитывания конфига)
local function shield(mon)
    if mon == shieldFor then return end
    shieldFor = mon
    local cmd = KILL_SHIELD
    if mon then
        local ok, mons = pcall(hl.get_monitors)
        if ok and mons and #mons > 1 then cmd = cmd .. "; exec " .. SHIELD .. " '" .. mon .. "'" end
    end
    pcall(hl.exec_cmd, cmd)
end

local function update()
    local w = lockedWindow()
    local ok, act = pcall(hl.get_active_window)
    if w and ok and act and act.address == w.address then shield(w.monitor.name) else shield(nil) end
end

hl.on("window.fullscreen", function(w)
    if not w then return end
    local sel = "address:" .. w.address
    if isLockMode(w) then
        locked = sel
    elseif locked == sel then
        locked = nil
    end
    update()
end)

hl.on("input.keyboard.key", function(keycode, _, pressed)
    if SUPER[keycode] then superDown = pressed ~= 0 end
end)

hl.on("monitor.focused", function(mon)
    if not (superDown or busy or not mon) then
        local w = lockedWindow()
        if w and w.monitor.name ~= mon.name then pullBack(w) end
    end
    if not busy then update() end
end)

hl.on("window.active", function(a)
    if not (superDown or busy or not a) then
        local w = lockedWindow()
        if w and a.address ~= w.address and a.monitor and a.monitor.name ~= w.monitor.name then pullBack(w) end
    end
    if not busy then update() end
end)

hl.on("workspace.active", function() update() end)
hl.on("window.close", function() update() end)

-- окно уже было в полном экране до перечитывания конфига
local ok, a = pcall(hl.get_active_window)
if ok and isLockMode(a) then locked = "address:" .. a.address end
update()                                        -- после перечитывания конфига: убрать старый щит или поставить новый
