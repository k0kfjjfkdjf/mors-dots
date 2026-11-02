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
