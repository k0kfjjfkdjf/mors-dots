-- Цвета берутся из lua/theme.lua — его пишет ~/.config/rice/rice.py при смене темы
local ok, t = pcall(require, "lua.theme")
if not ok then
    t = {
        border = { "rgba(33ccffee)", "rgba(00ff99ee)" }, border_angle = 45,
        border_inactive = "rgba(595959aa)", shadow = "rgba(1a1a1aee)",
        group_active = "rgba(cba6f7ee)", group_inactive = "rgba(313244aa)",
        groupbar_active = "rgba(cba6f7ff)", groupbar_inactive = "rgba(313244ff)",
        groupbar_locked = "rgba(f38ba8ff)", groupbar_text = "rgba(ffffffff)",
    }
end

hl.config({
    general = {
        gaps_in     = 5,
        gaps_out    = 10,
        border_size = 2,
        col = {
            active_border   = { colors = t.border, angle = t.border_angle },
            inactive_border = t.border_inactive,
        },
        resize_on_border = false,
        allow_tearing    = false,
        layout           = "dwindle",
    },

    decoration = {
        rounding         = 10,
        rounding_power   = 2,
        active_opacity   = 0.9,
        inactive_opacity = 0.8,
        shadow = {
            enabled      = true,
            range        = 6,
            render_power = 3,
            color        = t.shadow,
        },
        blur = {
            enabled  = true,
            size     = 3,
            passes   = 2,
            vibrancy = 0.1696,
        },
    },

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
            text_color    = t.groupbar_text,
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
