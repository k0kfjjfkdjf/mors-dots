-- Машина pc1: три монитора, прогрев 180 Гц, бинды мониторов
-- Мониторы по описанию — порт (HDMI-A-1/2) не важен.
--  ┌─────────┐┌───────────────┐┌──────────────┐
--  │  BenQ   ││   MKG (DP-2)  ││ Samsung (TV) │
--  │1280x1024││ 1920x1080@180 ││  1920x1080   │
--  └─────────┘└───────────────┘└──────────────┘
--     0x0         1280x0           3200x0

local M = {
    benq    = "desc:BNQ BenQ FP93G 0x00004011",
    main    = "desc:MKG MKF23F180 H80297Q8NSCQL",
    samsung = "desc:Samsung Electric Company SAMSUNG",
}

hl.monitor({ output = M.benq,    mode = "1280x1024@75", position = "0x0",    scale = 1 })
hl.monitor({ output = M.main,    mode = "1920x1080@60", position = "1280x0", scale = 1 })
hl.monitor({ output = M.samsung, mode = "1920x1080@60", position = "3200x0", scale = 1 })
-- Любой новый монитор — справа
hl.monitor({ output = "", mode = "preferred", position = "auto-right", scale = 1 })

-- Рабочие столы по мониторам слева направо: 1 — BenQ, 2 — MKG, 3 — Samsung
hl.workspace_rule({ workspace = "1", monitor = M.benq,    persistent = true, default = true })
hl.workspace_rule({ workspace = "2", monitor = M.main,    persistent = true, default = true })
hl.workspace_rule({ workspace = "3", monitor = M.samsung, persistent = true, default = true })

-- Прогрев: старт на 60 Гц, через 3 минуты основной монитор → 180 Гц
local notify = "~/.config/hypr/scripts/notify_dp2_hz.sh"
hl.on("hyprland.start", function()
    hl.exec_cmd(notify)
    hl.timer(function()
        hl.monitor({ output = M.main, mode = "1920x1080@180", position = "1280x0", scale = 1 })
        hl.exec_cmd("sleep 1; " .. notify)
    end, { timeout = 180000, type = "oneshot" })
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
