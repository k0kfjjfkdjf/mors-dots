hl.on("hyprland.start", function()
    hl.exec_cmd("/usr/lib/polkit-kde-authentication-agent-1")
    hl.exec_cmd("nm-applet --indicator")
    hl.exec_cmd("hyprpanel")
    -- шестерёнка в панели управления HyprPanel открывает наши настройки (configurator/app)
    hl.exec_cmd('python3 "$(dirname "$(readlink -f ~/.config/hypr)")/../configurator/app/gear-redirect.py"')
    -- обои текущей темы (rice сам поднимет awww/swww-daemon)
    hl.exec_cmd("python3 ~/.config/rice/rice.py wallpaper")
    -- простой: блокировка, экраны, сон. Конфиг hypridle.conf пишет mors-settings → Система → Электропитание;
    -- пока его нет, hypridle сразу выходит и ничего не делает
    hl.exec_cmd("hypridle")
    -- батарея (предупредить / критично) и режим производительности; без ~/.config/hypr/power.env сразу выходит
    hl.exec_cmd("~/.config/hypr/scripts/power.sh watch")
    -- hl.exec_cmd("env QT_QPA_PLATFORM=xcb AmneziaVPN")
end)
