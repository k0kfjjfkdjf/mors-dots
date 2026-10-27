-- Жесты тачпада (1:1). На машинах без тачпада просто ничего не делают.
-- Справка: https://wiki.hypr.land/configuring/core/binds/gestures/
--
--  Жест                        │ Действие                        │ Аналог на клавиатуре
-- ─────────────────────────────┼─────────────────────────────────┼─────────────────────
--  3 пальца ← / →              │ соседний рабочий стол           │ SUPER + колесо
--  3 пальца ↑                  │ scratchpad magic (показ/скрыть) │ SUPER + S
--  4 пальца ↑                  │ поверх панели, вкладки остаются │ SUPER + SHIFT + F
--  4 пальца ↓                  │ настоящий полный экран          │ SUPER + F
--  ALT   + 3 пальца ↓          │ закрыть окно                    │ SUPER + C
--  SUPER + 3 пальца (любые)    │ перемещать окно                 │ SUPER + ЛКМ
--  SUPER + 4 пальца (любые)    │ менять размер окна              │ SUPER + ПКМ

local fsToggle = require("lua.fullscreen").toggle

-- Рабочие столы и scratchpad
hl.gesture({ fingers = 3, direction = "horizontal", action = "workspace" })
hl.gesture({ fingers = 3, direction = "up", action = "special", workspace_name = "magic" })

-- Полный экран (повторный жест возвращает окно в обычный вид)
hl.gesture({ fingers = 4, direction = "up",   action = fsToggle(2, 1) })
hl.gesture({ fingers = 4, direction = "down", action = fsToggle(2, 2) })

-- Закрыть окно — только с ALT, чтобы не сработало случайно
hl.gesture({ fingers = 3, direction = "down", mods = "ALT", action = "close" })

-- Перемещение и ресайз окна — с зажатым SUPER
hl.gesture({ fingers = 3, direction = "swipe", mods = "SUPER", action = "move" })
hl.gesture({ fingers = 4, direction = "swipe", mods = "SUPER", action = "resize" })
