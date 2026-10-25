hl.config({ animations = { enabled = true } })

hl.curve("easeOutQuint",   { type = "bezier", points = { {0.23, 1},    {0.32, 1}  } })
hl.curve("easeInOutCubic", { type = "bezier", points = { {0.65, 0.05}, {0.36, 1}  } })
hl.curve("linear",         { type = "bezier", points = { {0, 0},       {1, 1}     } })
hl.curve("almostLinear",   { type = "bezier", points = { {0.5, 0.5},   {0.75, 1}  } })
hl.curve("quick",          { type = "bezier", points = { {0.15, 0},    {0.1, 1}   } })

local A = function(leaf, speed, curve, style)
    hl.animation({ leaf = leaf, enabled = true, speed = speed, bezier = curve, style = style })
end

A("global",        10,   "default")
A("border",        5.39, "easeOutQuint")
A("windows",       4.79, "easeOutQuint")
A("windowsIn",     4.1,  "easeOutQuint", "popin 87%")
A("windowsOut",    1.49, "linear",       "popin 87%")
A("fadeIn",        1.73, "almostLinear")
A("fadeOut",       1.46, "almostLinear")
A("fade",          3.03, "quick")
A("layers",        3.81, "easeOutQuint")
A("layersIn",      4,    "easeOutQuint", "fade")
A("layersOut",     1.5,  "linear",       "fade")
A("fadeLayersIn",  1.79, "almostLinear")
A("fadeLayersOut", 1.39, "almostLinear")
A("workspaces",    1.94, "almostLinear", "fade")
A("workspacesIn",  1.21, "almostLinear", "fade")
A("workspacesOut", 1.94, "almostLinear", "fade")
A("zoomFactor",    7,    "quick")

-- Вращающийся градиент рамки (включается темой, например Aurora)
local ok, t = pcall(require, "lua.theme")
if ok and t.border_loop then
    hl.animation({ leaf = "borderangle", enabled = true, speed = 100, bezier = "linear", style = "loop" })
end
