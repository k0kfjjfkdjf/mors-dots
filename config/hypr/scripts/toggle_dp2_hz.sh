#!/usr/bin/env python3
import gi
import subprocess
import re
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

# ------------------------------------------------------------
# 1. Получаем информацию о мониторе DP-2 через hyprctl
# ------------------------------------------------------------
result = subprocess.run(
    ["hyprctl", "monitors"],
    capture_output=True,
    text=True
)
output = result.stdout

# Регулярное выражение для поиска блока DP-2
# Пример строки: "Monitor DP-2 (ID 0): 1920x1080@180.000 at 1280x0"
pattern = r"Monitor\s+DP-2.*?:\s*(\d+x\d+)@(\d+)"
match = re.search(pattern, output)

if not match:
    print("Монитор DP-2 не найден")
    sys.exit(1)

resolution = match.group(1)   # например "1920x1080"
current_hz = match.group(2)    # например "180"

# ------------------------------------------------------------
# 2. Определяем новую частоту (переключаем между 60 и 180)
# ------------------------------------------------------------
if current_hz == "180":
    new_hz = "60"
else:
    new_hz = "180"

# Позиция и масштаб остаются без изменений (берём из вывода, но можно и жёстко)
# Для простоты оставим фиксированными, как в исходном скрипте
position = "1280x0"
scale = "1"

# ------------------------------------------------------------
# 3. Применяем новую конфигурацию монитора
# ------------------------------------------------------------
# Lua-конфиг (Hyprland 0.55+) понимает только eval, старый .conf — только keyword
MON = "desc:MKG MKF23F180 H80297Q8NSCQL"
lua = (f'hl.monitor({{ output = "{MON}", mode = "{resolution}@{new_hz}", '
       f'position = "{position}", scale = {scale} }})')
r = subprocess.run(["hyprctl", "eval", lua], capture_output=True, text=True)
if not r.stdout.strip().startswith("ok"):
    subprocess.run(["hyprctl", "keyword", "monitor",
                    f"{MON},{resolution}@{new_hz},{position},{scale}"])

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

label = Gtk.Label(label=f"DP-2: {resolution} @ {new_hz} Hz")
label.set_justify(Gtk.Justification.CENTER)
label.set_halign(Gtk.Align.CENTER)
label.set_valign(Gtk.Align.CENTER)
win.add(label)

# Центрируем окно примерно по центру DP-2
# Можно также вычислить позицию из данных монитора, но для простоты оставим как было
win.move(1280 + 1920//2 - 150, 0 + 1080//2 - 40)

win.show_all()

GLib.timeout_add(3000, Gtk.main_quit)
Gtk.main()
