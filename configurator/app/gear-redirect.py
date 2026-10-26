#!/usr/bin/env python3
"""Шестерёнка HyprPanel → наши настройки.

Кнопка 󰒓 в панели управления HyprPanel зашита в его код и всегда открывает его окно
настроек (заголовок «hyprpanel-settings»). Код HyprPanel не трогаем: этот скрипт слушает
события Hyprland (socket2), и как только такое окно появляется — закрывает его и открывает
mors-settings. Закрытие окна HyprPanel только прячет его (delete-event → hide).

Если mors-settings сам просит открыть оригинальное окно, он создаёт файл-пропуск
~/.cache/mors-settings/allow-hyprpanel-settings — одно открытие в течение 10 с пропускается.

Запускается из автостарта Hyprland (config/hypr/lua/autostart.lua).
"""
import os, pathlib, socket, subprocess, sys, time

TITLE = 'hyprpanel-settings'
HERE = pathlib.Path(__file__).resolve().parent
SETTINGS = HERE / 'mors-settings'
BYPASS = pathlib.Path(os.environ.get('XDG_CACHE_HOME', pathlib.Path.home() / '.cache')) / 'mors-settings/allow-hyprpanel-settings'


def socket_path():
    sig = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
    if not sig:
        sys.exit('gear-redirect: не в сессии Hyprland')
    run = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
    for p in (f'{run}/hypr/{sig}/.socket2.sock', f'/tmp/hypr/{sig}/.socket2.sock'):
        if os.path.exists(p):
            return p
    sys.exit('gear-redirect: нет socket2 Hyprland')


def bypass_active():
    try:
        if time.time() - BYPASS.stat().st_mtime < 10:
            BYPASS.unlink(missing_ok=True)
            return True
    except FileNotFoundError:
        pass
    return False


def redirect(address):
    if bypass_active():
        return
    subprocess.run(['hyprctl', 'dispatch', 'closewindow', f'address:0x{address}'],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # подстраховка: если окно не закрылось — прячем его командой самого HyprPanel
    vis = subprocess.run(['hyprpanel', 'isWindowVisible', 'settings-dialog'], capture_output=True, text=True)
    if vis.stdout.strip() == 'true':
        subprocess.run(['hyprpanel', 'toggleWindow', 'settings-dialog'], stdout=subprocess.DEVNULL)
    subprocess.Popen([sys.executable, str(SETTINGS)], start_new_session=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


PIDFILE = BYPASS.parent / 'gear-redirect.pid'


def main():
    PIDFILE.parent.mkdir(parents=True, exist_ok=True)
    try:                                         # второй экземпляр не нужен
        os.kill(int(PIDFILE.read_text()), 0)
        sys.exit(0)
    except (OSError, ValueError):
        pass
    PIDFILE.write_text(str(os.getpid()))
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(socket_path())
    buf = b''
    while True:
        chunk = s.recv(4096)
        if not chunk:
            return                                   # Hyprland завершился
        buf += chunk
        *lines, buf = buf.split(b'\n')
        for line in lines:
            ev, _, data = line.decode(errors='replace').partition('>>')
            if ev == 'openwindow':
                address, _ws, _cls, title = (data.split(',', 3) + ['', '', ''])[:4]
                if title == TITLE:
                    redirect(address)


if __name__ == '__main__':
    main()
