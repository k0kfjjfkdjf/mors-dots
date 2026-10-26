# Конфигуратор

«Конфиг для конфигов»: программа строит окно настроек прямо по комментариям в конфигах и
правит в файле только нужное значение. Сейчас здесь **кликабельный HTML-прототип** — проверяем
интерфейс, прежде чем писать саму программу.

## Как запустить

**Как программу** (настоящая тема, обновление, запись настроек HyprPanel):

```bash
sudo pacman -S --needed webkit2gtk-4.1          # окно на GTK + WebKit
~/mors-dots/configurator/app/mors-settings      # или шестерёнка в панели управления HyprPanel
```

**Как прототип в браузере** — только посмотреть интерфейс, команды не выполняются:

```bash
xdg-open ~/mors-dots/configurator/prototype/configurator.html
```

## Шестерёнка в HyprPanel

Кнопка 󰒓 в панели управления (аватарка слева вверху) зашита в код HyprPanel и открывает
его окно настроек. Код не трогаем: `app/gear-redirect.py` слушает события Hyprland и, как
только появляется окно `hyprpanel-settings`, закрывает его и открывает `mors-settings`.
Запускается из `config/hypr/lua/autostart.lua`. Родное окно HyprPanel можно открыть
кнопкой на странице «Система».

## Что уже есть в прототипе

- **Разметка в комментариях.** Над параметром пишется строка `#@name: … | type: … | range: …`,
  по ней рисуется переключатель, ползунок, пипетка, список или захват клавиш. Разделы — `#@section`.
- **Начало разбора.** Весь файл, после строки-маркера или только между двумя маркерами —
  чтобы не трогать то, что генерирует тема или другой софт.
- **Конфиг из нескольких файлов.** Подключения (`source =`, `include`, `require`) становятся
  разделами; файл можно добавить вручную. Конфликты биндов ищутся по всем файлам.
- **HyprPanel на русском.** Полная копия его окна настроек: 871 настройка, 26 страниц,
  перевод всех строк. Код HyprPanel не меняется — правится только `config.json`.
  Цвета, которые перезаписывает `rice.py`, помечены «тема».
- **Система.** Тема всего райса (то же, что `rice.py apply`), масштаб интерфейса,
  кнопка «Обновить райс с GitHub»: `git pull --ff-only` → `rice.py apply <текущая>` →
  `hyprctl reload`; если изменились пакеты или установщик — предложит запустить `install.sh`.
- **Цвета из темы rice.** Программа красится в текущую тему (`rice/current` →
  `rice/themes/<тема>.json`) и перекрашивается сама при смене темы. В прототипе смену
  имитируют карточки тем на странице «Система»; при этом пересчитываются и цвета HyprPanel —
  так же, как в `rice.py`. В программе окно следит за `rice/current` и `config.json` само.

## Структура

```
configurator/
├── app/
│   ├── mors-settings           окно GTK + WebKit: интерфейс + мост к rice.py, git, config.json
│   └── gear-redirect.py        шестерёнка HyprPanel → mors-settings
├── prototype/
│   ├── configurator.src.html   исходник интерфейса (данные подставляет build.py)
│   └── configurator.html       собранный прототип — его и открывать
├── adapters/hyprpanel/
│   ├── options.json            окно настроек HyprPanel, вытащенное из исходников
│   ├── defaults.json           стандартные значения всех ключей
│   ├── strings.json            строки интерфейса для перевода
│   └── ru.json                 перевод
├── tools/
│   ├── hyprpanel_extract.py    исходники HyprPanel → options/defaults/strings
│   └── build.py                всё вместе → prototype/configurator.html
└── docs/research.md            где что хранится: HyprPanel, fastfetch, neofetch
```

## Пересборка

```bash
cd ~/mors-dots/configurator
python tools/build.py                                    # значения из репозитория + текущая тема
python tools/build.py --config ~/.config/hyprpanel/config.json   # твой живой config.json
```

После обновления HyprPanel:

```bash
git clone --depth 1 https://github.com/Jas-SinghFSU/HyprPanel /tmp/HyprPanel
python tools/hyprpanel_extract.py /tmp/HyprPanel
python tools/build.py        # перечислит строки, которых ещё нет в ru.json
```

## Дальше

- fastfetch: список модулей с перетаскиванием и включением (отключение = комментарий `//`),
  подсказки из официальной JSON-схемы;
- Hyprland на Lua: разметка `--@`, разделы по `require(...)`, значения из `lua/theme.lua`
  помечать как «из темы»;
- выбор стека для настоящей программы (GTK4/libadwaita или TUI).
