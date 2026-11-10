hl.window_rule({
    name  = "suppress-maximize-events",
    match = { class = ".*" },
    suppress_event = "maximize",
})

hl.window_rule({
    name  = "fix-xwayland-drags",
    match = { class = "^$", title = "^$", xwayland = true, float = true, fullscreen = false, pin = false },
    no_focus = true,
})

hl.window_rule({
    name  = "move-hyprland-run",
    match = { class = "hyprland-run" },
    move  = "20 monitor_h-120",
    float = true,
})

-- Super+F (полный экран 2/2: игры, браузер без вкладок) — курсор не выходит за окно.
-- Super+Shift+F (поверх панели, 2/1) курсор не держит. Выйти — снова Super+F.
-- Если Hyprland всё же отпустит курсор — его вернёт lua/pointer_lock.lua.
hl.window_rule({
    name  = "confine-pointer-in-fullscreen",
    match = { fullscreen_state_internal = 2, fullscreen_state_client = 2 },
    confine_pointer = true,
})
