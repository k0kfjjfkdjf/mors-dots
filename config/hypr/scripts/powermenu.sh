#!/usr/bin/env bash
# Меню питания: Super+Esc и кнопка питания (XF86PowerOff).
#   powermenu.sh       — открыть меню
#   powermenu.sh key   — от кнопки питания. Меню показывается, только если в mors-settings
#                        (Система → Электропитание) для кнопки выбрано «показать меню»; иначе кнопку
#                        обрабатывает systemd-logind сам. На заблокированном экране — действие LOCKED_KEY.
# Что в меню и что спрашивать — ~/.config/hypr/power.env (пишет mors-settings).
set -u
MENU_KEY=0
MENU_ITEMS="lock suspend reboot poweroff logout"
MENU_CONFIRM="reboot poweroff logout"
LOCKED_KEY=suspend
ENV="${XDG_CONFIG_HOME:-$HOME/.config}/hypr/power.env"
[[ -r "$ENV" ]] && . "$ENV"

declare -A LABEL=(
    [lock]="  Заблокировать" [suspend]="󰤄  Сон" [hibernate]="󰒲  Гибернация"
    [reboot]="󰜉  Перезагрузка" [poweroff]="󰐥  Выключение" [logout]="󰍃  Выйти из сеанса"
)
declare -A VERB=(
    [lock]="заблокировать" [suspend]="уснуть" [hibernate]="уйти в гибернацию"
    [reboot]="перезагрузить" [poweroff]="выключить" [logout]="выйти из сеанса"
)

act() {
    case "$1" in
        lock)    if pgrep -x hypridle >/dev/null; then loginctl lock-session   # hypridle сам вызовет hyprlock
                 else pidof hyprlock >/dev/null || hyprlock & fi ;;
        suspend|hibernate|reboot|poweroff) systemctl "$1" ;;
        logout)  if command -v hyprshutdown >/dev/null 2>&1; then exec hyprshutdown; fi
                 out="$(hyprctl dispatch 'hl.dsp.exit()' 2>&1)"; [[ "$out" == ok* ]] || hyprctl dispatch exit ;;
        ignore|"") ;;
    esac
}

if [[ "${1:-}" == key ]]; then
    [[ "$MENU_KEY" == 1 ]] || exit 0
    if pidof hyprlock >/dev/null; then act "$LOCKED_KEY"; exit 0; fi
fi

if pgrep -x rofi >/dev/null; then pkill -x rofi; exit 0; fi   # второе нажатие — закрыть меню

read -r -a items <<<"$MENU_ITEMS"
(( ${#items[@]} )) || items=(lock suspend reboot poweroff logout)
up=$(cut -d. -f1 /proc/uptime); d=$((up / 86400)); h=$((up % 86400 / 3600)); m=$((up % 3600 / 60))
mesg="Работает $( ((d)) && printf '%d д ' $d)$( ((h)) && printf '%d ч ' $h)${m} мин"

choice=$(for i in "${items[@]}"; do echo "${LABEL[$i]:-$i}"; done |
    rofi -dmenu -i -no-custom -format i -p "" -mesg "$mesg" \
         -theme "$HOME/.config/rofi/powermenu.rasi" -theme-str "listview { lines: ${#items[@]}; }") || exit 0
[[ -n "$choice" ]] || exit 0
what="${items[$choice]}"

if [[ " $MENU_CONFIRM " == *" $what "* ]]; then
    yes="Да, ${VERB[$what]}"
    ans=$(printf '%s\n%s\n' "$yes" "Отмена" |
        rofi -dmenu -i -no-custom -p "" -mesg "Точно ${VERB[$what]}?" \
             -theme "$HOME/.config/rofi/powermenu.rasi" -theme-str "listview { lines: 2; }") || exit 0
    [[ "$ans" == "$yes" ]] || exit 0
fi
act "$what"
