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

-- Окно ввода пароля (polkit: pkexec из mors-settings, установщики и т.п.). Без этого правила оно могло
-- открыться позади окна или на другом рабочем столе — слышен только звук. Теперь: поверх всего, по центру,
-- видно на любом рабочем столе, забирает фокус, фон затемняется.
hl.window_rule({
    name  = "polkit-dialog-on-top",
    match = { class = "^(org\\.kde\\.polkit-kde-authentication-agent-1|polkit-kde-authentication-agent-1|hyprpolkitagent|polkit-gnome-authentication-agent-1)$" },
    float = true,
    center = true,
    pin = true,
    stay_focused = true,
    dim_around = true,
})

-- то же по заголовку — если у агента другое имя класса
hl.window_rule({
    name  = "polkit-dialog-on-top-by-title",
    match = { title = "(?i)^(authentication required|требуется (аутентификация|проверка подлинности|авторизация))$" },
    float = true,
    center = true,
    pin = true,
    stay_focused = true,
    dim_around = true,
})

-- Super+F (полный экран 2/2: игры, браузер без вкладок) — курсор не выходит за окно.
-- Super+Shift+F (поверх панели, 2/1) курсор не держит. Выйти — снова Super+F.
-- Если Hyprland всё же отпустит курсор — его вернёт lua/pointer_lock.lua.
hl.window_rule({
    name  = "confine-pointer-in-fullscreen",
    match = { fullscreen_state_internal = 2, fullscreen_state_client = 2 },
    confine_pointer = true,
})
