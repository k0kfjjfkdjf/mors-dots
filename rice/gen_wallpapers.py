import numpy as np
from PIL import Image, ImageFilter
W, H = 2560, 1440
rng = np.random.default_rng(7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
X, Y = xx / W, yy / H

def hexrgb(h): h = h.lstrip('#'); return np.array([int(h[i:i+2], 16) for i in (0, 2, 4)], np.float32) / 255

def blob(cx, cy, r, sx=1.0, sy=1.0):
    d = ((X - cx) / sx) ** 2 + ((Y - cy) * H / W / sy) ** 2
    return np.exp(-d / (2 * r * r))

def grain(img, amt):
    n = rng.normal(0, amt, (H, W, 1)).astype(np.float32)
    return img + n

def save(img, name):
    img = np.clip(img, 0, 1) ** (1 / 1.0)
    Image.fromarray((img * 255).astype(np.uint8)).save(f"wallpapers/{name}.png", optimize=True)

def vgrad(top, bottom):
    t = Y[..., None]
    return hexrgb(top) * (1 - t) + hexrgb(bottom) * t

# ---------- mono: графит, мягкий свет и тонкие дуги ----------
img = vgrad("#161616", "#060606")
img += blob(0.72, 0.30, 0.22)[..., None] * 0.10
img += blob(0.20, 0.85, 0.30)[..., None] * 0.05
r = np.sqrt(((X - 0.72) * W / H) ** 2 + (Y - 0.30) ** 2)
for k, rad in enumerate([0.32, 0.46, 0.63, 0.84]):
    ring = np.exp(-((r - rad) ** 2) / (2 * 0.0011 ** 2)) * (0.10 - k * 0.02)
    img += ring[..., None]
save(grain(img, 0.012), "mono")

# ---------- sakura: тёмная слива, розовые и лиловые свечения ----------
img = vgrad("#1f1520", "#0f0a10")
for cx, cy, rad, col, a in [
    (0.80, 0.20, 0.10, "#f5a9c8", 0.42), (0.66, 0.74, 0.13, "#e3b3e8", 0.20),
    (0.12, 0.28, 0.11, "#f9c6d3", 0.14), (0.36, 1.02, 0.15, "#f2849e", 0.16),
]:
    img += blob(cx, cy, rad)[..., None] * hexrgb(col) * a
# лепестки — мелкие размытые точки
pet = np.zeros((H, W), np.float32)
for _ in range(90):
    x, y = rng.uniform(0, W), rng.uniform(0, H)
    s = rng.uniform(2, 7)
    x0, x1, y0, y1 = int(max(0, x - 30)), int(min(W, x + 30)), int(max(0, y - 30)), int(min(H, y + 30))
    pet[y0:y1, x0:x1] += np.exp(-(((xx[y0:y1, x0:x1] - x) ** 2) / (2 * s * s) + ((yy[y0:y1, x0:x1] - y) ** 2) / (2 * (s * 0.6) ** 2))) * rng.uniform(0.15, 0.5)
img += np.clip(pet, 0, 1)[..., None] * hexrgb("#ffd6e6") * 0.45
save(grain(img, 0.010), "sakura")

# ---------- aurora: тёмно-синее небо, ленты сине-фиолетово-зелёного сияния ----------
img = vgrad("#0a0f2a", "#04060f")
def band(phase, amp, freq, y0, width):
    c = y0 + amp * np.sin(2 * np.pi * (X * freq + phase)) + 0.025 * np.sin(2 * np.pi * (X * 3.1 + phase * 2))
    d = Y - c
    # снизу резкий край, вверх — длинный «занавес»
    prof = np.where(d > 0, np.exp(-(d ** 2) / (2 * (width * 0.35) ** 2)), np.exp(-(d ** 2) / (2 * (width * 2.6) ** 2)))
    n1 = np.interp(X[0], np.linspace(0, 1, 260), rng.uniform(0, 1, 260))
    n1 = np.convolve(n1, np.ones(9) / 9, mode="same")
    curtain = (0.6 + 0.4 * n1)[None, :] * (0.85 + 0.15 * np.sin(X * 37 + phase * 9))
    return prof * curtain
for ph, amp, fr, y0, wdt, col, a in [
    (0.10, 0.06, 0.9, 0.46, 0.030, "#5cf2a6", 0.55),
    (0.35, 0.07, 0.7, 0.36, 0.035, "#5c7cff", 0.55),
    (0.60, 0.05, 1.1, 0.27, 0.030, "#a77bff", 0.50),
]:
    b = band(ph, amp, fr, y0, wdt) * (0.25 + 0.75 * blob(0.55, 0.32, 0.40, 1.6, 1))
    img += b[..., None] * hexrgb(col) * a
img = np.array(Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
# звёзды
stars = np.zeros((H, W), np.float32)
n = 900
sx, sy = rng.integers(0, W, n), rng.integers(0, int(H * 0.75), n)
stars[sy, sx] = rng.uniform(0.3, 1.0, n) ** 3
stars = np.array(Image.fromarray((stars * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255 * 3
img += stars[..., None] * hexrgb("#eef1ff")
img += blob(0.5, 1.15, 0.35, 2, 1)[..., None] * hexrgb("#5c7cff") * 0.15
save(grain(img, 0.008), "aurora")
print("done")
