-- Машина laptop: один экран eDP-1, дробный масштаб 1.25
-- (при 1.5 меню HyprPanel не влезало по высоте; 1.25 даёт запас)
hl.monitor({ output = "eDP-1", mode = "preferred", position = "auto", scale = 1.25 })

-- Ctrl+Super+D → 0 — выключить/включить экран, Esc — отмена
hl.bind("SUPER + CTRL + D", hl.dsp.submap("monitor_power"))
hl.define_submap("monitor_power", "reset", function()
    hl.bind("0",      hl.dsp.dpms())
    hl.bind("escape", hl.dsp.submap("reset"))
end)

return {}
