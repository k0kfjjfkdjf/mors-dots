-- Машина pc1: три монитора, прогрев 180 Гц, бинды мониторов
-- Мониторы по описанию — порт (HDMI-A-1/2, DP-2) не важен.
--  ┌─────────┐┌───────────────┐┌──────────────┐
--  │  BenQ   ││      MKG      ││ Samsung (TV) │
--  │1280x1024││ 1920x1080@180 ││  1920x1080   │
--  └─────────┘└───────────────┘└──────────────┘
--     0x0         1280x0           3200x0
--
-- Таблица MON — единственное место, где заданы мониторы. Её правит mors-settings
-- («Система» → «Мониторы»): mode, position, scale, transform (0/1/2/3 = 0°/90°/180°/270°).
-- warm — режим после прогрева: стартуем на mode, через warm_after мс переходим на warm.
local MON = {
--@monitors
    benq    = { output = "desc:BNQ BenQ FP93G 0x00004011", mode = "1280x1024@75", position = "0x0", scale = 1, transform = 0 },
    main    = { output = "desc:MKG MKF23F180 H80297Q8NSCQL", mode = "1920x1080@60", position = "1280x0", scale = 1, transform = 0, warm = "1920x1080@180" },
    samsung = { output = "desc:Samsung Electric Company SAMSUNG", mode = "1920x1080@60", position = "3200x0", scale = 1, transform = 0 },
--@end
}
local warm_after = 180000   -- 3 минуты

-- Прогрев переживает перечитывание конфига (hyprctl reload — его делают смена темы и
-- mors-settings): после прогрева в каталоге текущего сеанса Hyprland ставится метка,
-- и при перечитывании монитор сразу получает warm, а не падает обратно на 60 Гц.
-- Каталог сеанса удаляется при выходе — следующий вход снова начнётся с прогрева.
local sig = os.getenv("HYPRLAND_INSTANCE_SIGNATURE") or ""
local warm_flag = (os.getenv("XDG_RUNTIME_DIR") or "/tmp") .. "/hypr/" .. sig .. "/mors-warm-done"
local function warm_done()
    if sig == "" or type(io) ~= "table" then return false end
    local ok, f = pcall(io.open, warm_flag, "r")
    if ok and f then f:close() return true end
    return false
end

local function apply(m, mode)
    local rule = { output = m.output, mode = mode or m.mode, position = m.position, scale = m.scale }
    if m.transform and m.transform ~= 0 then rule.transform = m.transform end
    hl.monitor(rule)
end
for _, m in pairs(MON) do apply(m, m.warm and warm_done() and m.warm or m.mode) end
-- Любой новый монитор — справа
hl.monitor({ output = "", mode = "preferred", position = "auto-right", scale = 1 })

-- Короткие имена для биндов и правил ниже
local M = {}
for k, m in pairs(MON) do M[k] = m.output end

-- Рабочие столы по мониторам слева направо: 1 — BenQ, 2 — MKG, 3 — Samsung
hl.workspace_rule({ workspace = "1", monitor = M.benq,    persistent = true, default = true })
hl.workspace_rule({ workspace = "2", monitor = M.main,    persistent = true, default = true })
hl.workspace_rule({ workspace = "3", monitor = M.samsung, persistent = true, default = true })

-- Прогрев: старт на mode, через warm_after — warm (позиция и масштаб — из таблицы MON)
local notify = "~/.config/hypr/scripts/notify_dp2_hz.sh"
hl.on("hyprland.start", function()
    hl.exec_cmd(notify)
    hl.timer(function()
        for _, m in pairs(MON) do
            if m.warm then apply(m, m.warm) end
        end
        hl.exec_cmd("touch '" .. warm_flag .. "'; sleep 1; " .. notify)
    end, { timeout = warm_after, type = "oneshot" })
end)

-- Переключение 60/180 Гц на основном мониторе
hl.bind("SUPER + CTRL + R", hl.dsp.exec_cmd("~/.config/hypr/scripts/toggle_dp2_hz.sh"))

-- Ctrl+Super+D → 1/2/3 — вкл/выкл монитор, 0 — все, Esc — отмена
hl.bind("SUPER + CTRL + D", hl.dsp.submap("monitor_power"))
hl.define_submap("monitor_power", "reset", function()
    hl.bind("1",      hl.dsp.dpms({ monitor = M.benq }))
    hl.bind("2",      hl.dsp.dpms({ monitor = M.main }))
    hl.bind("3",      hl.dsp.dpms({ monitor = M.samsung }))
    hl.bind("0",      hl.dsp.dpms())
    hl.bind("escape", hl.dsp.submap("reset"))
end)

return M
