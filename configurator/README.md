# Конфигуратор

«Конфиг для конфигов»: программа строит окно настроек прямо по комментариям в конфигах и
правит в файле только нужное значение. Сейчас здесь **кликабельный HTML-прототип** — проверяем
интерфейс, прежде чем писать саму программу.

## Как посмотреть

Открыть [`prototype/configurator.html`](prototype/configurator.html) в браузере — ничего ставить не нужно.

```bash
xdg-open ~/mors-dots/configurator/prototype/configurator.html
```

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
- **Цвета из темы rice.** Программа красится в текущую тему (`rice/current` →
  `rice/themes/<тема>.json`) и перекрашивается сама при смене темы. В прототипе смену
  имитируют кнопки в углу; при этом пересчитываются и цвета HyprPanel — так же, как в `rice.py`.

## Структура

```
configurator/
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
