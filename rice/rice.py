#!/usr/bin/env python3
"""rice — переключатель тем для Hyprland-райса.

    rice.py list              — список тем
    rice.py current           — текущая тема
    rice.py apply <тема>      — применить тему ко всей системе
    rice.py wallpaper         — заново поставить обои текущей темы (для автозапуска)
    rice.py next|prev|random  — следующие / предыдущие / случайные обои в текущей теме

Одна тема = один файл themes/<имя>.json (27 цветов в слотах Catppuccin + акценты).
Из него генерируются конфиги: Hyprland, HyprPanel, Kitty, Rofi, Qt/KDE (Dolphin),
GTK 3/4, Fish, обои и экран входа SDDM.

Переменная RICE_CONFIG_HOME позволяет прогнать всё на копии ~/.config (для тестов);
RICE_DRY=1 — ничего не перезапускать и не трогать запущенные программы.
"""
import configparser
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

RICE_DIR = Path(__file__).resolve().parent
CFG = Path(os.environ.get("RICE_CONFIG_HOME", Path.home() / ".config"))
DATA = Path(os.environ.get("RICE_DATA_HOME", Path.home() / ".local/share"))
SDDM_DIR = Path(os.environ.get("RICE_SDDM_DIR", "/var/lib/rice"))
DRY = os.environ.get("RICE_DRY") == "1"
STATE = RICE_DIR / "current"


# ---------------------------------------------------------------- цвета
def rgb(h):
    h = h.lstrip("#")[:6]
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(c):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in c)


def mix(a, b, t):
    """t=0 → a, t=1 → b"""
    a, b = rgb(a), rgb(b)
    return hexc(tuple(a[i] + (b[i] - a[i]) * t for i in range(3)))


def kde(h):
    return ",".join(str(v) for v in rgb(h))


def rgba(h, alpha="ff"):
    h = h.lstrip("#")
    return f"rgba({h[:6]}{h[6:8] if len(h) == 8 else alpha})"


class Theme:
    def __init__(self, name):
        path = RICE_DIR / "themes" / f"{name}.json"
        if not path.exists():
            sys.exit(f"Нет темы «{name}». Есть: {', '.join(list_themes())}")
        self.id = name
        self.raw = json.loads(path.read_text())
        self.p = dict(self.raw["palette"])
        acc = self.raw["accent"]
        self.primary = self.p.get(acc["primary"], acc["primary"])
        self.secondary = self.p.get(acc["secondary"], acc["secondary"])
        self.tertiary = self.p.get(acc["tertiary"], acc["tertiary"])
        self.ansi = self.raw["ansi"]
        wp = self.raw.get("wallpapers") or [self.raw["wallpaper"]]
        # local/* — личные картинки (не в git); если их нет на машине — пропускаем
        self.wallpapers = [RICE_DIR / "wallpapers" / w for w in wp if (RICE_DIR / "wallpapers" / w).exists()]
        if not self.wallpapers:
            self.wallpapers = [RICE_DIR / "wallpapers" / f"{name}.png"]
        self.wallpaper = self.wallpapers[wp_index(name) % len(self.wallpapers)]

    def __getattr__(self, k):
        try:
            return self.__dict__["p"][k]
        except KeyError:
            raise AttributeError(k)

    def material(self):
        """Роли Material You — их ждёт rofi от HyprLuna."""
        p = self.p
        m = {}
        for role, c in (("primary", self.primary), ("secondary", self.secondary), ("tertiary", self.tertiary)):
            m[role] = c
            m[f"on-{role}"] = p["crust"]
            m[f"{role}-container"] = mix(p["base"], c, 0.30)
            m[f"on-{role}-container"] = p["text"]
            m[f"{role}-fixed"] = mix(c, "#ffffff", 0.3)
            m[f"{role}-fixed-dim"] = c
            m[f"on-{role}-fixed"] = p["crust"]
            m[f"on-{role}-fixed-variant"] = p["surface1"]
        m.update({
            "error": p["red"], "on-error": p["crust"],
            "error-container": mix(p["base"], p["red"], 0.30), "on-error-container": p["text"],
            "surface": p["base"], "on-surface": p["text"], "on-surface-variant": p["subtext0"],
            "outline": p["overlay0"], "outline-variant": p["surface1"],
            "shadow": "#000000", "scrim": "#000000",
            "inverse-surface": p["text"], "inverse-on-surface": p["base"],
            "inverse-primary": mix(self.primary, p["crust"], 0.5),
            "surface-dim": p["mantle"], "surface-bright": p["surface1"],
            "surface-container-lowest": p["crust"], "surface-container-low": p["mantle"],
            "surface-container": p["base2"], "surface-container-high": p["surface0"],
            "surface-container-highest": p["surface1"],
        })
        return m

    def gradient(self):
        cols = [c[:7] for c in self.raw["border"]]
        if len(cols) == 1:
            cols = cols * 2
        return cols


WP_STATE = RICE_DIR / "wallpaper-index.json"


def wp_index(theme, value=None):
    """Какие обои выбраны в каждой теме (запоминается отдельно для каждой)."""
    try:
        d = json.loads(WP_STATE.read_text())
    except Exception:
        d = {}
    if value is None:
        return int(d.get(theme, 0))
    d[theme] = value
    write(WP_STATE, json.dumps(d))
    return value


def list_themes():
    return sorted(p.stem for p in (RICE_DIR / "themes").glob("*.json"))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".rice-tmp")
    tmp.write_text(text)
    tmp.replace(path)


def run(*cmd, bg=False):
    if DRY:
        return None
    if not shutil.which(cmd[0]):
        return None
    try:
        if bg:
            return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception as e:  # тема всё равно должна примениться целиком
        print(f"  ! {' '.join(cmd)}: {e}")
        return None


# ---------------------------------------------------------------- Hyprland
def apply_hyprland(t):
    border = ", ".join(f'"{rgba(c)}"' for c in t.raw["border"])
    lua = f'''-- Сгенерировано rice.py ({t.raw["name"]}). Не редактируй руками — правь themes/{t.id}.json
return {{
    name            = "{t.id}",
    border          = {{ {border} }},
    border_angle    = {t.raw.get("border_angle", 45)},
    border_loop     = {"true" if t.raw.get("border_loop") else "false"},
    border_inactive = "{rgba(t.raw["border_inactive"])}",
    shadow          = "{rgba(t.crust, "ee")}",
    group_active    = "{rgba(t.primary, "ee")}",
    group_inactive  = "{rgba(t.surface0, "aa")}",
    groupbar_active   = "{rgba(t.primary)}",
    groupbar_inactive = "{rgba(t.surface0)}",
    groupbar_locked   = "{rgba(t.red)}",
    groupbar_text     = "{rgba(t.crust)}",
}}
'''
    write(CFG / "hypr/lua/theme.lua", lua)
    run("hyprctl", "reload")


# ---------------------------------------------------------------- HyprPanel
# Шаблон HyprPanel (catppuccin_mocha.json) использует палитру Catppuccin Mocha.
# Каждый цвет шаблона → слот палитры → цвет нашей темы.
MOCHA = {
    "rosewater": "#f5e0dc", "flamingo": "#f2cdcd", "pink": "#f5c2e7", "mauve": "#cba6f7",
    "red": "#f38ba8", "maroon": "#eba0ac", "peach": "#fab387", "yellow": "#f9e2af",
    "green": "#a6e3a1", "teal": "#94e2d5", "sky": "#89dceb", "sapphire": "#74c7ec",
    "blue": "#89b4fa", "lavender": "#b4befe", "text": "#cdd6f4", "subtext1": "#bac2de",
    "subtext0": "#a6adc8", "overlay2": "#9399b2", "overlay1": "#7f849c", "overlay0": "#6c7086",
    "surface2": "#585b70", "surface1": "#45475a", "surface0": "#313244", "base": "#1e1e2e",
    "base2": "#242438", "mantle": "#181825", "crust": "#11111b",
}


def mocha_slot(h):
    c = rgb(h)
    return min(MOCHA, key=lambda k: sum((a - b) ** 2 for a, b in zip(c, rgb(MOCHA[k]))))


def hyprpanel_theme(t):
    tpl = json.loads((RICE_DIR / "templates/hyprpanel.json").read_text())
    out = {}
    for k, v in tpl.items():
        if isinstance(v, str) and v.startswith("#") and len(v) in (7, 9):
            out[k] = t.p[mocha_slot(v[:7])] + v[7:]
        else:
            out[k] = v
    return out


def apply_hyprpanel(t):
    path = CFG / "hyprpanel/config.json"
    cfg = json.loads(path.read_text()) if path.exists() else {}
    cfg.update(hyprpanel_theme(t))
    cfg["theme.matugen"] = False
    # обоями занимается rice (awww/swww) — иначе HyprPanel перебьёт их при старте
    cfg["wallpaper.enable"] = False
    cfg["wallpaper.image"] = str(t.wallpaper)
    write(path, json.dumps(cfg, ensure_ascii=False, indent=2))
    # HyprPanel сам перечитывает config.json при изменении


# ---------------------------------------------------------------- Kitty
def apply_kitty(t):
    lines = [f"# Сгенерировано rice.py — тема {t.raw['name']}",
             f"foreground {t.text}", f"background {t.base}",
             f"selection_foreground {t.text}", f"selection_background {mix(t.base, t.primary, 0.35)}",
             f"cursor {t.primary}", f"cursor_text_color {t.crust}",
             f"url_color {t.tertiary}",
             f"active_border_color {t.primary}", f"inactive_border_color {t.surface1}",
             f"bell_border_color {t.yellow}",
             f"active_tab_foreground {t.crust}", f"active_tab_background {t.primary}",
             f"inactive_tab_foreground {t.subtext0}", f"inactive_tab_background {t.surface0}",
             f"tab_bar_background {t.mantle}",
             f"mark1_foreground {t.crust}", f"mark1_background {t.primary}"]
    lines += [f"color{i} {c}" for i, c in enumerate(t.ansi)]
    write(CFG / "kitty/theme.conf", "\n".join(lines) + "\n")
    run("pkill", "-USR1", "-x", "kitty")  # kitty перечитывает конфиг по SIGUSR1


# ---------------------------------------------------------------- Rofi
def apply_rofi(t):
    m = t.material()
    g = t.gradient()
    body = "\n".join(f"    {k}: {v};" for k, v in m.items())
    body += f"\n    gradient: linear-gradient(to right, {', '.join(g)});"
    write(CFG / "rofi/colors.rasi", f"/* Сгенерировано rice.py — {t.raw['name']} */\n* {{\n{body}\n}}\n")


# ---------------------------------------------------------------- Qt / KDE (Dolphin, Kate…)
def kde_scheme(t):
    p, P = t.p, t.primary
    common = dict(
        ForegroundNormal=p["text"], ForegroundInactive=p["subtext0"], ForegroundActive=P,
        ForegroundLink=p["sapphire"], ForegroundVisited=p["mauve"],
        ForegroundNegative=p["red"], ForegroundNeutral=p["yellow"], ForegroundPositive=p["green"],
        DecorationFocus=P, DecorationHover=t.secondary,
    )
    groups = {
        "Colors:Window": dict(BackgroundNormal=p["base"], BackgroundAlternate=p["base2"]),
        "Colors:View": dict(BackgroundNormal=p["mantle"], BackgroundAlternate=p["base"]),
        "Colors:Button": dict(BackgroundNormal=p["surface0"], BackgroundAlternate=p["surface1"]),
        "Colors:Tooltip": dict(BackgroundNormal=p["surface0"], BackgroundAlternate=p["base2"]),
        "Colors:Header": dict(BackgroundNormal=p["mantle"], BackgroundAlternate=p["base"]),
        "Colors:Header][Inactive": dict(BackgroundNormal=p["base"], BackgroundAlternate=p["mantle"]),
        "Colors:Complementary": dict(BackgroundNormal=p["crust"], BackgroundAlternate=p["mantle"]),
        "Colors:Selection": dict(BackgroundNormal=P, BackgroundAlternate=mix(p["base"], P, 0.5),
                                 ForegroundNormal=p["crust"], ForegroundInactive=p["surface1"],
                                 ForegroundActive=p["crust"]),
    }
    sections = {}
    for g, vals in groups.items():
        d = dict(common)
        d.update(vals)
        sections[g] = {k: kde(v) for k, v in d.items()}
    sections["WM"] = {
        "activeBackground": kde(p["mantle"]), "activeForeground": kde(p["text"]), "activeBlend": kde(p["text"]),
        "inactiveBackground": kde(p["crust"]), "inactiveForeground": kde(p["subtext0"]),
        "inactiveBlend": kde(p["subtext0"]),
    }
    sections["ColorEffects:Inactive"] = {"Enable": "false", "ChangeSelectionColor": "true"}
    sections["ColorEffects:Disabled"] = {"Color": kde(p["base"]), "ColorAmount": "0", "ColorEffect": "0",
                                         "ContrastAmount": "0.65", "ContrastEffect": "1",
                                         "IntensityAmount": "0.1", "IntensityEffect": "2"}
    return sections


def ini(path):
    c = configparser.RawConfigParser(strict=False, interpolation=None, delimiters=("=",), comment_prefixes=("#", ";"))
    c.optionxform = str
    if path.exists():
        c.read(path, encoding="utf-8")
    return c


def ini_write(c, path):
    from io import StringIO
    s = StringIO()
    c.write(s, space_around_delimiters=False)
    write(path, s.getvalue())


def apply_kde(t):
    scheme = f"Rice{t.raw['name']}"
    sections = kde_scheme(t)
    # 1) файл цветовой схемы — виден в настройках KDE
    sc = configparser.RawConfigParser(interpolation=None)
    sc.optionxform = str
    sc["General"] = {"ColorScheme": scheme, "Name": f"Rice {t.raw['name']}"}
    for s, kv in sections.items():
        sc[s] = kv
    ini_write(sc, DATA / "color-schemes" / f"{scheme}.colors")
    # 2) сразу в kdeglobals — Qt-приложения читают его через plasma-integration
    kg = ini(CFG / "kdeglobals")
    for s, kv in sections.items():
        if not kg.has_section(s):
            kg.add_section(s)
        for k, v in kv.items():
            kg.set(s, k, v)
    if not kg.has_section("General"):
        kg.add_section("General")
    kg.set("General", "ColorScheme", scheme)
    kg.remove_option("General", "ColorSchemeHash")
    if not kg.has_section("KDE"):
        kg.add_section("KDE")
    kg.set("KDE", "widgetStyle", "Breeze")
    ini_write(kg, CFG / "kdeglobals")
    # 3) Dolphin не должен держать свою отдельную схему
    dr = CFG / "dolphinrc"
    if dr.exists():
        import re
        txt = dr.read_text()
        txt2 = re.sub(r"(?m)^(\[UiSettings\]\n(?:(?!\[).*\n)*?)ColorScheme=.*$", rf"\1ColorScheme={scheme}", txt)
        if txt2 != txt:
            write(dr, txt2)
    # 4) сообщить запущенным Qt-приложениям, что палитра сменилась
    run("dbus-send", "--session", "--type=signal", "/KGlobalSettings",
        "org.kde.KGlobalSettings.notifyChange", "int32:0", "int32:0")


# ---------------------------------------------------------------- GTK 3/4
def gtk_breeze_colors(t):
    p, P = t.p, t.primary
    dim = lambda c: mix(p["base"], c, 0.35)
    rules = [  # (подстрока имени, цвет) — первое совпадение побеждает
        ("error_color_insensitive", dim(p["red"])), ("error_color", p["red"]),
        ("success_color_insensitive", dim(p["green"])), ("success_color", p["green"]),
        ("warning_color_insensitive", dim(p["yellow"])), ("warning_color", p["yellow"]),
        ("link_visited", p["mauve"]), ("link_color", p["sapphire"]),
        ("unfocused_insensitive_borders", p["surface1"]), ("insensitive_borders", p["surface1"]),
        ("borders", p["surface2"]), ("tooltip_border", p["surface2"]),
        ("tooltip_background", p["surface0"]), ("tooltip_text", p["text"]),
        ("decoration_focus_backdrop_insensitive", dim(P)), ("decoration_focus_insensitive", dim(P)),
        ("decoration_hover_backdrop_insensitive", dim(P)), ("decoration_hover_insensitive", dim(P)),
        ("decoration", P),
        ("button_background_backdrop_insensitive", p["base2"]), ("button_background_insensitive", p["base2"]),
        ("button_background", p["surface0"]),
        ("button_foreground_active_backdrop_insensitive", p["overlay1"]),
        ("button_foreground_active_insensitive", p["overlay1"]),
        ("button_foreground_backdrop_insensitive", p["overlay1"]),
        ("button_foreground_insensitive", p["overlay1"]), ("button_foreground", p["text"]),
        ("header_background_backdrop", p["base"]), ("header_background_light", p["base"]),
        ("header_background", p["mantle"]), ("header_foreground", p["text"]),
        ("titlebar_background_backdrop", p["base"]), ("titlebar_background_light", p["base"]),
        ("titlebar_background", p["mantle"]), ("titlebar_foreground", p["text"]),
        ("insensitive_base_fg", p["overlay0"]), ("insensitive_base_color", p["mantle"]),
        ("insensitive_selected_bg", p["base2"]), ("insensitive_unfocused_selected_bg", p["base2"]),
        ("insensitive_unfocused_bg", p["base2"]), ("insensitive_bg", p["base2"]),
        ("insensitive_", p["overlay0"]),
        ("unfocused_selected_bg", mix(p["base"], P, 0.4)), ("unfocused_selected_fg", p["text"]),
        ("unfocused_view_bg", p["crust"]), ("unfocused_view_text", p["overlay1"]),
        ("unfocused_base_color", p["mantle"]), ("unfocused_bg_color", p["base"]),
        ("hovering_selected_bg", P), ("selected_bg", P), ("selected_fg", p["crust"]),
        ("view_active_decoration", P), ("view_hover_decoration", P),
        ("content_view_bg", p["mantle"]), ("theme_base_color", p["mantle"]),
        ("theme_bg_color", p["base"]), ("_fg_color", p["text"]), ("text_color", p["text"]),
    ]
    names = ["borders", "content_view_bg", "error_color_backdrop", "error_color",
             "error_color_insensitive_backdrop", "error_color_insensitive", "insensitive_base_color",
             "insensitive_base_fg_color", "insensitive_bg_color", "insensitive_borders", "insensitive_fg_color",
             "insensitive_selected_bg_color", "insensitive_selected_fg_color", "insensitive_unfocused_bg_color",
             "insensitive_unfocused_fg_color", "insensitive_unfocused_selected_bg_color",
             "insensitive_unfocused_selected_fg_color", "link_color", "link_visited_color", "success_color_backdrop",
             "success_color", "success_color_insensitive_backdrop", "success_color_insensitive", "theme_base_color",
             "theme_bg_color", "theme_button_background_backdrop", "theme_button_background_backdrop_insensitive",
             "theme_button_background_insensitive", "theme_button_background_normal",
             "theme_button_decoration_focus_backdrop", "theme_button_decoration_focus_backdrop_insensitive",
             "theme_button_decoration_focus", "theme_button_decoration_focus_insensitive",
             "theme_button_decoration_hover_backdrop", "theme_button_decoration_hover_backdrop_insensitive",
             "theme_button_decoration_hover", "theme_button_decoration_hover_insensitive",
             "theme_button_foreground_active_backdrop", "theme_button_foreground_active_backdrop_insensitive",
             "theme_button_foreground_active", "theme_button_foreground_active_insensitive",
             "theme_button_foreground_backdrop", "theme_button_foreground_backdrop_insensitive",
             "theme_button_foreground_insensitive", "theme_button_foreground_normal", "theme_fg_color",
             "theme_header_background_backdrop", "theme_header_background", "theme_header_background_light",
             "theme_header_foreground_backdrop", "theme_header_foreground",
             "theme_header_foreground_insensitive_backdrop", "theme_header_foreground_insensitive",
             "theme_hovering_selected_bg_color", "theme_selected_bg_color", "theme_selected_fg_color",
             "theme_text_color", "theme_titlebar_background_backdrop", "theme_titlebar_background",
             "theme_titlebar_background_light", "theme_titlebar_foreground_backdrop", "theme_titlebar_foreground",
             "theme_titlebar_foreground_insensitive_backdrop", "theme_titlebar_foreground_insensitive",
             "theme_unfocused_base_color", "theme_unfocused_bg_color", "theme_unfocused_fg_color",
             "theme_unfocused_selected_bg_color_alt", "theme_unfocused_selected_bg_color",
             "theme_unfocused_selected_fg_color", "theme_unfocused_text_color", "theme_unfocused_view_bg_color",
             "theme_unfocused_view_text_color", "theme_view_active_decoration_color",
             "theme_view_hover_decoration_color", "tooltip_background", "tooltip_border", "tooltip_text",
             "unfocused_borders", "unfocused_insensitive_borders", "warning_color_backdrop", "warning_color",
             "warning_color_insensitive_backdrop", "warning_color_insensitive"]
    out = {}
    for n in names:
        out[n] = next(c for key, c in rules if key in n)
    return out


def apply_gtk(t):
    p, P = t.p, t.primary
    colors = gtk_breeze_colors(t)
    css = f"/* Сгенерировано rice.py — {t.raw['name']} */\n"
    for n, c in colors.items():
        css += f"@define-color {n}_breeze {c};\n"
    for d in ("gtk-3.0", "gtk-4.0"):
        write(CFG / d / "colors.css", css)
    # libadwaita (GTK4) берёт свои именованные цвета
    adw = {
        "accent_color": P, "accent_bg_color": P, "accent_fg_color": p["crust"],
        "destructive_color": p["red"], "destructive_bg_color": p["red"], "destructive_fg_color": p["crust"],
        "success_color": p["green"], "warning_color": p["yellow"], "error_color": p["red"],
        "window_bg_color": p["base"], "window_fg_color": p["text"],
        "view_bg_color": p["mantle"], "view_fg_color": p["text"],
        "headerbar_bg_color": p["mantle"], "headerbar_fg_color": p["text"],
        "headerbar_backdrop_color": p["base"], "sidebar_bg_color": p["base2"], "sidebar_fg_color": p["text"],
        "card_bg_color": p["surface0"], "card_fg_color": p["text"],
        "dialog_bg_color": p["base2"], "dialog_fg_color": p["text"],
        "popover_bg_color": p["surface0"], "popover_fg_color": p["text"],
    }
    gtk4 = "@import 'colors.css';\n" + "".join(f"@define-color {k} {v};\n" for k, v in adw.items())
    write(CFG / "gtk-4.0/gtk.css", f"/* Сгенерировано rice.py — {t.raw['name']} */\n" + gtk4)
    g3 = CFG / "gtk-3.0/gtk.css"
    if not g3.exists() or "colors.css" not in g3.read_text():
        write(g3, "@import 'colors.css';\n")
    run("gsettings", "set", "org.gnome.desktop.interface", "color-scheme", "prefer-dark")


# ---------------------------------------------------------------- Fish
def apply_fish(t):
    h = lambda c: c.lstrip("#")[:6]
    p = t.p
    v = {
        "fish_color_normal": h(p["text"]), "fish_color_command": h(t.primary),
        "fish_color_keyword": h(t.secondary), "fish_color_quote": h(p["green"]),
        "fish_color_redirection": h(p["teal"]), "fish_color_end": h(p["overlay2"]),
        "fish_color_error": h(p["red"]), "fish_color_param": h(p["subtext1"]),
        "fish_color_option": h(p["subtext0"]), "fish_color_comment": h(p["overlay0"]),
        "fish_color_operator": h(p["sky"]), "fish_color_escape": h(p["mauve"]),
        "fish_color_autosuggestion": h(p["overlay0"]), "fish_color_cancel": h(p["red"]),
        "fish_color_valid_path": "--underline", "fish_color_cwd": h(t.primary),
        "fish_color_user": h(t.tertiary), "fish_color_host": h(t.secondary),
        "fish_color_selection": f"--background={h(p['surface1'])}",
        "fish_color_search_match": f"--background={h(p['surface1'])}",
        "fish_pager_color_prefix": h(t.primary), "fish_pager_color_completion": h(p["text"]),
        "fish_pager_color_description": h(p["overlay1"]), "fish_pager_color_progress": h(p["overlay1"]),
        "fish_pager_color_selected_background": f"--background={h(p['surface1'])}",
    }
    body = "\n".join(f"set -g {k} {val}" for k, val in v.items())
    write(CFG / "fish/conf.d/rice-theme.fish", f"# Сгенерировано rice.py — {t.raw['name']}\n{body}\n")


# ---------------------------------------------------------------- обои
def wallpaper_tool():
    for tool in ("awww", "swww"):
        if shutil.which(tool):
            return tool
    return None


def apply_wallpaper(t, transition="fade"):
    tool = wallpaper_tool()
    if not tool or DRY:
        return
    r = run(tool, "query")
    if r is None or r.returncode != 0:
        run(f"{tool}-daemon", bg=True)
        import time
        for _ in range(30):
            time.sleep(0.15)
            r = run(tool, "query")
            if r and r.returncode == 0:
                break
    if transition == "none":
        run(tool, "img", str(t.wallpaper), "--transition-type", "none")
    else:
        run(tool, "img", str(t.wallpaper), "--transition-type", "fade",
            "--transition-duration", "0.6", "--transition-fps", "60")


# ---------------------------------------------------------------- SDDM (экран входа)
def apply_sddm(t):
    """Пишет переопределение темы sddm-astronaut в /var/lib/rice (один раз настраивается sddm-setup.sh)."""
    if not (SDDM_DIR.is_dir() and os.access(SDDM_DIR, os.W_OK)):
        return "пропущено (запусти sddm-setup.sh один раз)"
    p, P = t.p, t.primary
    conf = {
        "Background": "Backgrounds/rice.png", "DimBackground": "0.0",
        "HeaderTextColor": p["subtext1"], "DateTextColor": p["subtext1"], "TimeTextColor": p["text"],
        "FormBackgroundColor": p["crust"], "BackgroundColor": p["base"], "DimBackgroundColor": p["crust"],
        "LoginFieldBackgroundColor": p["surface0"], "PasswordFieldBackgroundColor": p["surface0"],
        "LoginFieldTextColor": p["text"], "PasswordFieldTextColor": p["text"],
        "UserIconColor": P, "PasswordIconColor": P,
        "PlaceholderTextColor": p["overlay1"], "WarningColor": p["red"],
        "LoginButtonTextColor": p["crust"], "LoginButtonBackgroundColor": P,
        "SystemButtonsIconsColor": p["subtext1"], "SessionButtonTextColor": p["subtext1"],
        "VirtualKeyboardButtonTextColor": p["subtext1"],
        "DropdownTextColor": p["text"], "DropdownSelectedBackgroundColor": p["surface1"],
        "DropdownBackgroundColor": p["mantle"],
        "HighlightTextColor": p["crust"], "HighlightBackgroundColor": P, "HighlightBorderColor": t.secondary,
        "HoverUserIconColor": t.secondary, "HoverPasswordIconColor": t.secondary,
        "HoverSystemButtonsIconsColor": P, "HoverSessionButtonTextColor": P,
        "HoverVirtualKeyboardButtonTextColor": P,
    }
    text = f"# Сгенерировано rice.py — {t.raw['name']}\n[General]\n" + "".join(f'{k}="{v}"\n' for k, v in conf.items())
    write(SDDM_DIR / "sddm.conf.user", text)
    shutil.copyfile(t.wallpaper, SDDM_DIR / "sddm-bg.png.tmp")
    os.replace(SDDM_DIR / "sddm-bg.png.tmp", SDDM_DIR / "sddm-bg.png")
    return "ok"


# ---------------------------------------------------------------- main
STEPS = [
    ("Hyprland", apply_hyprland), ("HyprPanel", apply_hyprpanel), ("Kitty", apply_kitty),
    ("Rofi", apply_rofi), ("Qt/KDE", apply_kde), ("GTK", apply_gtk), ("Fish", apply_fish),
    ("Обои", apply_wallpaper), ("SDDM", apply_sddm),
]


def apply(name):
    t = Theme(name)
    print(f"Тема: {t.raw['name']} — {t.raw['description']}")
    for label, fn in STEPS:
        try:
            res = fn(t)
            print(f"  ✓ {label}" + (f": {res}" if isinstance(res, str) and res != "ok" else ""))
        except Exception as e:
            print(f"  ✗ {label}: {e}")
    write(STATE, name + "\n")
    run("notify-send", "-a", "rice", "Тема применена", t.raw["name"])


def current():
    return STATE.read_text().strip() if STATE.exists() else None


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "list"
    if cmd == "list":
        cur = current()
        for n in list_themes():
            d = json.loads((RICE_DIR / "themes" / f"{n}.json").read_text())
            print(f"{'*' if n == cur else ' '} {n:8} {d['description']}")
    elif cmd == "current":
        print(current() or "")
    elif cmd == "apply" and len(argv) > 2:
        apply(argv[2])
    elif cmd in ("next", "prev", "random"):
        name = current()
        if not name:
            return 1
        t = Theme(name)
        n = len(t.wallpapers)
        i = wp_index(name)
        if cmd == "next":
            i = (i + 1) % n
        elif cmd == "prev":
            i = (i - 1) % n
        else:
            import random
            i = random.choice([k for k in range(n) if k != i] or [0])
        wp_index(name, i)
        t = Theme(name)
        apply_wallpaper(t)
        apply_sddm(t)
        print(f"{t.raw['name']}: обои {i + 1}/{n} — {t.wallpaper.name}")
    elif cmd == "wallpaper":
        if current():
            apply_wallpaper(Theme(current()), transition="none")  # при входе — без анимации
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
