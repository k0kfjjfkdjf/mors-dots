#!/usr/bin/env bash
# Один раз: даёт rice.py право менять экран входа без sudo.
# Тема sddm-astronaut читает <ConfigFile>.user поверх своего конфига — подкладываем туда ссылку.
set -euo pipefail
THEME=/usr/share/sddm/themes/sddm-astronaut-theme
CONF=$(sed -n 's/^ConfigFile=//p' "$THEME/metadata.desktop")
[[ -n "$CONF" ]] || { echo "Не нашёл ConfigFile в $THEME/metadata.desktop"; exit 1; }
sudo install -d -o "$USER" -g "$(id -gn)" -m 755 /var/lib/rice
sudo ln -sfn /var/lib/rice/sddm.conf.user "$THEME/$CONF.user"
sudo ln -sfn /var/lib/rice/sddm-bg.png   "$THEME/Backgrounds/rice.png"
echo "Готово: $THEME/$CONF.user → /var/lib/rice/sddm.conf.user"
cur=$(python3 ~/.config/rice/rice.py current)
python3 ~/.config/rice/rice.py apply "${cur:-aurora}"
