--@file Внешний вид
-- Цвета берутся из lua/theme.lua — его пишет ~/.config/rice/rice.py при смене темы
local ok, t = pcall(require, "lua.theme")
if not ok then
    t = {
        border = { "rgba(33ccffee)", "rgba(00ff99ee)" }, border_angle = 45,
        border_inactive = "rgba(595959aa)", shadow = "rgba(1a1a1aee)",
        group_active = "rgba(cba6f7ee)", group_inactive = "rgba(313244aa)",
        groupbar_active = "rgba(cba6f7ff)", groupbar_inactive = "rgba(313244ff)",
        groupbar_locked = "rgba(f38ba8ff)", groupbar_text = "rgba(ffffffff)",
        groupbar_text_inactive = "rgba(ffffffff)",
    }
end

-- Строки --@ — разметка для mors-settings (configurator/): по ним рисуется окно настроек.
-- Цвета (t.*) задаёт тема rice — в настройках они только для чтения.

hl.config({
--@section Окна и отступы
    general = {
        --@name: Внутренние отступы | type: int | range: 0-30 | desc: Расстояние между окнами, пикс.
        gaps_in     = 5,
        --@name: Внешние отступы | type: int | range: 0-60 | desc: От окон до краёв экрана, пикс.
        gaps_out    = 10,
        --@name: Толщина рамки | type: int | range: 0-8
        border_size = 2,
        col = {
            active_border   = { colors = t.border, angle = t.border_angle },
            inactive_border = t.border_inactive,
        },
        --@name: Тянуть за рамку | type: bool | desc: Менять размер окна, потянув за его рамку мышью
        resize_on_border = false,
        --@name: Tearing | type: bool | desc: Разрешить разрывы кадра в играх ради меньшей задержки
        allow_tearing    = false,
        --@name: Раскладка окон | type: enum | options: dwindle, master | desc: dwindle — делит экран спиралью, master — одно главное окно и стопка
        layout           = "dwindle",
    },
--@end

--@section Оформление окон
    decoration = {
        --@name: Скругление углов | type: int | range: 0-30
        rounding         = 10,
        --@name: Форма скругления | type: float | range: 1-10 | step: 0.5 | desc: 2 — обычный круг, больше — «квадратнее» (суперэллипс)
        rounding_power   = 2,
        --@name: Прозрачность активного окна | type: float | range: 0.3-1 | step: 0.05
        active_opacity   = 0.9,
        --@name: Прозрачность неактивных окон | type: float | range: 0.3-1 | step: 0.05
        inactive_opacity = 0.8,
        shadow = {
            --@name: Тень | type: bool
            enabled      = true,
            --@name: Размер тени | type: int | range: 0-40
            range        = 6,
            --@name: Резкость тени | type: int | range: 1-4 | desc: 1 — мягкая, 4 — резкая
            render_power = 3,
            --@name: Цвет тени
            color        = t.shadow,
        },
        blur = {
            --@name: Размытие | type: bool | desc: Размытие фона под прозрачными окнами
            enabled  = true,
            --@name: Сила размытия | type: int | range: 1-15
            size     = 3,
            --@name: Проходы размытия | type: int | range: 1-6 | desc: Больше — плавнее, но тяжелее для видеокарты
            passes   = 2,
            --@name: Насыщенность под размытием | type: float | range: 0-1 | step: 0.05
            vibrancy = 0.1696,
        },
    },
--@end

    dwindle = { preserve_split = true },
    master  = { new_on_top = true },

    misc = {
        force_default_wallpaper = -1,
        disable_hyprland_logo   = false,
    },

    group = {
        col = {
            border_active   = t.group_active,
            border_inactive = t.group_inactive,
        },
        groupbar = {
            height        = 18,
            font_size     = 11,
            text_color          = t.groupbar_text,
            text_color_inactive = t.groupbar_text_inactive,
            gradients     = true,
            render_titles = true,
            scrolling     = true,
            col = {
                active        = t.groupbar_active,
                inactive      = t.groupbar_inactive,
                locked_active = t.groupbar_locked,
            },
        },
    },
})
