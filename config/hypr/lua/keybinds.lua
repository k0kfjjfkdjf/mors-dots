local mainMod     = "SUPER"
local terminal    = "kitty"
local fileManager = "dolphin"
local menu        = "rofi -show drun"

local function key(k) return mainMod .. " + " .. k end
local exec = hl.dsp.exec_cmd

-- Переключатель полного экрана без «смешанных» состояний:
-- из любого фуллскрина возвращаемся в обычное окно, из обычного — входим в нужный режим.
-- internal=2 — окно на весь экран поверх панели; client=2 — приложению сказано "фуллскрин"
-- (игры, браузер прячет вкладки), client=1 — "развёрнуто" (вкладки остаются).
local function fsToggle(internal, client)
    return function()
        local w = hl.get_active_window()
        if not w then return end
        if w.fullscreen ~= 0 or w.fullscreen_client ~= 0 then
            hl.dispatch(hl.dsp.window.fullscreen_state({ internal = 0, client = 0, action = "set" }))
        else
            hl.dispatch(hl.dsp.window.fullscreen_state({ internal = internal, client = client, action = "set" }))
        end
    end
end

-- Приложения
hl.bind(key("Q"),            exec(terminal))
hl.bind(key("E"),            exec(fileManager))
hl.bind(key("D"),            exec(menu))
hl.bind(key("R"),            exec(menu))
hl.bind(key("P"),            exec("discord"))
hl.bind(key("CTRL + L"),     exec("chromium"))
hl.bind(key("CTRL + J"),     exec("flameshot gui"))
hl.bind("Print",             exec("flameshot gui"))   -- клавиша PrintScreen

-- Окна
hl.bind(key("C"),            hl.dsp.window.close())
hl.bind(key("V"),            hl.dsp.window.float({ action = "toggle" }))
hl.bind(key("F"),            fsToggle(2, 2))   -- настоящий полный экран (игры, браузер без вкладок)
hl.bind(key("SHIFT + F"),    fsToggle(2, 1))   -- поверх панели, вкладки остаются
hl.bind(key("M"),            exec("command -v hyprshutdown >/dev/null 2>&1 && hyprshutdown || hyprctl dispatch 'hl.dsp.exit()'"))

-- Группы (вкладки)
hl.bind(key("T"),            hl.dsp.group.toggle())
hl.bind(key("Tab"),          hl.dsp.group.next())

-- Фокус стрелками
hl.bind(key("left"),         hl.dsp.focus({ direction = "left" }))
hl.bind(key("right"),        hl.dsp.focus({ direction = "right" }))
hl.bind(key("up"),           hl.dsp.focus({ direction = "up" }))
hl.bind(key("down"),         hl.dsp.focus({ direction = "down" }))

-- Рабочие столы 1–10
for i = 1, 10 do
    local k = tostring(i % 10)
    hl.bind(key(k),           hl.dsp.focus({ workspace = i }))
    hl.bind(key("SHIFT + " .. k), hl.dsp.window.move({ workspace = i }))
end

-- Scratchpad
hl.bind(key("S"),            hl.dsp.workspace.toggle_special("magic"))
hl.bind(key("SHIFT + S"),    hl.dsp.window.move({ workspace = "special:magic" }))

-- Колесо мыши — по рабочим столам
hl.bind(key("mouse_down"),   hl.dsp.focus({ workspace = "e+1" }))
hl.bind(key("mouse_up"),     hl.dsp.focus({ workspace = "e-1" }))

-- Перетаскивание / ресайз мышью
hl.bind(key("mouse:272"),    hl.dsp.window.drag(),   { mouse = true })
hl.bind(key("mouse:273"),    hl.dsp.window.resize(), { mouse = true })

-- Мультимедиа
local lr = { locked = true, repeating = true }
hl.bind("XF86AudioRaiseVolume",  exec("wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ 5%+"), lr)
hl.bind("XF86AudioLowerVolume",  exec("wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-"),      lr)
hl.bind("XF86AudioMute",         exec("wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),     lr)
hl.bind("XF86AudioMicMute",      exec("wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle"),   lr)
hl.bind("XF86MonBrightnessUp",   exec("brightnessctl -e4 -n2 set 5%+"),                  lr)
hl.bind("XF86MonBrightnessDown", exec("brightnessctl -e4 -n2 set 5%-"),                  lr)
hl.bind("XF86AudioNext",  exec("playerctl next"),       { locked = true })
hl.bind("XF86AudioPause", exec("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPlay",  exec("playerctl play-pause"), { locked = true })
hl.bind("XF86AudioPrev",  exec("playerctl previous"),   { locked = true })

-- Меню тем (Rofi)
hl.bind(key("SHIFT + T"),    exec("~/.config/rice/theme-menu.sh"))
-- Обои внутри темы: SUPER+SHIFT+W — следующие, SUPER+CTRL+W — случайные
hl.bind(key("SHIFT + W"),    exec("python3 ~/.config/rice/rice.py next"))
hl.bind(key("CTRL + W"),     exec("python3 ~/.config/rice/rice.py random"))

-- Бинды мониторов (Ctrl+Super+D …) и прочее машинное — в hosts/<машина>/hypr.lua
