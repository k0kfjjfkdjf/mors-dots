# Где что хранится

Заметки для конфигуратора: откуда брать значения и как устроены настройки программ из райса.

## HyprPanel

- **Значения:** `~/.config/hyprpanel/config.json` — плоский JSON вида `"theme.bar.floating": false`.
  HyprPanel сам перечитывает файл при изменении. Ключей, которых нет в файле, HyprPanel
  берёт из умолчаний в коде.
- Рядом: `modules.json` и `modules.scss` — пользовательские модули.
- **Окно настроек — не файл, а код** HyprPanel:
  `src/components/settings/pages/{config,theme}/**` и `src/components/bar/settings/{config,theme}.tsx`.
  Каждая строка окна — `<Option opt={options.ключ} title="…" subtitle="…" type="…" />`,
  разделы — `<Header title="…" />`, порядок страниц — `src/components/settings/helpers.ts`.
  Открывается командой `hyprpanel toggleWindow settings-dialog`.
- **Умолчания:** `src/configuration/modules/**` — дерево `opt(значение)`.
- Объём (коммит 1961ba8): 871 настройка, 26 страниц (10 «Конфигурация» + 16 «Оформление»),
  590 уникальных строк для перевода.
- **В mors-dots:** `install.sh` кладёт `config/hyprpanel/config.base.json`, только если файла ещё нет;
  `rice.py apply` переписывает все ключи из `rice/templates/hyprpanel.json` (цвета темы,
  шаблон Catppuccin → ближайший слот палитры). Такие ключи в конфигураторе помечены «тема».

## fastfetch

- Конфиг: `~/.config/fastfetch/config.jsonc` (JSONC — с комментариями). В mors-dots — симлинк
  на `config/fastfetch/`, картинки в `config/fastfetch/images/` (не в git).
- Пресеты: `/usr/share/fastfetch/presets/`, `~/.local/share/fastfetch/presets/`;
  `fastfetch --list-presets`, `fastfetch --list-config-paths`.
- Есть официальная JSON-схема (`"$schema"` в начале конфига) — из неё можно строить
  интерфейс автоматически: типы, варианты, описания.
- Главное в конфиге — **массив модулей**, а не пары ключ-значение: нужен список с порядком
  и включением. Отключённые модули в mors-dots закомментированы `//`.

## neofetch

- Проект закрыт и заархивирован 26 апреля 2024; заменой обычно называют fastfetch.
- Конфиг — `~/.config/neofetch/config.conf`, это bash-скрипт. Поддержка — низкий приоритет.

## Hyprland (mors-dots)

- С 0.56 конфиг на Lua: `config/hypr/hyprland.lua` подключает `lua/*.lua` через `require`,
  настройки — вложенные таблицы в `hl.config({...})`. Комментарии — `--`, значит разметка `--@`.
- Цвета приходят из `lua/theme.lua` (пишет `rice.py`) как `t.border` и т.п. — это ссылки,
  а не значения: в конфигураторе их показывать как «из темы», а не редактировать.

## Источники

- HyprPanel — https://github.com/Jas-SinghFSU/HyprPanel
- fastfetch(1) — https://man.archlinux.org/man/extra/fastfetch/fastfetch.1.en.html
- Neofetch — https://en.wikipedia.org/wiki/Neofetch
