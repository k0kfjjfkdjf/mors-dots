-- Машина по умолчанию: мониторы расставляются автоматически.
-- Свою машину: скопируй hosts/pc1 в hosts/<имя>, поправь и запусти install.sh --host <имя>.
-- Описания мониторов: hyprctl monitors all | grep description

hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

-- Ctrl+Super+D → 0 — вкл/выкл все мониторы, Esc — отмена
hl.bind("SUPER + CTRL + D", hl.dsp.submap("monitor_power"))
hl.define_submap("monitor_power", "reset", function()
    hl.bind("0",      hl.dsp.dpms())
    hl.bind("escape", hl.dsp.submap("reset"))
end)

return {}
