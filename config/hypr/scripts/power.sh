#!/usr/bin/env bash
# Помощник электропитания — его вызывает hypridle (конфиг пишет mors-settings → Система → Электропитание).
#
#   power.sh source ac|bat     код 0, если компьютер сейчас питается от этого: от сети / от батареи.
#                              Без батареи (ПК) — всегда «от сети».
#   power.sh dpms off|on       погасить / включить экраны (Lua-конфиг Hyprland 0.56+ и старый .conf)
#   power.sh sleep ДЕЙСТВИЕ    suspend | hibernate | suspend-then-hibernate | hybrid-sleep | poweroff
#   power.sh lock              экран блокировки (если ещё не запущен)
#   power.sh watch             фоном: батарея (предупредить / критично) и режим производительности
#                              от сети и от батареи. Настройки — ~/.config/hypr/power.env (пишет mors-settings);
#                              нет файла — сразу выходит. Запускается из autostart.lua, второй экземпляр не стартует.
set -u
ENV="${XDG_CONFIG_HOME:-$HOME/.config}/hypr/power.env"
SELF="$(readlink -f "$0")"

capacity() {      # средний заряд батарей ноутбука, %
    local sum=0 n=0 d
    for d in "${POWER_SUPPLY_DIR:-/sys/class/power_supply}"/*; do
        [[ "$(cat "$d/type" 2>/dev/null)" == Battery && "$(cat "$d/scope" 2>/dev/null)" != Device ]] || continue
        [[ -r "$d/capacity" ]] || continue
        sum=$((sum + $(cat "$d/capacity"))); n=$((n + 1))
    done
    ((n)) && echo $((sum / n)) || echo 100
}

on_battery() {
    local bat=0 mains=0 d
    for d in "${POWER_SUPPLY_DIR:-/sys/class/power_supply}"/*; do   # POWER_SUPPLY_DIR — для проверки
        [[ -r "$d/type" ]] || continue
        case "$(cat "$d/type")" in
            Battery) [[ "$(cat "$d/scope" 2>/dev/null)" == Device ]] || bat=1 ;;   # мышь/наушники — не в счёт
            Mains|USB|USB_C|USB_PD) [[ "$(cat "$d/online" 2>/dev/null)" == 1 ]] && mains=1 ;;
        esac
    done
    [[ $bat == 1 && $mains == 0 ]]
}

case "${1:-}" in
    source)
        case "${2:-}" in
            bat) on_battery ;;
            ac)  ! on_battery ;;
            *)   echo "power.sh source ac|bat" >&2; exit 2 ;;
        esac ;;
    dpms)
        act="${2:-off}"
        out="$(hyprctl dispatch "hl.dsp.dpms({ action = \"$act\" })" 2>&1)"
        [[ "$out" == ok* ]] || hyprctl dispatch dpms "$act" >/dev/null 2>&1 ;;
    sleep)
        case "${2:-suspend}" in
            suspend|hibernate|suspend-then-hibernate|hybrid-sleep|poweroff) exec systemctl "${2:-suspend}" ;;
            *) echo "неизвестное действие: $2" >&2; exit 2 ;;
        esac ;;
    lock)
        pidof hyprlock >/dev/null || exec hyprlock ;;
    watch)
        exec 9>"${XDG_RUNTIME_DIR:-/tmp}/mors-power-watch.lock"
        flock -n 9 || exit 0                          # уже следит другой экземпляр
        warned=0 crit=0 last=""
        while [[ -r "$ENV" ]]; do
            BAT_WARN=0 BAT_CRIT=0 BAT_CRIT_ACTION=hibernate PROFILE_AC="" PROFILE_BAT="" INTERVAL=30
            . "$ENV"
            if on_battery; then src=bat; else src=ac; fi
            if [[ "$src" != "$last" ]]; then          # сменился источник — сменить режим производительности
                prof=$([[ $src == bat ]] && echo "$PROFILE_BAT" || echo "$PROFILE_AC")
                [[ -n "$prof" ]] && command -v powerprofilesctl >/dev/null && powerprofilesctl set "$prof" 2>/dev/null
                last=$src
            fi
            if [[ $src == bat ]]; then
                cap=$(capacity)
                if (( BAT_CRIT > 0 && cap <= BAT_CRIT && crit == 0 )); then
                    crit=1
                    case "$BAT_CRIT_ACTION" in hibernate) what="гибернация";; poweroff) what="выключение";;
                        suspend-then-hibernate) what="сон, потом гибернация";; *) what="сон";; esac
                    notify-send -a power -u critical "Батарея: ${cap}%" "Через ${CRIT_WAIT:-30} секунд — ${what}. Подключи зарядку, чтобы отменить."
                    sleep "${CRIT_WAIT:-30}"
                    on_battery && (( $(capacity) <= BAT_CRIT )) && "$SELF" sleep "$BAT_CRIT_ACTION"
                elif (( BAT_WARN > 0 && cap <= BAT_WARN && warned == 0 )); then
                    warned=1
                    notify-send -a power -u normal "Батарея: ${cap}%" "Пора подключить зарядку"
                fi
            else
                warned=0 crit=0
            fi
            sleep "$INTERVAL"
        done ;;
    *)
        sed -n '2,10p' "$0"; exit 2 ;;
esac
