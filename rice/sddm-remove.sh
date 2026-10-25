#!/usr/bin/env bash
# Откат: экран входа снова как в оригинальной теме
THEME=/usr/share/sddm/themes/sddm-astronaut-theme
CONF=$(sed -n 's/^ConfigFile=//p' "$THEME/metadata.desktop")
sudo rm -f "$THEME/$CONF.user" "$THEME/Backgrounds/rice.png"
echo "Экран входа вернулся к оригинальной теме"
