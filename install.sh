#!/usr/bin/env bash
# mors-dots — райс Hyprland одной командой.
#
#   git clone https://github.com/k0kfjjfkdjf/mors-dots ~/mors-dots && ~/mors-dots/install.sh
#   или:  curl -fsSL https://raw.githubusercontent.com/k0kfjjfkdjf/mors-dots/main/install.sh | bash
#
# Опции:
#   --host <имя>     набор машинных настроек из hosts/ (по умолчанию спросит; без ответа — default)
#   --theme <имя>    mono | sakura | aurora (по умолчанию aurora или текущая)
#   --no-packages    не ставить пакеты
#   --no-sddm        не трогать экран входа
#   -y               не задавать вопросов
#
# Повторный запуск безопасен: всё, что заменяется, уходит в ~/.config/mors-dots-backup/<дата>.

set -euo pipefail

REPO_URL="https://github.com/k0kfjjfkdjf/mors-dots"
CLONE_DIR="$HOME/mors-dots"

# ---------- запуск через curl | bash: сначала клонируем репозиторий
SELF="${BASH_SOURCE[0]:-}"
DOTS=""
[[ -n "$SELF" && -f "$SELF" ]] && DOTS="$(cd "$(dirname "$(readlink -f "$SELF")")" && pwd)"
if [[ -z "$DOTS" || ! -d "$DOTS/config" ]]; then
    command -v git >/dev/null || sudo pacman -S --needed --noconfirm git
    if [[ -d "$CLONE_DIR/.git" ]]; then git -C "$CLONE_DIR" pull --ff-only
    else git clone "$REPO_URL" "$CLONE_DIR"; fi
    exec bash "$CLONE_DIR/install.sh" "$@"
fi

# ---------- опции
HOST=""; THEME=""; DO_PKGS=1; DO_SDDM=1; YES=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --host) HOST="$2"; shift 2 ;;
        --theme) THEME="$2"; shift 2 ;;
        --no-packages) DO_PKGS=0; shift ;;
        --no-sddm) DO_SDDM=0; shift ;;
        -y|--yes) YES=1; shift ;;
        -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
        *) echo "Неизвестная опция: $1"; exit 1 ;;
    esac
done

c_ok=$'\e[32m'; c_warn=$'\e[33m'; c_hd=$'\e[1;35m'; c_0=$'\e[0m'
step() { echo; echo "${c_hd}==> $*${c_0}"; }
ok()   { echo "  ${c_ok}✓${c_0} $*"; }
warn() { echo "  ${c_warn}!${c_0} $*"; WARNINGS+=("$*"); }
WARNINGS=()

ask() {  # ask "вопрос" "по умолчанию"
    local ans
    if [[ $YES -eq 1 || ! -r /dev/tty ]]; then echo "$2"; return; fi
    read -r -p "$1 [$2]: " ans </dev/tty || true
    echo "${ans:-$2}"
}

[[ $EUID -ne 0 ]] || { echo "Запускай от обычного пользователя, не от root."; exit 1; }
command -v pacman >/dev/null || { echo "Нужен Arch Linux (pacman)."; exit 1; }

STATE_DIR="$HOME/.config/mors-dots"
mkdir -p "$STATE_DIR"
BACKUP="$HOME/.config/mors-dots-backup/$(date +%F_%H%M%S)"

# ---------- машина
if [[ -z "$HOST" ]]; then
    saved="$(cat "$STATE_DIR/host" 2>/dev/null || true)"
    hosts="$(ls "$DOTS/hosts" | tr '\n' ' ')"
    HOST="$(ask "Машина ($hosts)" "${saved:-default}")"
fi
[[ -f "$DOTS/hosts/$HOST/hypr.lua" ]] || { echo "Нет hosts/$HOST/hypr.lua"; exit 1; }
echo "$HOST" > "$STATE_DIR/host"

echo "${c_hd}mors-dots${c_0}: машина «$HOST», репозиторий $DOTS"
sudo -v
( while true; do sudo -n true; sleep 50; kill -0 "$$" 2>/dev/null || exit; done ) 2>/dev/null &

read_list() { grep -vE '^\s*(#|$)' "$1" | awk '{print $1}'; }

# ---------- пакеты
if [[ $DO_PKGS -eq 1 ]]; then
    step "Пакеты из репозиториев Arch"
    mapfile -t PKGS < <(read_list "$DOTS/packages/pacman.txt")
    if ! sudo pacman -S --needed --noconfirm "${PKGS[@]}"; then
        warn "общая установка не прошла — ставлю по одному"
        for p in "${PKGS[@]}"; do sudo pacman -S --needed --noconfirm "$p" >/dev/null 2>&1 || warn "не установился: $p"; done
    fi
    ok "pacman"

    step "AUR"
    if ! command -v yay >/dev/null; then
        tmp="$(mktemp -d)"; git clone --depth 1 https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
        (cd "$tmp/yay-bin" && makepkg -si --noconfirm); rm -rf "$tmp"
    fi
    mapfile -t AUR < <(read_list "$DOTS/packages/aur.txt")
    for p in "${AUR[@]}"; do
        yay -S --needed --noconfirm --answerclean None --answerdiff None "$p" || warn "AUR: не установился $p"
    done
    ok "yay"
fi

# ---------- шрифт Geist (kitty, rofi) — если нет в системе, берём с GitHub
step "Шрифты"
if fc-list | grep -qi "Geist Mono"; then ok "Geist уже есть"
else
    url="$(curl -fsSL https://api.github.com/repos/vercel/geist-font/releases/latest \
        | python3 -c 'import json,sys; a=json.load(sys.stdin)["assets"]; print(next(x["browser_download_url"] for x in a if x["name"].endswith(".zip")))' 2>/dev/null || true)"
    if [[ -n "$url" ]]; then
        tmp="$(mktemp -d)"; curl -fsSL "$url" -o "$tmp/geist.zip" && unzip -qo "$tmp/geist.zip" -d "$tmp/g"
        mkdir -p "$HOME/.local/share/fonts/geist"
        find "$tmp/g" -type f \( -name '*.otf' -o -name '*.ttf' \) -exec cp {} "$HOME/.local/share/fonts/geist/" \;
        rm -rf "$tmp"; fc-cache -f >/dev/null; ok "Geist установлен в ~/.local/share/fonts/geist"
    else warn "не скачал Geist — kitty/rofi возьмут запасной шрифт"; fi
fi

# ---------- конфиги: симлинки из репозитория
step "Конфиги"
link() {  # link <в репо> <куда>
    local src="$1" dst="$2"
    if [[ -L "$dst" && "$(readlink -f "$dst")" == "$(readlink -f "$src")" ]]; then ok "уже на месте: ${dst/#$HOME/~}"; return; fi
    if [[ -e "$dst" || -L "$dst" ]]; then
        mkdir -p "$BACKUP/$(dirname "${dst#$HOME/}")"
        mv "$dst" "$BACKUP/${dst#$HOME/}"
    fi
    mkdir -p "$(dirname "$dst")"
    ln -s "$src" "$dst"; ok "${dst/#$HOME/~} → репо"
}
for d in hypr kitty rofi fish fastfetch; do link "$DOTS/config/$d" "$HOME/.config/$d"; done
link "$DOTS/rice"                         "$HOME/.config/rice"
link "$DOTS/config/gtk-3.0/settings.ini"  "$HOME/.config/gtk-3.0/settings.ini"
link "$DOTS/config/gtk-4.0/settings.ini"  "$HOME/.config/gtk-4.0/settings.ini"

# машинные настройки Hyprland
ln -sfn "../../../hosts/$HOST/hypr.lua" "$DOTS/config/hypr/lua/host.lua"
ok "hypr/lua/host.lua → hosts/$HOST/hypr.lua"

# HyprPanel: свой config.json не трогаем (там настройки из GUI), только если его нет
if [[ ! -f "$HOME/.config/hyprpanel/config.json" ]]; then
    mkdir -p "$HOME/.config/hyprpanel"
    cp "$DOTS/config/hyprpanel/config.base.json" "$HOME/.config/hyprpanel/config.json"; ok "hyprpanel/config.json из шаблона"
fi

# переносим личное из бэкапа обратно (то, чего нет в git)
if [[ -d "$BACKUP/.config" ]]; then
    B="$BACKUP/.config"
    [[ -d "$B/fastfetch/images" ]] && { mkdir -p "$DOTS/config/fastfetch/images"; cp --update=none "$B/fastfetch/images/"* "$DOTS/config/fastfetch/images/" 2>/dev/null || true; ok "картинки fastfetch перенесены"; }
    [[ -f "$B/fish/fish_variables" ]] && cp --update=none "$B/fish/fish_variables" "$DOTS/config/fish/"
    [[ -d "$B/fish/functions" ]] && cp --update=none "$B/fish/functions/"* "$DOTS/config/fish/functions/" 2>/dev/null || true
    if [[ -d "$B/rice" ]]; then   # старая установка rice: личные обои, текущая тема
        for f in "$B/rice/wallpapers/"*.png; do
            [[ -e "$f" ]] || continue
            n="$(basename "$f")"; [[ -e "$DOTS/rice/wallpapers/$n" ]] || cp --update=none "$f" "$DOTS/rice/wallpapers/local/$n"
        done
        cp --update=none "$B/rice/current" "$B/rice/wallpaper-index.json" "$DOTS/rice/" 2>/dev/null || true
        ok "личные обои и выбор темы перенесены из прошлой установки"
    fi
fi
chmod +x "$DOTS/rice/"*.sh "$DOTS/rice/rice.py" "$DOTS/config/hypr/scripts/"* 2>/dev/null || true

# KDE: иконки, терминал, стиль (цвета пишет rice)
python3 - <<'PY'
import configparser, pathlib
p = pathlib.Path.home() / ".config/kdeglobals"
c = configparser.RawConfigParser(strict=False, interpolation=None); c.optionxform = str
if p.exists(): c.read(p, encoding="utf-8")
for s, k, v in [("Icons", "Theme", "breeze-dark"), ("General", "TerminalApplication", "kitty"),
                ("General", "TerminalService", "kitty.desktop"), ("KDE", "widgetStyle", "Breeze")]:
    if not c.has_section(s): c.add_section(s)
    c.set(s, k, v)
with open(p, "w", encoding="utf-8") as f: c.write(f, space_around_delimiters=False)
PY
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
gsettings set org.gnome.desktop.interface icon-theme breeze-dark 2>/dev/null || true
gsettings set org.gnome.desktop.interface cursor-theme breeze_cursors 2>/dev/null || true
ok "KDE/GTK: иконки breeze-dark, терминал kitty"

# fish по умолчанию? — только если пользователь хочет
if [[ "$(basename "${SHELL:-}")" != "fish" ]] && command -v fish >/dev/null; then
    [[ "$(ask "Сделать fish оболочкой по умолчанию? (y/n)" n)" == y ]] && chsh -s "$(command -v fish)" && ok "оболочка: fish"
fi

# ---------- экран входа
if [[ $DO_SDDM -eq 1 ]]; then
    step "Экран входа (SDDM)"
    THEME_DIR=/usr/share/sddm/themes/sddm-astronaut-theme
    if [[ ! -d "$THEME_DIR" ]]; then
        sudo git clone --depth 1 https://github.com/Keyitdev/sddm-astronaut-theme "$THEME_DIR" \
            && { [[ -d "$THEME_DIR/Fonts" ]] && sudo cp -r --update=none "$THEME_DIR/Fonts/"* /usr/share/fonts/ ; true; } \
            && ok "тема astronaut скачана с GitHub" || warn "не удалось поставить sddm-astronaut-theme"
    fi
    if [[ -d "$THEME_DIR" ]]; then
        [[ -f "$THEME_DIR/Themes/black_hole.conf" ]] && \
            sudo sed -i 's|^ConfigFile=.*|ConfigFile=Themes/black_hole.conf|' "$THEME_DIR/metadata.desktop"
        sudo install -d /etc/sddm.conf.d
        printf '[Theme]\nCurrent=sddm-astronaut-theme\n\n[General]\nInputMethod=qtvirtualkeyboard\n' \
            | sudo tee /etc/sddm.conf.d/10-theme.conf >/dev/null
        ok "тема экрана входа: sddm-astronaut-theme"
    fi
    # машинная расстановка мониторов на экране входа
    if [[ -d "$DOTS/hosts/$HOST/sddm" ]]; then
        H="$DOTS/hosts/$HOST/sddm"
        sudo install -Dm755 "$H/monitors.py" /etc/sddm/monitors.py
        sudo install -Dm755 "$H/Xsetup" /etc/sddm/Xsetup
        sudo install -Dm644 "$H/10-monitors.conf" /etc/sddm.conf.d/10-monitors.conf
        ok "мониторы на экране входа: hosts/$HOST/sddm"
    fi
    if ! systemctl is-enabled display-manager.service >/dev/null 2>&1; then
        sudo systemctl enable sddm.service && ok "sddm включён"
    else
        dm="$(readlink -f /etc/systemd/system/display-manager.service | xargs basename)"
        [[ "$dm" == sddm.service ]] && ok "sddm уже включён" || warn "включён другой менеджер входа ($dm) — sddm не трогаю"
    fi
fi

# ---------- тема
step "Тема"
if [[ -z "$THEME" ]]; then
    cur="$(python3 "$DOTS/rice/rice.py" current 2>/dev/null || true)"
    THEME="$(ask "Тема (mono / sakura / aurora)" "${cur:-aurora}")"
fi
if [[ $DO_SDDM -eq 1 && -d /usr/share/sddm/themes/sddm-astronaut-theme ]]; then
    bash "$DOTS/rice/sddm-setup.sh" >/dev/null && ok "экран входа подключён к темам"
fi
python3 "$DOTS/rice/rice.py" apply "$THEME"
pgrep -x Hyprland >/dev/null && hyprctl reload >/dev/null 2>&1 || true

# ---------- итог
echo
echo "${c_hd}Готово.${c_0}"
[[ -d "$BACKUP" ]] && echo "  Бэкап заменённого: ${BACKUP/#$HOME/~}"
echo "  SUPER+SHIFT+T — меню тем · SUPER+SHIFT+W — следующие обои · SUPER+Q — терминал"
echo "  Личные обои: положи png в ~/.config/rice/wallpapers/local/ (имена — в rice/themes/*.json)"
if [[ ${#WARNINGS[@]} -gt 0 ]]; then
    echo; echo "${c_warn}Предупреждения:${c_0}"; printf '  - %s\n' "${WARNINGS[@]}"
fi
pgrep -x Hyprland >/dev/null || echo "  Перезагрузись и выбери Hyprland на экране входа."
