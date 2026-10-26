#!/usr/bin/env python3
"""Собирает прототип: prototype/configurator.src.html + данные → prototype/configurator.html

    build.py [--config ~/.config/hyprpanel/config.json] [--theme sakura]

Без --config значения HyprPanel берутся из репозитория: config/hyprpanel/config.base.json
+ цвета темы, посчитанные так же, как rice.py apply. С --config — твой живой файл.
Тема по умолчанию — из rice/current, иначе sakura.
"""
import argparse, importlib.util, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent.parent          # configurator/
DOTS = HERE.parent                                             # корень mors-dots
AD = HERE / 'adapters/hyprpanel'
RICE = DOTS / 'rice'

ap = argparse.ArgumentParser()
ap.add_argument('--config', help='живой config.json HyprPanel')
ap.add_argument('--theme')
ap.add_argument('--out', default=str(HERE / 'prototype/configurator.html'))
args = ap.parse_args()

# rice.py как модуль — берём из него Theme и hyprpanel_theme, ничего не применяя
sys.argv = ['rice.py']
spec = importlib.util.spec_from_file_location('rice', RICE / 'rice.py')
rice = importlib.util.module_from_spec(spec); spec.loader.exec_module(rice)
current = args.theme or ((RICE / 'current').read_text().strip() if (RICE / 'current').exists() else 'sakura')

ex = json.loads((AD / 'options.json').read_text())
defaults = json.loads((AD / 'defaults.json').read_text())
ru = json.loads((AD / 'ru.json').read_text())
tpl = json.loads((RICE / 'templates/hyprpanel.json').read_text())

if args.config:
    user = json.loads(pathlib.Path(args.config).expanduser().read_text())
else:
    user = json.loads((DOTS / 'config/hyprpanel/config.base.json').read_text())
    user.update(rice.hyprpanel_theme(rice.Theme(current)))
    user['theme.matugen'] = False

missing = [s for s in json.loads((AD / 'strings.json').read_text()) if s not in ru]
if missing:
    print(f'Нет перевода для {len(missing)} строк (останутся по-английски):')
    for s in missing: print('  ', json.dumps(s, ensure_ascii=False))

T = lambda s: ru.get(s, s)
pages = [{'tab': tab, 'id': p, 'ru': T(p)} for tab in ('config', 'theme') for p in ex['pages'][tab]]
pid = {(p['tab'], p['id']): i for i, p in enumerate(pages)}
opts = []
for x in ex['options']:
    sub = x['subtitle']
    if sub and sub.startswith('bind(options.wallpaper.image)'):
        sub = '@wallpaper'                       # динамическая подсказка: путь к обоям
    e = {'p': pid[(x['tab'], x['page'])], 'h': T(x['header']) if x['header'] else '', 'k': x['key'],
         't': T(x['title']), 'en': x['title'], 'ty': x['type'], 'd': defaults.get(x['key'])}
    if sub: e['s'] = sub if sub == '@wallpaper' else T(sub)
    if x['link']: e['l'] = x['link']
    for a, b in (('min', 'mn'), ('max', 'mx'), ('step', 'st'), ('enums', 'en_')):
        if x[a] is not None: e[b] = x[a]
    if x['key'] in tpl: e['r'] = 1                # этот ключ перезаписывает rice.py
    opts.append(e)

themes = {}
for f in sorted((RICE / 'themes').glob('*.json')):
    t = json.loads(f.read_text())
    themes[f.stem] = {k: t[k] for k in ('name', 'description', 'palette', 'accent', 'border')}
rice_data = {'current': current, 'themes': themes, 'mocha': rice.MOCHA, 'hpTemplate': tpl}

js = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
html = (HERE / 'prototype/configurator.src.html').read_text()
for ph, data in (('/*HP_DATA*/null', {'pages': pages, 'opts': opts, 'user': user}), ('/*RICE_DATA*/null', rice_data)):
    assert ph in html, ph
    html = html.replace(ph, js(data))
pathlib.Path(args.out).write_text(html)
print(f'{args.out}: {len(opts)} настроек HyprPanel, {len(pages)} страниц, тема {current}, '
      f'{round(len(html) / 1024)} КБ')
