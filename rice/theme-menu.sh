#!/usr/bin/env bash
# Меню выбора темы (SUPER+SHIFT+T)
RICE="$HOME/.config/rice/rice.py"
choice=$(python3 "$RICE" list | sed 's/^\* /●  /; s/^  /   /' | rofi -dmenu -i -no-custom -p "Тема" \
    -theme-str 'window { location: center; anchor: center; width: 640px; height: 300px; }
                listview { lines: 3; }
                element-icon { enabled: false; }
                inputbar { children: [ "prompt", "entry" ]; }') || exit 0
name=$(sed 's/^[● ]*//' <<<"$choice" | awk '{print $1}')
[[ -n "$name" ]] && python3 "$RICE" apply "$name" >"${XDG_RUNTIME_DIR:-/tmp}/rice.log" 2>&1 &
