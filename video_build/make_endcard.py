#!/usr/bin/env python3
"""End-card: flyer real del evento (datos del flyer de referencia) a 1620x2880.
Compone tipografía nítida sobre el arte generado (endcard_art.jpg)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math

CW, CH = 1620, 2880
FDIR = '/usr/share/fonts/truetype/dejavu'
SERIF = os.path.join(FDIR, 'DejaVuSerif-Bold.ttf')
SANS = os.path.join(FDIR, 'DejaVuSans-Bold.ttf')

art = Image.open('video_build/endcard_art.jpg').convert('RGB')
w, h = art.size
tgt = CW / CH
if w / h > tgt:
    nw = int(h * tgt); x = (w - nw) // 2; art = art.crop((x, 0, x + nw, h))
else:
    nh = int(w / tgt); y = (h - nh) // 2; art = art.crop((0, y, w, y + nh))
art = art.resize((CW, CH), Image.Resampling.LANCZOS)

# oscurece zona superior e inferior para legibilidad tipográfica
arr = np.asarray(art).astype(np.float32)
rows = np.linspace(0, 1, CH, dtype=np.float32)
band_top = 1 - 0.42 * np.clip((0.235 - rows) / 0.235, 0, 1) ** 1.4
band_bot = 1 - 0.52 * np.clip((rows - 0.70) / 0.30, 0, 1) ** 1.3
arr *= (band_top * band_bot)[:, None, None]
art = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

def text_masks(text, font, tracking, stroke_w):
    ws = [max(1.0, font.getlength(ch)) for ch in text]
    asc, desc = font.getmetrics()
    pad = stroke_w + 14
    wt = int(sum(ws) + tracking * (len(text) - 1) + 2 * pad) + 4
    ht = asc + desc + 2 * pad
    imS, imC = Image.new('L', (wt, ht), 0), Image.new('L', (wt, ht), 0)
    dS, dC = ImageDraw.Draw(imS), ImageDraw.Draw(imC)
    x = pad + 2
    for ch, wd in zip(text, ws):
        dS.text((x, pad), ch, font=font, fill=255, stroke_width=stroke_w, stroke_fill=255)
        dC.text((x, pad), ch, font=font, fill=255)
        x += wd + tracking
    aS, aC = np.asarray(imS), np.asarray(imC)
    ys, xs = np.where(aS > 6)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return aS[y0:y1, x0:x1], aC[y0:y1, x0:x1]

def grad_rgb(h, w, stops):
    pos = np.array([s[0] for s in stops]) * (h - 1)
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)
    for c in range(3):
        rgb[:, :, c] = np.interp(ys, pos, np.array([s[1][c] for s in stops], dtype=np.float32))[:, None]
    return rgb

def colorize(mS, mC, palette, stroke_col, stretch=1.0, glow_r=0, glow_col=(255,80,20), glow_amp=0.0):
    h0, w0 = mS.shape
    h1 = int(h0 * stretch)
    imS = Image.fromarray(mS).resize((w0, h1), Image.Resampling.BILINEAR)
    imC = Image.fromarray(mC).resize((w0, h1), Image.Resampling.BILINEAR)
    aS = np.asarray(imS).astype(np.float32) / 255.0
    aC = np.asarray(imC).astype(np.float32) / 255.0
    h, w = aS.shape
    rgb = grad_rgb(h, w, palette)
    stroke_only = (aS > 0.22) & (aC <= 0.22)
    rgb[stroke_only] = np.array(stroke_col, dtype=np.float32)
    glow = None
    if glow_r > 0 and glow_amp > 0:
        gimg = Image.fromarray((np.clip(aC, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(glow_r))
        g = np.asarray(gimg).astype(np.float32) / 255.0 * glow_amp
        glow = g[:, :, None] * np.array(glow_col, dtype=np.float32)[None, None, :]
    return rgb, aS, glow

def paste(base_np, rgb, alpha, cx=None, x=None, y=0, glow=None):
    h, w = alpha.shape
    x0 = (CW - w) // 2 if cx is None else cx
    if x is not None:
        x0 = x
    reg = base_np[y:y + h, x0:x0 + w]
    if glow is not None:
        reg += glow
    af = alpha[:, :, None]
    base_np[y:y + h, x0:x0 + w] = reg * (1 - af) + rgb * af
    return h

RED_TITLE = [(0.0, (255, 168, 110)), (0.22, (255, 72, 38)), (0.68, (205, 16, 16)), (1.0, (112, 0, 14))]
GOLD_RIM = (255, 198, 112)
MAGMA = [(0.0, (255, 232, 168)), (0.35, (255, 168, 60)), (0.7, (238, 84, 8)), (1.0, (150, 18, 0))]
BONE = [(0.0, (255, 244, 224)), (1.0, (214, 184, 148))]
GOLD = [(0.0, (255, 244, 190)), (0.5, (255, 205, 94)), (1.0, (198, 100, 14))]
SILVER = [(0.0, (240, 232, 222)), (1.0, (170, 154, 138))]

base = np.asarray(art).astype(np.float32)

# ---------------- Título ----------------
f1 = ImageFont.truetype(SERIF, 208)
mS, mC = text_masks('THE FIRE', f1, tracking=14, stroke_w=6)
rgb, a, glow = colorize(mS, mC, RED_TITLE, GOLD_RIM, stretch=1.24, glow_r=22, glow_col=(255, 70, 16), glow_amp=0.75)
h1 = paste(base, rgb, a, cx=None, y=64, glow=glow)

f2 = ImageFont.truetype(SERIF, 178)
mS, mC = text_masks('OF TERROR', f2, tracking=14, stroke_w=6)
rgb, a, glow = colorize(mS, mC, RED_TITLE, GOLD_RIM, stretch=1.24, glow_r=22, glow_col=(255, 70, 16), glow_amp=0.75)
paste(base, rgb, a, cx=None, y=64 + h1 - 26, glow=glow)

# ---------------- Placa REGGAETON VERSION ----------------
fp = ImageFont.truetype(SERIF, 58)
mS, mC = text_masks('REGGAETON VERSION', fp, tracking=10, stroke_w=1)
th, tw = mS.shape
px, py = 46, 22
pw, ph = tw + 2 * px, th + 2 * py
plq = Image.new('L', (pw, ph), 0)
ImageDraw.Draw(plq).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=16, fill=255, outline=120, width=3)
pa = np.asarray(plq).astype(np.float32) / 255.0
prgb = grad_rgb(ph, pw, [(0.0, (252, 232, 170)), (0.5, (236, 182, 92)), (1.0, (158, 96, 32))])
prgb *= (0.82 + 0.18 * (np.asarray(plq).astype(np.float32)[:, :, None] / 255.0))
# texto rojo oscuro encima
ta_full = np.zeros((ph, pw), dtype=np.float32)
ta_full[py:py + th, px:px + tw] = mC.astype(np.float32) / 255.0
ta_st = np.zeros((ph, pw), dtype=np.float32)
ta_st[py:py + th, px:px + tw] = mS.astype(np.float32) / 255.0
stroke_only = (ta_st > 0.3) & (ta_full <= 0.3)
trgb = np.zeros((ph, pw, 3), dtype=np.float32)
trgb[:] = np.array([96, 8, 4], dtype=np.float32)
trgb[stroke_only] = np.array([40, 2, 0], dtype=np.float32)
ta = ta_st
out_a = np.clip(pa + ta * (1 - pa), 0, 1)
out_rgb = (prgb * (pa * (1 - ta))[:, :, None] + trgb * ta[:, :, None]) / np.maximum(out_a, 1e-6)[:, :, None]
# sombra suave bajo la placa
sh = Image.fromarray((out_a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))
x0 = (CW - pw) // 2
y0 = 752
base[y0 + 8:y0 + 8 + ph, x0:x0 + pw] *= (1 - (np.asarray(sh).astype(np.float32) / 255.0)[:, :, None] * 0.55)
af = out_a[:, :, None]
base[y0:y0 + ph, x0:x0 + pw] = base[y0:y0 + ph, x0:x0 + pw] * (1 - af) + out_rgb * af

# ---------------- Pila de información ----------------
def line(text, size, palette, y, tracking=6, stroke_w=2, stroke_col=(30,2,0), font=SANS, glow_r=0, glow_amp=0.0, glow_col=(255,90,20)):
    f = ImageFont.truetype(font, size)
    mS, mC = text_masks(text, f, tracking=tracking, stroke_w=stroke_w)
    rgb, a, glow = colorize(mS, mC, palette, stroke_col, glow_r=glow_r, glow_amp=glow_amp, glow_col=glow_col)
    paste(base, rgb, a, cx=None, y=y, glow=glow)

line('31 DE OCTUBRE, DISCO EL EMPERADOR', 60, MAGMA, 2200, tracking=5, stroke_w=3,
     glow_r=14, glow_amp=0.5)
line('REGGAETON  ·  MERENGUE  ·  BACHATA Y MÁS', 38, BONE, 2322, tracking=8, stroke_w=2)
line('JESUS TORRES   •   KENN DJ   •   JESUS MADERO', 50, GOLD, 2390, tracking=6, stroke_w=2,
     glow_r=10, glow_amp=0.35, glow_col=(255, 140, 40))
line('(SPECIAL SET)', 32, SILVER, 2482, tracking=8, stroke_w=1)
line('PREMIOS A LOS 3 MEJORES DISFRACES', 36, BONE, 2546, tracking=6, stroke_w=2)
line('PRIMER LUGAR 300$', 56, GOLD, 2604, tracking=6, stroke_w=3,
     glow_r=12, glow_amp=0.5, glow_col=(255, 160, 40))
line('OPEN DOOR 9:00PM', 42, BONE, 2698, tracking=8, stroke_w=2)

# ---------------- Logos ----------------
dd = ImageDraw.Draw(art_rgb := Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)))
gold_col = (232, 190, 110)

def badge_star(cx, cy, r):
    dd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=gold_col, width=4)
    pts = []
    for i in range(5):
        ang = -math.pi / 2 + i * 4 * math.pi / 5   # une cada 2 vértices = pentagrama
        pts.append((cx + (r - 8) * math.cos(ang), cy + (r - 8) * math.sin(ang)))
    dd.line(pts + [pts[0]], fill=gold_col, width=3)

def badge_letter(cx, cy, r, letter):
    dd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=gold_col, width=4)
    dd.ellipse([cx - r + 9, cy - r + 9, cx + r - 9, cy + r - 9], outline=gold_col, width=1)
    f = ImageFont.truetype(SERIF, int(r * 1.1))
    bb = dd.textbbox((0, 0), letter, font=f)
    dd.text((cx - (bb[2] - bb[0]) / 2 - bb[0], cy - (bb[3] - bb[1]) / 2 - bb[1]),
            letter, font=f, fill=gold_col)

badge_star(190, 2795, 56)
badge_letter(1430, 2795, 56, 'E')

base = np.asarray(art_rgb).astype(np.float32)
fe = ImageFont.truetype(SANS, 30)
mS, mC = text_masks('ELEMENTS EVENTS', fe, tracking=6, stroke_w=1)
rgb, a, _ = colorize(mS, mC, SILVER, (20, 2, 0))
paste(base, rgb, a, x=272, y=2768)
mS, mC = text_masks('DISCO EL EMPERADOR', fe, tracking=6, stroke_w=1)
rgb, a, _ = colorize(mS, mC, SILVER, (20, 2, 0))
hw = a.shape[1]
paste(base, rgb, a, x=1348 - hw, y=2768)
f5 = ImageFont.truetype(SANS, 24)
mS, mC = text_masks('RIF J-502530000', f5, tracking=4, stroke_w=1)
rgb, a, _ = colorize(mS, mC, SILVER, (20, 2, 0))
hw = a.shape[1]
paste(base, rgb, a, x=1348 - hw, y=2818)

out = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
out.save('video_build/endcard.png')
# versión ligera para vista previa
out.resize((540, 960), Image.Resampling.LANCZOS).save('video_build/previews/endcard_preview.jpg', quality=90)
print('endcard.png OK', out.size)
