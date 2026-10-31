#!/usr/bin/env python3
import gi
import subprocess
import re
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# ------------------------------------------------------------
# 1. Находим монитор MKG по описанию (разъём DP-2 может смениться)
# ------------------------------------------------------------
import json
MON_DESC = "MKG MKF23F180 H80297Q8NSCQL"
mons = json.loads(subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True).stdout or "[]")
m = next((x for x in mons if x.get("description", "").startswith(MON_DESC)), None)
if not m:
    print("Монитор MKG не найден", file=sys.stderr)
    sys.exit(1)

resolution = f"{m['width']}x{m['height']}"
current_hz = str(round(m["refreshRate"]))
scale = m.get("scale", 1) or 1

# ------------------------------------------------------------
# 2. Создаём уведомление
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
    cr.set_source_rgba(0.13, 0.13, 0.13, 0.80)  # полупрозрачный тёмный фон
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

label = Gtk.Label(label=f"{m['name']}: {resolution} @ {current_hz} Hz")
label.set_justify(Gtk.Justification.CENTER)
label.set_halign(Gtk.Align.CENTER)
label.set_valign(Gtk.Align.CENTER)
win.add(label)

# ------------------------------------------------------------
# 3. Центрируем окно по центру монитора
#    (можно вычислить динамически, но для простоты оставим фиксированные координаты)
# ------------------------------------------------------------
# Позиция и размер — из hyprctl monitors -j
win.move(m["x"] + int(m["width"] / scale) // 2 - 150, m["y"] + int(m["height"] / scale) // 2 - 40)

win.show_all()

# Закрываем через 3 секунды
GLib.timeout_add(3000, Gtk.main_quit)
Gtk.main()
