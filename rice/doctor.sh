#!/usr/bin/env bash
# Проверка установки mors-dots — ничего не меняет, только показывает.
#
#   ~/.config/rice/doctor.sh
#
# • конфиги в ~/.config — ссылки на репозиторий, а не отдельные копии (дубли);
# • дубли обоев (одинаковые картинки) и картинки, оставшиеся без темы;
# • копии, которые копятся рядом (hyprpanel config.json.bak*, бэкапы установщика);
# • машина (hosts/), текущая тема, пакеты для конфигуратора, состояние git.

DOTS="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
C=$'\e[1;35m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; D=$'\e[2m'; N=$'\e[0m'
ok()   { echo "  ${G}✓${N} $*"; }
warn() { echo "  ${Y}!${N} $*"; ISSUES=$((ISSUES+1)); }
bad()  { echo "  ${R}✗${N} $*"; ISSUES=$((ISSUES+1)); }
hd()   { echo; echo "${C}$*${N}"; }
ISSUES=0

hd "Репозиторий: $DOTS"
if git -C "$DOTS" rev-parse --git-dir >/dev/null 2>&1; then
    br="$(git -C "$DOTS" rev-parse --abbrev-ref HEAD)"
    ok "ветка $br, версия $(git -C "$DOTS" log -1 --format='%h · %s')"
    git -C "$DOTS" fetch -q 2>/dev/null && {
        behind="$(git -C "$DOTS" rev-list --count HEAD..@{u} 2>/dev/null || echo ?)"
        [[ "$behind" == 0 ]] && ok "последняя версия" || warn "отстаёт от GitHub на $behind коммит(ов) — обнови"
    }
    ch="$(git -C "$DOTS" status --porcelain --untracked-files=no | wc -l)"
    [[ $ch -eq 0 ]] || warn "локально изменено файлов в репозитории: $ch (git -C $DOTS status)"
else
    bad "это не git-клон — обновление с GitHub работать не будет"
fi

hd "Ссылки ~/.config → репозиторий (не должно быть копий)"
check_link() {  # check_link <в репо> <в ~/.config>
    local src="$1" dst="$2" short="${2/#"$HOME"/\~}"
    if [[ -L "$dst" ]]; then
        if [[ "$(readlink -f "$dst")" == "$(readlink -f "$src")" ]]; then ok "$short"
        else bad "$short → $(readlink -f "$dst") (ведёт не в этот репозиторий)"; fi
    elif [[ -e "$dst" ]]; then
        bad "$short — обычная копия, а не ссылка: правки в репо сюда не попадут (дубль). Исправит: $DOTS/install.sh"
    else
        warn "$short — нет (запусти $DOTS/install.sh)"
    fi
}
for d in hypr kitty rofi fish fastfetch; do check_link "$DOTS/config/$d" "$HOME/.config/$d"; done
check_link "$DOTS/rice" "$HOME/.config/rice"
check_link "$DOTS/config/gtk-3.0/settings.ini" "$HOME/.config/gtk-3.0/settings.ini"
check_link "$DOTS/config/gtk-4.0/settings.ini" "$HOME/.config/gtk-4.0/settings.ini"

hd "Машина и тема"
host="$(cat "$HOME/.config/mors-dots/host" 2>/dev/null)"
hl="$DOTS/config/hypr/lua/host.lua"
if [[ -L "$hl" ]]; then ok "машина: ${host:-?} (host.lua → $(readlink "$hl" | sed 's#.*/hosts/##'))"
else bad "нет config/hypr/lua/host.lua — запусти install.sh --host <машина>"; fi
[[ -n "$host" && -L "$hl" && "$(readlink "$hl")" != *"/hosts/$host/"* ]] && warn "в ~/.config/mors-dots/host записано «$host», а host.lua указывает на другую машину"
theme="$(cat "$DOTS/rice/current" 2>/dev/null)"
[[ -n "$theme" ]] && ok "тема: $theme" || warn "тема не выбрана — rice.py apply <тема>"

hd "Обои (rice/wallpapers/<тема>/)"
WP="$DOTS/rice/wallpapers"
python3 "$DOTS/rice/rice.py" wallpapers >/dev/null 2>&1 || true   # заодно разложит старый local/ по темам
for t in "$DOTS"/rice/themes/*.json; do
    t="$(basename "$t" .json)"
    n="$(find "$WP/$t" -type f \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' -o -iname '*.gif' -o -iname '*.bmp' \) 2>/dev/null | wc -l)"
    [[ $n -gt 0 ]] && ok "$t: картинок $n" || warn "$t: папка пуста ($WP/$t)"
done
for f in "$WP"/*.png "$WP"/*.jpg; do [[ -e "$f" ]] && warn "картинка лежит в корне wallpapers/, а не в папке темы: $(basename "$f")"; done
if [[ -d "$WP/local" ]] && compgen -G "$WP/local/*" >/dev/null; then
    warn "в wallpapers/local/ остались картинки без темы: $(ls "$WP/local" | tr '\n' ' ')— перенеси в папку темы"
fi
dups="$(find "$WP" -type f -exec md5sum {} + 2>/dev/null | sort | awk '{h=$1; $1=""; f=substr($0,2); if (h==p) {print "    " pf "  =  " f} p=h; pf=f}')"
if [[ -n "$dups" ]]; then warn "одинаковые картинки (дубли):"; echo "${dups//$WP\//}"; else ok "дублей картинок нет"; fi

hd "Копии, которые копятся"
hpb="$(ls "$HOME"/.config/hyprpanel/config.json.bak* 2>/dev/null | wc -l)"
[[ $hpb -le 3 ]] && ok "резервных копий config.json HyprPanel: $hpb" \
    || warn "резервных копий config.json HyprPanel: $hpb — старые можно удалить: ls ~/.config/hyprpanel/config.json.bak*"
bk="$HOME/.config/mors-dots-backup"
if [[ -d "$bk" ]]; then
    n="$(ls "$bk" | wc -l)"; sz="$(du -sh "$bk" 2>/dev/null | cut -f1)"
    [[ $n -le 3 ]] && ok "бэкапов установщика: $n ($sz)" || warn "бэкапов установщика: $n ($sz) в $bk — старые можно удалить"
fi
for d in hypr kitty rofi fish fastfetch rice; do
    for x in "$HOME/.config/$d".{bak,old,orig} "$HOME/.config/$d"~ "$HOME/.config/$d"-backup*; do
        [[ -e "$x" ]] && warn "лишняя копия: ${x/#"$HOME"/\~}"
    done
done

hd "Конфигуратор (ветка configurator)"
if [[ -x "$DOTS/configurator/app/mors-settings" ]]; then
    for p in python-gobject gtk3 webkit2gtk-4.1; do
        pacman -Q "$p" >/dev/null 2>&1 && ok "пакет $p" || bad "нет пакета $p: sudo pacman -S --needed $p"
    done
    pid="$(cat "${XDG_CACHE_HOME:-$HOME/.cache}/mors-settings/gear-redirect.pid" 2>/dev/null)"
    [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null && ok "шестерёнка HyprPanel → mors-settings работает" \
        || warn "перехват шестерёнки не запущен: python3 $DOTS/configurator/app/gear-redirect.py & disown (дальше — сам при входе)"
    [[ -f "$DOTS/configurator/prototype/configurator.html" ]] && ok "интерфейс собран" || bad "нет configurator.html — python $DOTS/configurator/tools/build.py"
else
    echo "  ${D}не установлен — это нормально на ветке main${N}"
fi

echo
[[ $ISSUES -eq 0 ]] && echo "${G}Всё в порядке.${N}" || echo "${Y}Замечаний: $ISSUES${N}"
