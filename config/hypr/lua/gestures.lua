--@file Жесты тачпада
-- Жесты 1:1: окно/стол едет за пальцами. На машинах без тачпада ничего не делают.
-- Справка: https://wiki.hypr.land/configuring/core/binds/gestures/
--
-- Строки --@ — разметка для mors-settings (configurator/): по ним рисуются
-- переключатели и списки, а программа правит только значение под строкой.
-- Число пальцев не настраивается намеренно: 3 и 4 пальца уже распределены так,
-- чтобы жесты не перекрывали друг друга.
--
--  Жест                         │ Действие                        │ Аналог на клавиатуре
-- ──────────────────────────────┼─────────────────────────────────┼─────────────────────
--  3 пальца ← / →               │ соседний рабочий стол           │ SUPER + колесо
--  3 пальца ↑                   │ scratchpad magic (показ/скрыть) │ SUPER + S
--  4 пальца ↑                   │ поверх панели, вкладки остаются │ SUPER + SHIFT + F
--  4 пальца ↓                   │ настоящий полный экран          │ SUPER + F
--  ALT   + 3 пальца ↓           │ закрыть окно                    │ SUPER + C
--  SUPER + 3 пальца (любые)     │ перемещать окно                 │ SUPER + ЛКМ
--  SUPER + 4 пальца (любые)     │ менять размер окна              │ SUPER + ПКМ

local G = {
--@section Рабочие столы
    --@name: Свайп по рабочим столам | type: bool | desc: 3 пальца влево/вправо — соседний рабочий стол
    workspace = true,
    --@name: Скорость свайпа | type: float | range: 0.5-2 | step: 0.1 | desc: Больше — стол переключается при более коротком движении
    workspace_scale = 1.0,
    --@name: Scratchpad свайпом вверх | type: bool | desc: 3 пальца вверх — показать/спрятать стол magic (как SUPER + S)
    special = true,
--@end

--@section Полный экран
    --@name: Поверх панели (4 пальца вверх) | type: bool | desc: Как SUPER + SHIFT + F: окно на весь экран, вкладки браузера остаются. Повторный жест — обратно
    fullscreen_fake = true,
    --@name: Настоящий полный экран (4 пальца вниз) | type: bool | desc: Как SUPER + F: игры, браузер без вкладок. Повторный жест — обратно
    fullscreen_real = true,
--@end

--@section Окна
    --@name: Закрытие окна (3 пальца вниз) | type: bool | desc: Только с зажатой клавишей ниже — чтобы не закрыть окно случайно
    close = true,
    --@name: Клавиша для закрытия | type: enum | options: ALT, CTRL, SHIFT | desc: SUPER не предлагается: SUPER + 3 пальца уже двигают окно
    close_mod = "ALT",
    --@name: Перемещение окна (3 пальца) | type: bool | desc: С зажатым SUPER окно едет за пальцами, как SUPER + ЛКМ
    move = true,
    --@name: Изменение размера (4 пальца) | type: bool | desc: С зажатым SUPER размер меняется за пальцами, как SUPER + ПКМ
    resize = true,
--@end
}

-- ── дальше логика, разметки нет ─────────────────────────────────────────────

local fsToggle = require("lua.fullscreen").toggle

if G.workspace then
    hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace", scale = G.workspace_scale })
end
if G.special then
    hl.gesture({ fingers = 3, direction = "up", action = "special", workspace_name = "magic" })
end
if G.fullscreen_fake then
    hl.gesture({ fingers = 4, direction = "up", action = fsToggle(2, 1) })
end
if G.fullscreen_real then
    hl.gesture({ fingers = 4, direction = "down", action = fsToggle(2, 2) })
end
if G.close then
    hl.gesture({ fingers = 3, direction = "down", mods = G.close_mod, action = "close" })
end
if G.move then
    hl.gesture({ fingers = 3, direction = "swipe", mods = "SUPER", action = "move" })
end
if G.resize then
    hl.gesture({ fingers = 4, direction = "swipe", mods = "SUPER", action = "resize" })
end
