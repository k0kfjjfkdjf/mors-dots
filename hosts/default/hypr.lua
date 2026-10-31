-- Машина по умолчанию: мониторы расставляются автоматически.
-- Свою машину: скопируй hosts/pc1 в hosts/<имя>, поправь и запусти install.sh --host <имя>.
-- Описания мониторов: hyprctl monitors all | grep description

-- Таблица MON правится mors-settings («Система» → «Мониторы»): мониторы, которые ты
-- расставишь там, появятся здесь; остальные расставляются автоматически.
local MON = {
--@monitors
--@end
}
local function apply(m, mode)
    local rule = { output = m.output, mode = mode or m.mode, position = m.position, scale = m.scale }
    if m.transform and m.transform ~= 0 then rule.transform = m.transform end
    hl.monitor(rule)
end
for _, m in pairs(MON) do apply(m) end
hl.monitor({ output = "", mode = "preferred", position = "auto", scale = "auto" })

-- Ctrl+Super+D → 0 — вкл/выкл все мониторы, Esc — отмена
hl.bind("SUPER + CTRL + D", hl.dsp.submap("monitor_power"))
hl.define_submap("monitor_power", "reset", function()
    hl.bind("0",      hl.dsp.dpms())
    hl.bind("escape", hl.dsp.submap("reset"))
end)

return {}
