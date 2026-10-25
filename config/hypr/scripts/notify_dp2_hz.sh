#!/usr/bin/env python3
import gi
import subprocess
import re
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# ------------------------------------------------------------
# 1. Получаем информацию о мониторе DP-2
# ------------------------------------------------------------
result = subprocess.run(
    ["hyprctl", "monitors"],
    capture_output=True,
    text=True
)
output = result.stdout

# Ищем строку с DP-2, захватываем разрешение и частоту
pattern = r"Monitor\s+DP-2.*?:\s*(\d+x\d+)@(\d+)"
match = re.search(pattern, output)

if not match:
    print("Монитор DP-2 не найден", file=sys.stderr)
    sys.exit(1)

resolution = match.group(1)   # например "1920x1080"
current_hz = match.group(2)    # например "180"

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

label = Gtk.Label(label=f"DP-2: {resolution} @ {current_hz} Hz")
label.set_justify(Gtk.Justification.CENTER)
label.set_halign(Gtk.Align.CENTER)
label.set_valign(Gtk.Align.CENTER)
win.add(label)

# ------------------------------------------------------------
# 3. Центрируем окно примерно по центру DP-2
#    (можно вычислить динамически, но для простоты оставим фиксированные координаты)
# ------------------------------------------------------------
# Позиция монитора из вашего monitors.conf: 1280x0, размер 1920x1080
win.move(1280 + 1920//2 - 150, 0 + 1080//2 - 40)

win.show_all()

# Закрываем через 3 секунды
GLib.timeout_add(3000, Gtk.main_quit)
Gtk.main()
