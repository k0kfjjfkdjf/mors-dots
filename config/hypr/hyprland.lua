-- mors-dots · Hyprland 0.56+ (Lua-конфиг)
-- Общие модули — lua/*.lua. Всё, что зависит от конкретной машины
-- (мониторы, их бинды, прогрев 180 Гц), — в lua/host.lua:
-- install.sh делает его ссылкой на hosts/<машина>/hypr.lua.

require("lua.env")
require("lua.host")
require("lua.autostart")
require("lua.appearance")
require("lua.animations")
require("lua.input")
require("lua.windowrules")
require("lua.keybinds")
