# mors-dots

Райс Hyprland на Arch Linux: три темы, переключаемые одной клавишей, от экрана входа до терминала.

| | |
|---|---|
| **WM** | Hyprland 0.56+ (конфиг на Lua) |
| **Панель** | HyprPanel |
| **Терминал** | kitty + fish |
| **Меню** | rofi |
| **Файлы** | Dolphin (тема через plasma-integration) |
| **Обои** | awww |
| **Вход** | SDDM + sddm-astronaut-theme |

## Установка

```bash
git clone https://github.com/k0kfjjfkdjf/mors-dots ~/mors-dots && ~/mors-dots/install.sh
```

или одной строкой:

```bash
curl -fsSL https://raw.githubusercontent.com/k0kfjjfkdjf/mors-dots/main/install.sh | bash
```

Установщик спросит машину и тему, поставит пакеты (pacman + AUR через yay), разложит конфиги
симлинками из репозитория, настроит экран входа и применит тему. Всё, что он заменяет,
уходит в `~/.config/mors-dots-backup/<дата>/`. Повторный запуск безопасен.

Опции: `--host <имя>`, `--theme <mono|sakura|aurora>`, `--no-packages`, `--no-sddm`, `-y`.

## Темы

| Тема | Настроение |
|---|---|
| **mono** | графит, белый текст, без цвета |
| **sakura** | тёмная слива, пастельно-розовый и лиловый |
| **aurora** | тёмно-синий, сине-фиолетовый, зелёный; рамка окна — вращающийся градиент |

Одна тема — один файл `rice/themes/<имя>.json`. Из него `rice/rice.py` генерирует цвета для
Hyprland, HyprPanel, kitty, rofi, Qt/KDE (Dolphin), GTK 3/4, fish, обоев и SDDM.

```bash
~/.config/rice/rice.py list            # темы
~/.config/rice/rice.py apply sakura    # применить
~/.config/rice/rice.py next            # следующие обои в теме
```

### Свои обои

Сгенерированные обои лежат в репозитории. Личные картинки (арты и т. п.) в git не попадают —
положи их в `~/.config/rice/wallpapers/local/` под именами из `"wallpapers"` в файле темы,
и тема подхватит их первыми. Нет картинок — остаются сгенерированные.

## Клавиши

| | |
|---|---|
| `SUPER+Q` | терминал |
| `SUPER+E` | Dolphin |
| `SUPER+D` / `SUPER+R` | меню приложений |
| `SUPER+C` | закрыть окно |
| `SUPER+V` | плавающее окно |
| `SUPER+F` / `SUPER+SHIFT+F` | полный экран / развернуть |
| `SUPER+T`, `SUPER+Tab` | группа окон, следующее в группе |
| `SUPER+1…0`, `SUPER+SHIFT+1…0` | рабочий стол / перенести окно |
| `SUPER+S` | scratchpad |
| `SUPER+SHIFT+T` | **меню тем** |
| `SUPER+SHIFT+W` / `SUPER+CTRL+W` | следующие / случайные обои |
| `SUPER+CTRL+D`, затем цифра | вкл/выкл монитор (0 — все) |
| `SUPER+M` | выход |

## Машины

Всё, что зависит от железа (мониторы, их бинды, особенности), — в `hosts/<машина>/`:

- `hosts/default` — мониторы расставляются автоматически;
- `hosts/pc1` — три монитора по EDID (BenQ · MKG 180 Гц · Samsung), прогрев 180 Гц,
  раскладка мониторов на экране входа.

Новая машина: скопируй `hosts/default` в `hosts/<имя>`, опиши мониторы
(`hyprctl monitors all | grep description`) и запусти `install.sh --host <имя>`.

## Структура

```
config/      конфиги → симлинки в ~/.config (hypr, kitty, rofi, fish, fastfetch, gtk)
hosts/       машинные настройки
packages/    списки пакетов pacman и AUR
rice/        переключатель тем, темы, обои, интеграция с SDDM
install.sh   установщик
```

## В разработке: конфигуратор

В ветке [`configurator`](https://github.com/k0kfjjfkdjf/mors-dots/tree/configurator/configurator) —
прототип «конфига для конфигов»: окно настроек строится по комментариям-разметке прямо в
конфигах, есть русская копия настроек HyprPanel, цвета берутся из текущей темы rice.
Прототип — один HTML-файл, открывается в браузере:
[`configurator/prototype/configurator.html`](https://github.com/k0kfjjfkdjf/mors-dots/blob/configurator/configurator/prototype/configurator.html).

```bash
git -C ~/mors-dots fetch origin configurator
git -C ~/mors-dots worktree add ~/mors-dots-configurator configurator
xdg-open ~/mors-dots-configurator/configurator/prototype/configurator.html
```
