#!/usr/bin/env bash
# Помощник электропитания — его вызывает hypridle (конфиг пишет mors-settings → Система → Электропитание).
#
#   power.sh source ac|bat     код 0, если компьютер сейчас питается от этого: от сети / от батареи.
#                              Без батареи (ПК) — всегда «от сети».
#   power.sh dpms off|on       погасить / включить экраны (Lua-конфиг Hyprland 0.56+ и старый .conf)
#   power.sh sleep ДЕЙСТВИЕ    suspend | hibernate | suspend-then-hibernate | hybrid-sleep | poweroff
#   power.sh lock              экран блокировки (если ещё не запущен)
set -u

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
    *)
        sed -n '2,10p' "$0"; exit 2 ;;
esac
