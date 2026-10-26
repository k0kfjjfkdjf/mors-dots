#!/usr/bin/env python3
"""Вытаскивает окно настроек HyprPanel из его исходников.

    hyprpanel_extract.py <клон HyprPanel> [папка вывода]

Пишет в папку вывода (по умолчанию ../adapters/hyprpanel):
  options.json  — все <Option …/> окна настроек: вкладка, страница, заголовок раздела,
                  ключ config.json, название, подсказка, тип, min/max/шаг, варианты;
  defaults.json — стандартные значения всех ключей (из src/configuration);
  strings.json  — уникальные строки интерфейса; их переводы лежат в ru.json.

Код HyprPanel не запускается: исходники только читаются и разбираются.
После обновления HyprPanel: перезапустить скрипт и перевести новые строки
(build.py перечислит те, которых нет в ru.json).
"""
import json, re, sys, pathlib, collections

ROOT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else sys.exit(__doc__)
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path(__file__).parent.parent / 'adapters/hyprpanel'
SRC = ROOT / 'src'

# ------------------------------------------------------------------ окно настроек
def attrs(body):
    """Атрибуты JSX: name="…", name='…', name={…} (со вложенными скобками), name."""
    out, i = {}, 0
    while i < len(body):
        m = re.compile(r'\s*([A-Za-z_]\w*)(=)?').match(body, i)
        if not m or not m.group(1):
            i += 1
            continue
        name = m.group(1); i = m.end()
        if not m.group(2):
            out[name] = True
            continue
        c = body[i]
        if c in '"\'':
            j = body.index(c, i + 1); out[name] = body[i + 1:j]; i = j + 1
        elif c == '{':
            d, j = 0, i
            while True:
                ch = body[j]
                if ch in '"\'`':
                    j = body.index(ch, j + 1)
                elif ch == '{':
                    d += 1
                elif ch == '}':
                    d -= 1
                    if d == 0:
                        break
                j += 1
            out[name] = body[i + 1:j].strip(); i = j + 1
        else:
            i += 1
    return out


def jsval(x):
    """Литерал из атрибута: массив строк, строка (в т.ч. 'a' + 'b'), число; иначе — как есть."""
    if x is None or x is True:
        return x
    x = x.strip()
    if x.startswith('['):
        return [json.loads('"' + s[1:-1].replace('"', '\\"') + '"') for s in re.findall(r"'[^']*'|\"[^\"]*\"", x)]
    parts = re.findall(r"'((?:\\.|[^'])*)'|\"((?:\\.|[^\"])*)\"|`((?:\\.|[^`])*)`", x)
    if parts and re.fullmatch(r"\s*(?:(?:'(?:\\.|[^'])*'|\"(?:\\.|[^\"])*\"|`(?:\\.|[^`])*`)\s*\+?\s*)+", x):
        return ''.join(a or b or c for a, b, c in parts).replace('\\n', '\n').replace("\\'", "'")
    try:
        return float(x) if '.' in x else int(x)
    except ValueError:
        return x


TABS = {
    'config': ['src/components/settings/pages/config', 'src/components/bar/settings/config.tsx'],
    'theme': ['src/components/settings/pages/theme', 'src/components/bar/settings/theme.tsx'],
}
options = []
for tab, paths in TABS.items():
    files = []
    for p in paths:
        p = ROOT / p
        files += [p] if p.is_file() else sorted(p.rglob('*.tsx'))
    for f in files:
        s = f.read_text()
        if '<Option' not in s:
            continue
        pm = re.search(r"<scrollable[^>]*?name=\{?['\"]([^'\"]+)", s, re.S)
        page, hdr = (pm.group(1) if pm else f.stem), None
        for m in re.finditer(r'<Header\s+title=["\']([^"\']+)["\']\s*/>|<Option\b(.*?)/>\s*(?=[\n<{)])', s, re.S):
            if m.group(1):
                hdr = m.group(1)
                continue
            a = attrs(m.group(2)); opt = a.get('opt', '')
            if not opt.startswith('options.') or 'dummy' in opt:
                continue
            options.append(dict(tab=tab, page=page, header=hdr, key=opt[8:].strip(),
                                title=jsval(a.get('title')), subtitle=jsval(a.get('subtitle')),
                                link=jsval(a.get('subtitleLink')), type=jsval(a.get('type')),
                                min=jsval(a.get('min')), max=jsval(a.get('max')),
                                step=jsval(a.get('increment')), enums=jsval(a.get('enums'))))

# порядок страниц — как в helpers.ts
helpers = (SRC / 'components/settings/helpers.ts').read_text()
pages = {k: re.findall(r"'([^']+)'", re.search(rf'export const {k}Pages = \[(.*?)\]', helpers, re.S).group(1))
         for k in ('config', 'theme')}

# ------------------------------------------------------------------ умолчания
TOK = re.compile(r'''\s*(?:(//[^\n]*)|(/\*.*?\*/)|(`(?:\\.|[^`])*`)|("(?:\\.|[^"])*")|('(?:\\.|[^'])*')|(-?\d+(?:\.\d+)?)|(\.\.\.)|([A-Za-z_$][\w$]*)|(.))''', re.S)


def toks(s):
    out = []
    for m in TOK.finditer(s):
        if m.group(1) or m.group(2):
            continue
        for i, k in ((3, 'tpl'), (4, 'str'), (5, 'str'), (6, 'num'), (7, 'spread'), (8, 'id'), (9, 'p')):
            if m.group(i) is not None:
                v = m.group(i)
                if k == 'str':
                    v = json.loads('"' + v[1:-1].replace('"', '\\"').replace("\\'", "'") + '"')
                if k == 'tpl':
                    v = v[1:-1]
                out.append((k, v)); break
    return out


def resolve(frm, spec):
    p = SRC.parent / spec if spec.startswith('src/') else (frm.parent / spec).resolve()
    for c in (p.with_suffix('.ts'), p / 'index.ts'):
        if c.exists():
            return c


class Opt:
    def __init__(self, v): self.v = v


cache = {}


def load(path):
    if path in cache:
        return cache[path]
    s = path.read_text(); env = {}
    for m in re.finditer(r"import\s+(\w+)\s+from\s+'([^']+)'", s):
        p = resolve(path, m.group(2))
        if p: env[m.group(1)] = ('default', p)
    for m in re.finditer(r"import\s*\{([^}]*)\}\s*from\s*'([^']+)'", s):
        p = resolve(path, m.group(2))
        if p:
            for n in m.group(1).split(','):
                n = n.strip().split(' as ')[-1].strip()
                if n: env[n] = ('named', p, n)
    mod = {'default': None, 'named': {}}
    cache[path] = mod
    T = toks(s)
    for i, (k, v) in enumerate(T):
        if k == 'id' and v == 'export' and i + 1 < len(T):
            if T[i + 1] == ('id', 'default'):
                mod['default'] = Parser(T, i + 2, env).value()
            elif T[i + 1][1] in ('const', 'let') and T[i + 3] == ('p', '='):
                mod['named'][T[i + 2][1]] = Parser(T, i + 4, env).value()
    for i, (k, v) in enumerate(T):
        if k == 'id' and v == 'const' and i + 2 < len(T) and T[i + 2] == ('p', '=') \
                and T[i + 1][1] not in mod['named'] and (i == 0 or T[i - 1] != ('id', 'export')):
            try:
                env.setdefault(T[i + 1][1], ('value', Parser(T, i + 3, env).value()))
            except Exception:
                pass
    return mod


def ref(env, name):
    e = env.get(name)
    if not e: return None
    if e[0] == 'value': return e[1]
    m = load(e[1])
    return m['default'] if e[0] == 'default' else m['named'].get(e[2])


class Parser:
    def __init__(s, T, i, env): s.T, s.i, s.env = T, i, env
    def peek(s): return s.T[s.i] if s.i < len(s.T) else (None, None)
    def nxt(s): t = s.T[s.i]; s.i += 1; return t

    def skip_generic(s):
        if s.peek() == ('p', '<'):
            d = 0
            while True:
                t = s.nxt()
                if t == ('p', '<'): d += 1
                elif t == ('p', '>'):
                    d -= 1
                    if d == 0: break

    def value(s):
        k, v = s.peek()
        if (k, v) == ('p', '{'): return s.obj()
        if (k, v) == ('p', '['): return s.arr()
        if k in ('str', 'tpl', 'num'):
            s.nxt(); return (float(v) if '.' in v else int(v)) if k == 'num' else v
        if k == 'id':
            s.nxt()
            if v in ('true', 'false'): return v == 'true'
            if v == 'opt':
                s.skip_generic(); s.nxt()
                val = s.value(); d = 0
                while True:
                    t = s.nxt()
                    if t == ('p', '('): d += 1
                    elif t == ('p', ')'):
                        if d == 0: break
                        d -= 1
                return Opt(val)
            base = ref(s.env, v)
            while s.peek() == ('p', '.'):
                s.nxt(); n = s.nxt()[1]; base = base.get(n) if isinstance(base, dict) else None
            if s.peek() == ('id', 'as'):
                s.nxt(); s.nxt()
                while s.peek()[1] in ('[', ']'): s.nxt()
            return base
        s.nxt(); return None

    def arr(s):
        s.nxt(); out = []
        while s.peek() != ('p', ']'):
            out.append(s.value())
            if s.peek() == ('p', ','): s.nxt()
        s.nxt(); return out

    def obj(s):
        s.nxt(); out = {}
        while s.peek() != ('p', '}'):
            k, v = s.peek()
            if k == 'spread':
                s.nxt(); val = s.value()
                if isinstance(val, dict): out.update(val)
            else:
                s.nxt(); key = v
                if s.peek() == ('p', ':'):
                    s.nxt(); out[key] = s.value()
                else:
                    out[key] = ref(s.env, key)
            if s.peek() == ('p', ','): s.nxt()
        s.nxt(); return out


theme = load(SRC / 'configuration/modules/theme/index.ts')['default']
config = load(SRC / 'configuration/modules/config/index.ts')['default']
defaults = {}


def walk(o, p):
    if isinstance(o, Opt): defaults[p] = o.v
    elif isinstance(o, dict):
        for k, v in o.items(): walk(v, f'{p}.{k}' if p else k)


walk({'theme': theme, **config}, '')

# ------------------------------------------------------------------ строки для перевода
strings = ['Configuration', 'Theming']
for x in options:
    for s_ in (x['page'], x['header'], x['title']):
        if s_ and s_ not in strings: strings.append(s_)
for x in options:
    s_ = x['subtitle']
    if s_ and not s_.startswith('bind(') and s_ not in strings: strings.append(s_)

OUT.mkdir(parents=True, exist_ok=True)
dump = lambda name, obj: (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1) + '\n')
dump('options.json', {'pages': pages, 'options': options})
dump('defaults.json', defaults)
dump('strings.json', strings)
missing = [o['key'] for o in options if o['key'] not in defaults]
print(f'{len(options)} настроек на {sum(map(len, pages.values()))} страницах, {len(defaults)} умолчаний, '
      f'{len(strings)} строк; без умолчания: {len(missing)}')
print(collections.Counter(o['type'] for o in options).most_common())
