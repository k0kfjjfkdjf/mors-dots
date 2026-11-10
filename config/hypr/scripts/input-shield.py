#!/usr/bin/env python3
"""Щит: невидимый слой поверх всех мониторов, кроме монитора с игрой.

Пока окно в полном экране Super+F, курсор ещё может на миг заехать на соседний монитор.
Щит лежит поверх всего (даже панели), прозрачный и ловит клики — они никуда не уходят,
фокус остаётся у игры. Курсор над щитом — «запрещено».

    input-shield.py <монитор-с-игрой>     закрыть щитом все остальные мониторы
    pkill -f '[i]nput-shield.py'          убрать (так делает lua/pointer_lock.lua)

Нужен gtk-layer-shell (GTK3).
"""
import json
import subprocess
import sys

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
try:
    gi.require_version('GtkLayerShell', '0.1')
    from gi.repository import GtkLayerShell
except (ValueError, ImportError):
    sys.exit('input-shield: нет gtk-layer-shell — sudo pacman -S gtk-layer-shell')
from gi.repository import Gdk, Gtk  # noqa: E402

NAMESPACE = 'mors-input-shield'


def hypr_monitors():
    try:
        out = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True, timeout=5).stdout
        return [m for m in json.loads(out) if not m.get('disabled')]
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []


def shield_window(gdk_mon):
    w = Gtk.Window()
    w.set_app_paintable(True)                      # фон не рисуем — окно прозрачное
    visual = w.get_screen().get_rgba_visual()
    if visual:
        w.set_visual(visual)
    GtkLayerShell.init_for_window(w)
    GtkLayerShell.set_namespace(w, NAMESPACE)
    GtkLayerShell.set_layer(w, GtkLayerShell.Layer.OVERLAY)
    for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT, GtkLayerShell.Edge.RIGHT):
        GtkLayerShell.set_anchor(w, edge, True)
    GtkLayerShell.set_exclusive_zone(w, -1)        # поверх панелей, ничего не сдвигает
    if hasattr(GtkLayerShell, 'set_keyboard_mode'):
        GtkLayerShell.set_keyboard_mode(w, GtkLayerShell.KeyboardMode.NONE)
    else:
        GtkLayerShell.set_keyboard_interactivity(w, False)
    GtkLayerShell.set_monitor(w, gdk_mon)

    def on_realize(win):
        cur = Gdk.Cursor.new_from_name(win.get_display(), 'not-allowed')
        if cur:
            win.get_window().set_cursor(cur)
    w.connect('realize', on_realize)
    w.show_all()
    return w


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    keep = sys.argv[1]
    if not GtkLayerShell.is_supported():
        sys.exit('input-shield: композитор не поддерживает layer-shell')
    display = Gdk.Display.get_default()
    gdk_mons = [display.get_monitor(i) for i in range(display.get_n_monitors())]
    by_pos = {(g.get_geometry().x, g.get_geometry().y): g for g in gdk_mons}
    windows = []
    for m in hypr_monitors():
        if m.get('name') == keep:
            continue
        g = by_pos.get((m.get('x'), m.get('y')))   # мониторы GTK и Hyprland совпадают по позиции
        if g:
            windows.append(shield_window(g))
    if not windows:
        return 0                                   # один монитор — закрывать нечего
    Gtk.main()
    return 0


if __name__ == '__main__':
    sys.exit(main())
