#!/usr/bin/env python3
"""rice — переключатель тем для Hyprland-райса.

    rice.py list              — список тем
    rice.py current           — текущая тема
    rice.py apply <тема>      — применить тему ко всей системе
    rice.py wallpaper         — заново поставить обои текущей темы (для автозапуска)
    rice.py next|prev|random  — следующие / предыдущие / случайные обои в текущей теме
    rice.py wallpapers [тема] — какие обои нашлись у темы (и где её папка)
    rice.py set-wallpaper <файл> — поставить конкретные обои текущей темы
    rice.py monitors          — мониторы и какие обои на каждом
    rice.py monitor-wallpaper <монитор> <файл> [x y w h] [--rotate 90] [--flip]
                              — свои обои на один монитор (x y w h — кадр в долях картинки 0…1,
                              поворот по часовой, отражение; «-» вместо файла — как у всех)

Обои: у каждой темы своя папка wallpapers/<тема>/ — всё, что там лежит (png, jpg, webp,
gif…, в том числе в подпапках), подхватывается само; прописывать пути не нужно.
Сгенерированные обои темы — default.png, идут последними. Папка для новой темы
создаётся автоматически. Личные картинки в git не попадают.

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
        self.wallpapers = theme_wallpapers(name)
        self.wallpaper = selected_wallpaper(name, self.wallpapers)   # None, если папка пуста

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


# ---------------------------------------------------------------- поиск обоев
WP_DIR = RICE_DIR / "wallpapers"
WP_STATE = RICE_DIR / "wallpaper-index.json"
WP_DEFAULT = "default.png"                     # сгенерированные обои темы (gen_wallpapers.py)
WP_EXT = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}


def _natural(p):
    import re
    return [int(x) if x.isdigit() else x.lower() for x in re.split(r"(\d+)", str(p))]


def migrate_wallpapers():
    """Старая раскладка → папки тем. Безопасно запускать сколько угодно раз.
    wallpapers/<тема>.png → wallpapers/<тема>/default.png;
    wallpapers/local/<тема>-что-угодно.* → wallpapers/<тема>/."""
    themes = list_themes()
    for t in themes:
        (WP_DIR / t).mkdir(parents=True, exist_ok=True)
        old = WP_DIR / f"{t}.png"
        if old.is_file() and not (WP_DIR / t / WP_DEFAULT).exists():
            old.replace(WP_DIR / t / WP_DEFAULT)
    local = WP_DIR / "local"
    if local.is_dir():
        for f in local.iterdir():
            if not f.is_file() or f.suffix.lower() not in WP_EXT:
                continue
            owner = next((t for t in themes if f.name.lower().startswith((t + "-", t + "_", t + "."))), None)
            if owner and not (WP_DIR / owner / f.name).exists():
                f.replace(WP_DIR / owner / f.name)


def theme_wallpapers(name):
    """Все картинки из папки темы: свои — по имени, default.png — в конце."""
    migrate_wallpapers()
    d = WP_DIR / name
    d.mkdir(parents=True, exist_ok=True)
    files = [f for f in d.rglob("*")
             if f.is_file() and f.suffix.lower() in WP_EXT
             and not any(part.startswith(".") for part in f.relative_to(d).parts)]
    own = sorted((f for f in files if f.name != WP_DEFAULT), key=lambda f: _natural(f.relative_to(d)))
    return own + [f for f in files if f.name == WP_DEFAULT]


def _wp_state():
    try:
        return json.loads(WP_STATE.read_text())
    except Exception:
        return {}


def selected_wallpaper(theme, files):
    """Какие обои выбраны в теме — запоминается имя файла, отдельно для каждой темы."""
    if not files:
        return None
    v = _wp_state().get(theme, 0)
    if isinstance(v, str):
        for f in files:
            if str(f.relative_to(WP_DIR / theme)) == v:
                return f
        v = 0
    return files[int(v) % len(files)]


# ---------------------------------------------------------------- обои по мониторам
MON_STATE = RICE_DIR / "monitor-wallpapers.json"          # машинное (у каждого компьютера свои), не в git
MON_CACHE = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "rice/monitors"


def monitors():
    """Подключённые мониторы: имя выхода, EDID-описание (ключ — не зависит от разъёма),
    разрешение в пикселях с учётом поворота, положение. RICE_MONITORS — JSON для тестов."""
    raw = os.environ.get("RICE_MONITORS")
    if raw is None:
        if not shutil.which("hyprctl"):
            return []
        try:
            raw = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, timeout=5).stdout
        except Exception:
            return []
    try:
        data = json.loads(raw)
    except Exception:
        return []
    out = []
    for m in data:
        w, h = int(m.get("width", 0)), int(m.get("height", 0))
        if int(m.get("transform", 0)) % 2:                  # повёрнут на 90/270°
            w, h = h, w
        scale = float(m.get("scale", 1) or 1)
        desc = (m.get("description") or "").strip()
        out.append({"name": m.get("name", ""), "key": desc or m.get("name", ""), "desc": desc,
                    "w": w, "h": h, "x": int(m.get("x", 0)), "y": int(m.get("y", 0)), "scale": scale})
    return out


def find_monitor(query, mons=None):
    mons = mons if mons is not None else monitors()
    q = query.lower().removeprefix("desc:")
    return next((m for m in mons if q in (m["name"].lower(), m["key"].lower())), None) \
        or next((m for m in mons if q in m["key"].lower()), None)


def mon_state():
    try:
        return json.loads(MON_STATE.read_text())
    except Exception:
        return {}


def set_monitor_wallpaper(theme, key, rel=None, crop=None, rotate=0, flip=False):
    """rel=None — монитор снова «как у всех». crop — [x, y, w, h] в долях картинки
    (уже повёрнутой). rotate — поворот по часовой 0/90/180/270, flip — отразить по горизонтали."""
    d = mon_state()
    per = d.setdefault(theme, {})
    if rel is None:
        per.pop(key, None)
    else:
        if crop is not None:
            x, y, w, h = (min(max(float(v), 0.0), 1.0) for v in crop)
            crop = [round(x, 5), round(y, 5), round(max(w, 0.01), 5), round(max(h, 0.01), 5)]
        per[key] = {"file": rel, "crop": crop}
        if int(rotate) % 360:
            per[key]["rotate"] = int(rotate) % 360
        if flip:
            per[key]["flip"] = True
    if not per:
        d.pop(theme, None)
    write(MON_STATE, json.dumps(d, ensure_ascii=False, indent=2))


def render_for_monitor(theme, mon, entry):
    """Картинка для монитора: вырезает кадр и масштабирует ровно под его пиксели.
    Без кадра, для gif или без GdkPixbuf — исходный файл (awww сам обрежет по центру)."""
    src = WP_DIR / theme / entry["file"]
    if not src.is_file():
        return None
    crop = entry.get("crop")
    rot, flip = int(entry.get("rotate", 0)) % 360, bool(entry.get("flip"))
    if src.suffix.lower() == ".gif" or not (mon["w"] and mon["h"]) or not (crop or rot or flip):
        return src
    out = MON_CACHE / theme / ("".join(c if c.isalnum() else "_" for c in mon["key"])[:80] + ".png")
    sig = f"{src}|{src.stat().st_mtime_ns}|{crop}|{rot}|{flip}|{mon['w']}x{mon['h']}"
    sigf = out.with_suffix(".sig")
    if out.exists() and sigf.exists() and sigf.read_text() == sig:
        return out
    try:
        import gi
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf
        pb = GdkPixbuf.Pixbuf.new_from_file(str(src))
        if rot:          # сначала поворот по часовой, потом отражение — так же делает конфигуратор
            pb = pb.rotate_simple({90: GdkPixbuf.PixbufRotation.CLOCKWISE,
                                   180: GdkPixbuf.PixbufRotation.UPSIDEDOWN,
                                   270: GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE}[rot])
        if flip:
            pb = pb.flip(True)
        if not crop:     # без кадра — заполнить экран по центру
            a, A = pb.get_width() / pb.get_height(), mon["w"] / mon["h"]
            crop = [(1 - A / a) / 2, 0, A / a, 1] if a > A else [0, (1 - a / A) / 2, 1, a / A]
        W, H = pb.get_width(), pb.get_height()
        x, y = int(crop[0] * W), int(crop[1] * H)
        w, h = max(1, min(int(crop[2] * W), W - x)), max(1, min(int(crop[3] * H), H - y))
        sub = pb.new_subpixbuf(x, y, w, h).scale_simple(mon["w"], mon["h"], GdkPixbuf.InterpType.HYPER)
        out.parent.mkdir(parents=True, exist_ok=True)
        sub.savev(str(out), "png", [], [])
        sigf.write_text(sig)
        return out
    except Exception as e:
        print(f"  ! не вырезал кадр для {mon['name']}: {e} — ставлю картинку целиком", file=sys.stderr)
        return src


def select_wallpaper(theme, f):
    d = _wp_state()
    d[theme] = str(Path(f).relative_to(WP_DIR / theme))
    write(WP_STATE, json.dumps(d, ensure_ascii=False))


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
    groupbar_text_inactive = "{rgba(t.text)}",
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
    cfg["wallpaper.image"] = str(t.wallpaper or "")
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
    if not t.wallpaper:
        return f"нет картинок — положи их в {WP_DIR / t.id}"
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
    trans = (["--transition-type", "none"] if transition == "none" else
             ["--transition-type", "fade", "--transition-duration", "0.6", "--transition-fps", "60"])
    per = mon_state().get(t.id, {})
    mons = monitors() if per else []
    if not mons:
        run(tool, "img", str(t.wallpaper), *trans)
        return
    rest = []
    for m in mons:                                   # свои обои — на свой монитор, остальным — общие
        img = render_for_monitor(t.id, m, per[m["key"]]) if m["key"] in per else None
        if img:
            run(tool, "img", "-o", m["name"], str(img), *trans)
        else:
            rest.append(m["name"])
    if rest:
        run(tool, "img", "-o", ",".join(rest), str(t.wallpaper), *trans)


# ---------------------------------------------------------------- экран входа и блокировки: свои настройки
# rice/login.json (у каждой машины свой, не в git) — пишет mors-settings, «Система → Экран входа и блокировки»:
#   image  — "theme" (обои темы) или путь к своей картинке, общая для входа и блокировки
#   sddm   — ключи темы sddm-astronaut поверх цветов темы (FormPosition, Blur, DimBackground…)
#   lock   — экран блокировки hyprlock: image (login | theme | screenshot), blur, brightness, clock, date
LOGIN_FILE = RICE_DIR / "login.json"
SDDM_RU = {     # подписи экрана входа по-русски (тема sddm-astronaut их переводит этими ключами)
    "TranslatePlaceholderUsername": "Имя пользователя", "TranslatePlaceholderPassword": "Пароль",
    "TranslateLogin": "Войти", "TranslateLoginFailedWarning": "Неверный пароль",
    "TranslateCapslockWarning": "Включён Caps Lock", "TranslateSuspend": "Сон", "TranslateHibernate": "Гибернация",
    "TranslateReboot": "Перезагрузка", "TranslateShutdown": "Выключение", "TranslateSessionSelection": "Сеанс",
    "TranslateVirtualKeyboardButtonOn": "Экранная клавиатура", "TranslateVirtualKeyboardButtonOff": "Скрыть клавиатуру",
}
SDDM_KEYS = {   # что можно переопределить — и только это (остальное у темы rice)
    "FormPosition", "Blur", "BlurMax", "PartialBlur", "FullBlur", "DimBackground", "HaveFormBackground",
    "CropBackground", "BackgroundHorizontalAlignment", "BackgroundVerticalAlignment", "HourFormat", "DateFormat",
    "HeaderText", "HideVirtualKeyboard", "VirtualKeyboardPosition", "HideSystemButtons", "HideLoginButton",
    "RoundCorners", "ScreenPadding", "Font", "FontSize", "ForceLastUser", "UseRealName", "PasswordFocus",
    "HideCompletePassword", *SDDM_RU,
}
LOCK_DEFAULTS = {"image": "login", "blur": 2, "brightness": 0.75, "clock": True, "date": True, "font": "Sans",
                 "layout": "center", "clockSize": 84, "clockFormat": "24", "dateFormat": "long", "greeting": "",
                 "avatar": "", "inputWidth": 320, "placeholder": "Пароль…", "showLayout": True,
                 "fingerprint": False, "animations": True}


def login_settings():
    try:
        d = json.loads(LOGIN_FILE.read_text())
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def login_image(t):
    """Картинка экрана входа: своя из login.json (если файл на месте) или обои темы."""
    img = login_settings().get("image") or "theme"
    if img != "theme":
        f = Path(os.path.expanduser(img))
        if f.is_file():
            return f
    return t.wallpaper


def save_png(src, dst):
    """Копия картинки в PNG: тема SDDM ждёт файл rice.png, а Qt по расширению выбирает декодер."""
    tmp = dst.with_name(dst.name + ".tmp")
    if src.suffix.lower() == ".png":
        shutil.copyfile(src, tmp)
    else:
        try:
            import gi
            gi.require_version("GdkPixbuf", "2.0")
            from gi.repository import GdkPixbuf
            GdkPixbuf.Pixbuf.new_from_file(str(src)).savev(str(tmp), "png", [], [])
        except Exception:
            shutil.copyfile(src, tmp)            # без GdkPixbuf — как есть, Qt обычно угадывает формат по содержимому
    os.replace(tmp, dst)


# ---------------------------------------------------------------- SDDM (экран входа)
def apply_sddm(t):
    """Пишет переопределение темы sddm-astronaut в /var/lib/rice (один раз настраивается sddm-setup.sh)."""
    if not (SDDM_DIR.is_dir() and os.access(SDDM_DIR, os.W_OK)):
        return "пропущено (запусти sddm-setup.sh один раз)"
    if not t.wallpaper:
        return "нет обоев у темы"
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
    ls = login_settings()
    if ls.get("russian", True):
        conf.update(SDDM_RU)
    user = ls.get("sddm") or {}
    conf.update({k: str(v).replace('"', "'").replace("\n", " ") for k, v in user.items() if k in SDDM_KEYS})
    text = f"# Сгенерировано rice.py — {t.raw['name']}\n[General]\n" + "".join(f'{k}="{v}"\n' for k, v in conf.items())
    write(SDDM_DIR / "sddm.conf.user", text)
    save_png(login_image(t), SDDM_DIR / "sddm-bg.png")
    return "ok"


# ---------------------------------------------------------------- экран блокировки (hyprlock)
def hl_color(h, alpha=None):
    h = h.lstrip("#")[:6]
    return f"rgba({h}{alpha:02x})" if alpha is not None else f"rgb({h})"


def apply_hyprlock(t):
    """~/.config/hypr/hyprlock.conf в цветах темы. Без этого файла hyprlock не запускается вовсе —
    и блокировка по простою (hypridle) ничего бы не делала. Элементы ставятся столбиком сами:
    раскладка center / left / bottom, лишнее (аватар, приветствие, дата…) просто выпадает."""
    p, P = t.p, t.primary
    L = {**LOCK_DEFAULTS, **(login_settings().get("lock") or {})}
    clean = lambda v: str(v).replace("\n", " ").strip()
    if L["image"] == "screenshot":
        bg = "screenshot"
    else:
        img = t.wallpaper if L["image"] == "theme" else login_image(t)
        bg = str(img) if img else ""
    blur = max(0, min(4, int(L.get("blur") or 0)))
    bright = max(0.2, min(1.0, float(L.get("brightness") or 1)))
    font = clean(L.get("font") or "Sans")
    csize = max(32, min(180, int(L.get("clockSize") or 84)))
    iw = max(200, min(560, int(L.get("inputWidth") or 320)))
    out = [f"# Сгенерировано rice.py — {t.raw['name']}. Вид меняется в mors-settings → Система → Экран входа и блокировки.",
           "general {", "    hide_cursor = true", "    ignore_empty_input = true", "}",
           "animations {", f"    enabled = {'true' if L.get('animations', True) else 'false'}", "}"]
    if L.get("fingerprint"):
        out += ["auth {", "    fingerprint {", "        enabled = true",
                "        ready_message = Приложи палец или введи пароль", "        present_message = Сканирую отпечаток…", "    }", "}"]
    out += ["", "background {", "    monitor =", f"    path = {bg}", f"    color = {hl_color(p['base'])}",
            f"    blur_passes = {blur}", "    blur_size = 7", f"    brightness = {bright:.2f}", "}"]
    # элементы сверху вниз: (высота, строки виджета без position/halign/valign)
    items = []
    av = clean(L.get("avatar") or "")
    if av:
        avp = Path(os.path.expanduser(av))
        if avp.is_file():
            items.append((126, ["image {", "    monitor =", f"    path = {avp}", "    size = 110", "    rounding = -1",
                                "    border_size = 3", f"    border_color = {hl_color(P)} {hl_color(t.secondary)} 45deg"]))
    g = L.get("greeting") or ""
    if g:
        text = "Привет, $USER" if g == "user" else clean(g)
        items.append((40, ["label {", "    monitor =", f"    text = {text}", "    font_size = 18", f"    font_family = {font}",
                           f"    color = {hl_color(p['subtext1'])}"]))
    if L.get("clock", True):
        fmt = {"24": "$TIME", "12": "$TIME12", "24s": 'cmd[update:1000] date +"%H:%M:%S"'}.get(L.get("clockFormat"), "$TIME")
        items.append((int(csize * 1.3), ["label {", "    monitor =", f"    text = {fmt}", f"    font_size = {csize}",
                                         f"    font_family = {font}", f"    color = {hl_color(p['text'])}"]))
    if L.get("date", True):
        df = {"long": "%A, %-d %B", "full": "%A, %-d %B %Y", "short": "%d.%m.%Y"}.get(L.get("dateFormat"), "%A, %-d %B")
        items.append((40, ["label {", "    monitor =", f'    text = cmd[update:60000] LC_TIME=ru_RU.UTF-8 date +"{df}"',
                           "    font_size = 20", f"    font_family = {font}", f"    color = {hl_color(p['subtext1'])}"]))
    items.append((54 + 26, ["input-field {", "    monitor =", f"    size = {iw}, 54", "    outline_thickness = 2", "    rounding = 14",
                            f"    outer_color = {hl_color(P)} {hl_color(t.secondary)} 45deg",
                            f"    inner_color = {hl_color(p['crust'], 0xcc)}", f"    font_color = {hl_color(p['text'])}",
                            f"    check_color = {hl_color(t.secondary)}", f"    fail_color = {hl_color(p['red'])}",
                            f"    capslock_color = {hl_color(p.get('yellow', P))}", f"    font_family = {font}",
                            f"    placeholder_text = <i>{clean(L.get('placeholder') or 'Пароль…')}</i>",
                            "    fail_text = <i>$PAMFAIL</i>", "    fade_on_empty = false", "    dots_spacing = 0.3"]))
    if L.get("showLayout", True):
        items.append((30, ["label {", "    monitor =", "    text = $LAYOUT[en,ru]", "    font_size = 14", f"    font_family = {font}",
                           f"    color = {hl_color(p['overlay1'])}"]))
    lay = L.get("layout") if L.get("layout") in ("center", "left", "bottom") else "center"
    total = sum(h for h, _ in items)
    if lay == "bottom":                  # столбик у нижнего края: y — от низа экрана
        y = 70
        placed = []
        for h, w in reversed(items):
            placed.append((w, f"0, {y}", "center", "bottom")); y += h
        placed.reverse()
    else:                                # по центру экрана (left — тот же столбик у левого края)
        top = total / 2
        placed = []
        for h, w in items:
            cy = round(top - h / 2); top -= h
            placed.append((w, f"{'140' if lay == 'left' else '0'}, {cy}", "left" if lay == "left" else "center", "center"))
    for w, pos, ha, va in placed:
        out += [""] + w + [f"    position = {pos}", f"    halign = {ha}", f"    valign = {va}", "}"]
    write(CFG / "hypr/hyprlock.conf", "\n".join(out) + "\n")
    return "ok" if bg else "нет обоев у темы — фон будет цветом"


# ---------------------------------------------------------------- main
STEPS = [
    ("Hyprland", apply_hyprland), ("HyprPanel", apply_hyprpanel), ("Kitty", apply_kitty),
    ("Rofi", apply_rofi), ("Qt/KDE", apply_kde), ("GTK", apply_gtk), ("Fish", apply_fish),
    ("Обои", apply_wallpaper), ("SDDM", apply_sddm), ("Блокировка", apply_hyprlock),
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
    # не ждём ответа: служба уведомлений (HyprPanel) в этот момент сама перекрашивается
    run("notify-send", "-a", "rice", "Тема применена", t.raw["name"], bg=True)


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
        if not n:
            print(f"У темы нет обоев — положи картинки в {WP_DIR / name}")
            return 1
        i = t.wallpapers.index(t.wallpaper)
        if cmd == "next":
            i = (i + 1) % n
        elif cmd == "prev":
            i = (i - 1) % n
        else:
            import random
            i = random.choice([k for k in range(n) if k != i] or [0])
        select_wallpaper(name, t.wallpapers[i])
        t = Theme(name)
        apply_wallpaper(t)
        apply_sddm(t)
        apply_hyprlock(t)
        print(f"{t.raw['name']}: обои {i + 1}/{n} — {t.wallpaper.name}")
    elif cmd == "wallpapers":
        name = argv[2] if len(argv) > 2 else current()
        if not name:
            return 1
        t = Theme(name)
        print(f"{t.raw['name']}: {WP_DIR / name}")
        for f in t.wallpapers:
            print(f"{'*' if f == t.wallpaper else ' '} {f.relative_to(WP_DIR / name)}")
        if not t.wallpapers:
            print("  (пусто — положи сюда картинки)")
        left = [f.name for f in (WP_DIR / "local").glob("*") if f.suffix.lower() in WP_EXT] if (WP_DIR / "local").is_dir() else []
        if left:
            print(f"В {WP_DIR / 'local'} остались картинки без темы: {', '.join(left)} — перенеси их в папку нужной темы")
    elif cmd == "set-wallpaper" and len(argv) > 2:
        name = current()
        if not name:
            return 1
        t = Theme(name)
        want = argv[2]
        f = next((f for f in t.wallpapers if want in (str(f), f.name, str(f.relative_to(WP_DIR / name)))), None)
        if not f:
            print(f"Нет такой картинки у темы {name}: {want}")
            return 1
        select_wallpaper(name, f)
        t = Theme(name)
        apply_wallpaper(t)
        apply_sddm(t)
        apply_hyprlock(t)
        print(f"{t.raw['name']}: {f.name}")
    elif cmd == "login":         # только экран входа и блокировки — после правки rice/login.json
        name = current()
        if not name:
            print("тема не выбрана"); return 1
        t = Theme(name)
        for label, fn in (("SDDM", apply_sddm), ("Блокировка", apply_hyprlock)):
            try:
                res = fn(t)
                print(f"  ✓ {label}" + (f": {res}" if isinstance(res, str) and res != "ok" else ""))
            except Exception as e:
                print(f"  ✗ {label}: {e}")
    elif cmd == "wallpaper":
        if current():   # при входе — без анимации; «rice.py wallpaper fade» — с ней
            apply_wallpaper(Theme(current()), transition="fade" if "fade" in argv[2:] else "none")
    elif cmd == "monitors":
        name = current()
        per = mon_state().get(name, {}) if name else {}
        for m in monitors():
            e = per.get(m["key"])
            print(f"{m['name']:10} {m['w']}x{m['h']}  {m['key']}\n           обои: "
                  + (f"{e['file']}" + (f" (кадр {e['crop']})" if e.get('crop') else "") if e else "как у всех"))
    elif cmd == "monitor-wallpaper" and len(argv) > 3:
        name = current()
        m = find_monitor(argv[2])
        if not name or not m:
            print(f"Нет монитора «{argv[2]}» — смотри rice.py monitors")
            return 1
        if argv[3] == "-":
            set_monitor_wallpaper(name, m["key"])
        else:
            t = Theme(name)
            f = next((f for f in t.wallpapers if argv[3] in (str(f), f.name, str(f.relative_to(WP_DIR / name)))), None)
            if not f:
                print(f"Нет такой картинки у темы {name}: {argv[3]}")
                return 1
            rest = argv[4:]
            rot = int(rest[rest.index("--rotate") + 1]) if "--rotate" in rest else 0
            flip = "--flip" in rest
            nums = [a for a in rest if a.replace(".", "", 1).isdigit()]
            nums = [n for n in nums if not ("--rotate" in rest and n == str(rot))]
            crop = [float(v) for v in nums[:4]] if len(nums) >= 4 else None
            set_monitor_wallpaper(name, m["key"], str(f.relative_to(WP_DIR / name)), crop, rot, flip)
        apply_wallpaper(Theme(name))
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
