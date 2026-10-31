-- Машина laptop: один экран eDP-1, дробный масштаб 1.25
-- (при 1.5 меню HyprPanel не влезало по высоте; 1.25 даёт запас)
-- Таблица MON правится mors-settings («Система» → «Мониторы»).
local MON = {
--@monitors
    edp = { output = "eDP-1", mode = "preferred", position = "auto", scale = 1.25, transform = 0 },
--@end
}
local function apply(m, mode)
    local rule = { output = m.output, mode = mode or m.mode, position = m.position, scale = m.scale }
    if m.transform and m.transform ~= 0 then rule.transform = m.transform end
    hl.monitor(rule)
end
for _, m in pairs(MON) do apply(m) end

-- Ctrl+Super+D → 0 — выключить/включить экран, Esc — отмена
hl.bind("SUPER + CTRL + D", hl.dsp.submap("monitor_power"))
hl.define_submap("monitor_power", "reset", function()
    hl.bind("0",      hl.dsp.dpms())
    hl.bind("escape", hl.dsp.submap("reset"))
end)

return {}
