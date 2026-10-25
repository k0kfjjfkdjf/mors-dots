#!/usr/bin/env python3
"""Расставляет мониторы на экране входа SDDM (X11) по названию модели из EDID,
а не по имени порта — перестановка кабелей ничего не ломает.
Ошибки только пишутся в лог; вход в систему они не блокируют."""
import re, subprocess, sys

# (кусок имени модели из EDID, режим, частота, позиция, основной)
LAYOUT = [
    ("FP93G",   "1280x1024", "75", "0x0",    False),  # BenQ — слева
    ("MKF23F",  "1920x1080", "60", "1280x0", True),   # MKG — по центру, тут форма входа
    ("SAMSUNG", "1920x1080", "60", "3200x0", False),  # Samsung TV — справа
]

def edid_name(hexstr):
    b = bytes.fromhex(hexstr)
    for off in (54, 72, 90, 108):
        d = b[off:off + 18]
        if len(d) == 18 and d[:3] == b"\0\0\0" and d[3] == 0xFC:
            return d[5:].split(b"\n")[0].decode("ascii", "ignore").strip()
    return ""

def outputs():
    txt = subprocess.run(["xrandr", "--props"], capture_output=True, text=True).stdout
    res, cur, edid, grab = {}, None, "", False
    for line in txt.splitlines():
        m = re.match(r"^(\S+) (connected|disconnected)", line)
        if m:
            if cur and edid: res[cur] = edid_name(edid)
            cur = m.group(1) if m.group(2) == "connected" else None
            edid, grab = "", False
            continue
        if cur is None: continue
        if line.strip() == "EDID:":
            grab = True; continue
        if grab:
            if re.fullmatch(r"\s+[0-9a-fA-F]+", line): edid += line.strip()
            else: grab = False
    if cur and edid: res[cur] = edid_name(edid)
    return res

def main():
    found = outputs()
    print("sddm-monitors: найдено", found, file=sys.stderr)
    cmd = ["xrandr"]
    for key, mode, rate, pos, primary in LAYOUT:
        out = next((o for o, n in found.items() if key.lower() in n.lower()), None)
        if not out:
            print(f"sddm-monitors: не найден {key}", file=sys.stderr); continue
        cmd += ["--output", out, "--mode", mode, "--rate", rate, "--pos", pos]
        if primary: cmd.append("--primary")
    if len(cmd) > 1:
        r = subprocess.run(cmd, capture_output=True, text=True)
        print("sddm-monitors:", " ".join(cmd), r.stderr.strip(), file=sys.stderr)

if __name__ == "__main__":
    try: main()
    except Exception as e: print("sddm-monitors: ошибка", e, file=sys.stderr)
    sys.exit(0)
