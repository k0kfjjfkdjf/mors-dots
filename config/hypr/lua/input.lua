--@file Ввод
-- Строки --@ — разметка для mors-settings (configurator/).
hl.config({
--@section Клавиатура
    input = {
        --@name: Раскладки | type: string | desc: Через запятую, без пробелов: us,ru
        kb_layout    = "us,ru",
        kb_variant   = "",
        kb_model     = "",
        --@name: Переключение раскладки | type: enum | options: grp:alt_shift_toggle, grp:ctrl_shift_toggle, grp:caps_toggle, grp:win_space_toggle | desc: Сочетание клавиш для смены языка
        kb_options   = "grp:alt_shift_toggle",
        kb_rules     = "",
--@end
--@section Мышь и тачпад
        --@name: Фокус за мышью | type: enum | options: 0, 1, 2, 3 | desc: 1 — фокус переходит на окно под курсором, 0 — только по клику
        follow_mouse = 1,
        --@name: Чувствительность мыши | type: float | range: -1-1 | step: 0.1 | desc: 0 — как есть
        sensitivity  = 0,
        touchpad = {
            --@name: Естественная прокрутка | type: bool | desc: Как на смартфоне: палец вниз → страница вверх
            natural_scroll = true,
        },
--@end
    },
})

hl.device({ name = "epic-mouse-v1", sensitivity = -0.5 })
