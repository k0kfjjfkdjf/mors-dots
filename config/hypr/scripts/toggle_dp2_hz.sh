#!/usr/bin/env python3
import gi
import subprocess
import re
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# ------------------------------------------------------------
# 1. Находим монитор по описанию (разъём DP-2 может смениться), берём его текущие
#    разрешение, частоту, позицию, масштаб и поворот — их и сохраняем
# ------------------------------------------------------------
import json, os
MON_DESC = "MKG MKF23F180 H80297Q8NSCQL"
MON = "desc:" + MON_DESC
mons = json.loads(subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True).stdout or "[]")
m = next((x for x in mons if x.get("description", "").startswith(MON_DESC)), None)
if not m:
    print("Монитор MKG не найден")
    sys.exit(1)

resolution = f"{m['width']}x{m['height']}"
current_hz = str(round(m["refreshRate"]))
position = f"{m['x']}x{m['y']}"
scale = m.get("scale", 1)
transform = m.get("transform", 0)

# ------------------------------------------------------------
# 2. Переключаем 60 ↔ 180
# ------------------------------------------------------------
new_hz = "60" if current_hz == "180" else "180"

# ------------------------------------------------------------
# 3. Применяем; метка прогрева — чтобы hyprctl reload не менял частоту обратно
# ------------------------------------------------------------
lua = (f'hl.monitor({{ output = "{MON}", mode = "{resolution}@{new_hz}", '
       f'position = "{position}", scale = {scale}' + (f', transform = {transform}' if transform else '') + ' })')
r = subprocess.run(["hyprctl", "eval", lua], capture_output=True, text=True)
if not r.stdout.strip().startswith("ok"):
    subprocess.run(["hyprctl", "keyword", "monitor",
                    f"{MON},{resolution}@{new_hz},{position},{scale}"])
flag = os.path.join(os.environ.get("XDG_RUNTIME_DIR", "/tmp"), "hypr",
                    os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", ""), "mors-warm-done")
try:
    if new_hz == "180":
        open(flag, "a").close()
    elif os.path.exists(flag):
        os.remove(flag)
except OSError:
    pass

# ------------------------------------------------------------
# 4. Показываем уведомление (GTK окно)
# ------------------------------------------------------------
win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
win.set_default_size(300, 80)
win.set_decorated(False)
win.set_keep_above(True)
win.set_app_paintable(True)
win.set_resizable(False)

screen = win.get_screen()
visual = screen.get_rgba_visual()
if visual:
    win.set_visual(visual)

def draw_bg(widget, cr):
    cr.set_source_rgba(0.13, 0.13, 0.13, 0.80)
    cr.paint()
    return False

win.connect("draw", draw_bg)

css = b"""
window {
  border-radius: 12px;
  border: 2px solid #555555;
}
label {
  color: white;
  font-weight: bold;
  font-size: 18px;
}
"""
style_provider = Gtk.CssProvider()
style_provider.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(
    screen,
    style_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

label = Gtk.Label(label=f"{m['name']}: {resolution} @ {new_hz} Hz")
label.set_justify(Gtk.Justification.CENTER)
label.set_halign(Gtk.Align.CENTER)
label.set_valign(Gtk.Align.CENTER)
win.add(label)

# Центрируем окно по центру монитора
# Можно также вычислить позицию из данных монитора, но для простоты оставим как было
win.move(m["x"] + int(m["width"] / scale) // 2 - 150, m["y"] + int(m["height"] / scale) // 2 - 40)

win.show_all()

GLib.timeout_add(3000, Gtk.main_quit)
Gtk.main()
