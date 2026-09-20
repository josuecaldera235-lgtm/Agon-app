#!/usr/bin/env python3
"""THE FIRE OF TERROR — render de video 1080x1920 @ 24fps, 30s.
Bloques: 1) macro zoom-out  2) orbital 180°  3) tilt descendente + shake
4) dolly-out a póster. Overlays: título ígneo, fecha magma, DJs, logos,
brasas, humo, flicker de vela, pulso de corazón, grano 70mm, viñeta,
flash final y fade a negro. Pipe rawvideo -> ffmpeg libx264.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import subprocess, time, os

FFMPEG = '/home/user/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2'
W, H = 1080, 1920
FPS, DUR = 24, 30.0
NF = int(FPS * DUR)
CW, CH = 1620, 2880          # lienzo con margen para pans/zooms
T_BLOCKS = (7.5, 15.0, 22.5)

rng = np.random.default_rng(13)

# ---------------------------------------------------------------- fuentes
FDIR = '/usr/share/fonts/truetype/dejavu'
FONT_SERIF = os.path.join(FDIR, 'DejaVuSerif-Bold.ttf')
FONT_SANS = os.path.join(FDIR, 'DejaVuSans-Bold.ttf')
if not os.path.exists(FONT_SANS):
    FONT_SANS = FONT_SERIF

# ---------------------------------------------------------------- fuentes de imagen
def load_src(path):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    tgt = W / H
    if w / h > tgt:
        nw = int(h * tgt); x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / tgt); y = max(0, (h - nh) // 3)
        im = im.crop((0, y, w, y + nh))
    return im.resize((CW, CH), Image.Resampling.LANCZOS)

SRCS = [load_src(f'video_build/key_block{i}.jpg') for i in (1, 2, 3, 4)]
END = Image.open('video_build/endcard.png').convert('RGB').resize((CW, CH), Image.Resampling.LANCZOS)
print('fuentes cargadas', [s.size for s in SRCS], '+ endcard', END.size, flush=True)

# ---------------------------------------------------------------- grading LUT (gótico cálido)
def curve(pts):
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return np.clip(np.interp(np.arange(256), xs, ys), 0, 255).astype(np.uint8)
LUT_R = curve([(0, 6), (40, 32), (96, 98), (160, 174), (210, 222), (255, 255)])
LUT_G = curve([(0, 2), (40, 26), (96, 92), (160, 160), (210, 208), (255, 246)])
LUT_B = curve([(0, 10), (40, 26), (96, 82), (160, 144), (210, 194), (255, 236)])

# ---------------------------------------------------------------- viñeta + bandas de legibilidad
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rx = (xx - W / 2) / (W / 2); ry = (yy - H / 2) / (H / 2)
rr = np.sqrt(rx ** 2 + ry ** 2) / np.sqrt(2.0)
VIG = np.clip(1.0 - 0.44 * (rr ** 2.1), 0.52, 1.0).astype(np.float32)

rows = np.linspace(0, 1, H, dtype=np.float32)
BAND_TOP = 1.0 - 0.20 * np.clip((0.16 - rows) / 0.16, 0, 1) ** 1.5
BAND_BOT = 1.0 - 0.30 * np.clip((rows - 0.60) / 0.40, 0, 1) ** 1.6

# ---------------------------------------------------------------- humo volumétrico (textura drifting)
_sm = Image.fromarray((rng.random((480, 1080)) * 255).astype(np.uint8)).filter(
    ImageFilter.GaussianBlur(46)).resize((W * 2, H), Image.Resampling.BILINEAR)
SMOKE = np.asarray(_sm, dtype=np.float32) / 255.0
SMOKE_TINT = np.array([1.0, 0.72, 0.45], dtype=np.float32)
SMOKE_ROW = (0.35 + 0.65 * rows[:, None]).astype(np.float32)

# ---------------------------------------------------------------- brasas / cenizas
N_EMB = 140
ex0 = rng.uniform(0, W, N_EMB)
ey0 = rng.uniform(0, H + 240, N_EMB)
evy = rng.uniform(26, 120, N_EMB)
eam = rng.uniform(4, 24, N_EMB)
efr = rng.uniform(0.05, 0.4, N_EMB)
eph = rng.uniform(0, 6.283, N_EMB)
etw = rng.uniform(2.0, 7.0, N_EMB)
ekind = rng.integers(0, 9, N_EMB)

def make_kernels():
    out = []
    for size in (5, 7, 11):
        c = (size - 1) / 2
        ay, ax = np.mgrid[0:size, 0:size].astype(np.float32)
        d2 = ((ax - c) ** 2 + (ay - c) ** 2) / (c * c + 1e-6)
        dot = np.clip(1.0 - d2, 0, 1) ** 2
        for col in ((255, 176, 70), (255, 110, 24), (255, 60, 8)):
            out.append((dot[:, :, None] * np.array(col, dtype=np.float32)[None, None, :]).astype(np.float32))
    return out
KERNS = make_kernels()

def ember_gain(t):
    g = 0.75
    if t > 15.0: g = 1.05
    if t > 22.5: g = 1.25
    if t > 28.55: g = 2.4 + (t - 28.55) * 3.0
    return g

def draw_embers(img, t):
    g = ember_gain(t)
    speed = 1.0 if t < 28.55 else 2.2
    ys = (ey0 - evy * t * speed) % (H + 240) - 120
    xs = ex0 + eam * np.sin(6.283 * efr * t + eph)
    tw = 0.5 + 0.5 * np.sin(etw * t + eph * 3.0)
    alphas = (0.30 + 0.70 * tw) * min(g, 2.0)
    for i in range(N_EMB):
        x = int(xs[i]); y = int(ys[i])
        k = KERNS[ekind[i]]
        kh, kw = k.shape[:2]
        x0, y0 = x - kw // 2, y - kh // 2
        sx0, sy0 = max(x0, 0), max(y0, 0)
        sx1, sy1 = min(x0 + kw, W), min(y0 + kh, H)
        if sx1 <= sx0 or sy1 <= sy0:
            continue
        kx0, ky0 = sx0 - x0, sy0 - y0
        img[sy0:sy1, sx0:sx1] += k[ky0:ky0 + (sy1 - sy0), kx0:kx0 + (sx1 - sx0)] * alphas[i] * 0.85

# ---------------------------------------------------------------- textos con gradiente ígneo
def render_mask(text, font, tracking, stroke_w):
    ws = [max(1.0, font.getlength(ch)) for ch in text]
    asc, desc = font.getmetrics()
    pad = stroke_w + 16
    wtot = int(sum(ws) + tracking * (len(text) - 1) + 2 * pad) + 4
    htot = asc + desc + 2 * pad
    imS = Image.new('L', (wtot, htot), 0)
    imC = Image.new('L', (wtot, htot), 0)
    dS, dC = ImageDraw.Draw(imS), ImageDraw.Draw(imC)
    x = pad + 2
    for ch, wd in zip(text, ws):
        dS.text((x, pad), ch, font=font, fill=255, stroke_width=stroke_w, stroke_fill=255)
        dC.text((x, pad), ch, font=font, fill=255)
        x += wd + tracking
    aS = np.asarray(imS)
    aC = np.asarray(imC)
    ys, xs = np.where(aS > 6)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    return aS[y0:y1, x0:x1].astype(np.float32) / 255.0, aC[y0:y1, x0:x1].astype(np.float32) / 255.0

def gradient_rgb(h, w, stops):
    pos = np.array([s[0] for s in stops]) * (h - 1)
    rgb = np.zeros((h, w, 3), dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)
    for c in range(3):
        col = np.array([s[1][c] for s in stops], dtype=np.float32)
        rgb[:, :, c] = np.interp(ys, pos, col)[:, None]
    return rgb

def make_item(text, size, palette, tracking, stroke_w, maxw, y,
              glow_r, glow_col, glow_amp, font_path=FONT_SERIF, rules=False):
    fs = size
    while True:
        font = ImageFont.truetype(font_path, fs)
        mS, mC = render_mask(text, font, tracking, stroke_w)
        if mS.shape[1] <= maxw or fs <= 22:
            break
        fs -= 3
    h, w = mS.shape
    rgb = gradient_rgb(h, w, palette)
    stroke_only = (mS > 0.25) & (mC <= 0.25)
    rgb[stroke_only] = np.array([34, 4, 2], dtype=np.float32)
    alpha = mS.copy()
    if rules:
        # líneas decorativas arriba/abajo (badges)
        h2 = h + 84
        rgb2 = np.zeros((h2, w, 3), dtype=np.float32)
        a2 = np.zeros((h2, w), dtype=np.float32)
        rgb2[42:42 + h] = rgb; a2[42:42 + h] = alpha
        line_w = int(w * 0.92); lx = (w - line_w) // 2
        for ly in (10, h + 72):
            a2[ly:ly + 2, lx:lx + line_w] = 0.85
            rgb2[ly:ly + 2] = np.array([212, 178, 128], dtype=np.float32)
        rgb, alpha, h = rgb2, a2, h2
    # brillo: desenfoque del NÚCLEO (no del borde) para fuego por letra
    if rules:
        core_full = np.zeros_like(alpha)
        core_full[42:42 + mC.shape[0], :] = mC
    else:
        core_full = mC
    core_src = np.maximum(core_full, alpha * 0.30)
    aimg = Image.fromarray((np.clip(core_src, 0, 1) * 255).astype(np.uint8))
    g1 = np.asarray(aimg.filter(ImageFilter.GaussianBlur(glow_r)), dtype=np.float32) / 255.0
    g2 = np.asarray(aimg.filter(ImageFilter.GaussianBlur(max(2, glow_r // 3))), dtype=np.float32) / 255.0
    gc = np.array(glow_col, dtype=np.float32)
    glow = ((g1 * 0.55 + g2 * 0.45) * glow_amp)[:, :, None] * gc[None, None, :]
    return {'rgb': rgb, 'a': alpha, 'glow': glow, 'w': w, 'h': h,
            'x': (W - w) // 2, 'y': y}

FIRE = [(0.0, (255, 246, 200)), (0.30, (255, 205, 92)), (0.62, (255, 122, 16)),
        (0.86, (196, 40, 0)), (1.0, (110, 12, 0))]
MAGMA = [(0.0, (255, 232, 168)), (0.35, (255, 168, 60)), (0.7, (238, 84, 8)),
         (1.0, (140, 16, 0))]
BONE = [(0.0, (255, 244, 224)), (1.0, (216, 186, 150))]
SILVER = [(0.0, (238, 230, 218)), (1.0, (168, 152, 136))]
GOLDBONE = [(0.0, (255, 240, 200)), (1.0, (228, 168, 88))]

def make_plaque(text, size, maxw, y, tracking=10, glow_amp=0.5):
    """Placa dorada con texto rojo oscuro (banner REGGAETON VERSION)."""
    fs = size
    while True:
        font = ImageFont.truetype(FONT_SERIF, fs)
        mS, mC = render_mask(text, font, tracking, 1)
        if mS.shape[1] <= maxw or fs <= 18:
            break
        fs -= 2
    th, tw = mS.shape
    px, py = 30, 14
    pw, ph = tw + 2 * px, th + 2 * py
    plq = Image.new('L', (pw, ph), 0)
    ImageDraw.Draw(plq).rounded_rectangle([0, 0, pw - 1, ph - 1], radius=11,
                                          fill=255, outline=120, width=2)
    pa = np.asarray(plq).astype(np.float32) / 255.0
    prgb = np.zeros((ph, pw, 3), dtype=np.float32)
    ys = np.arange(ph, dtype=np.float32)
    for c, stops in enumerate([(252, 236, 158), (232, 182, 96), (170, 90, 32)]):
        prgb[:, :, c] = np.interp(ys, [0, ph * 0.5, ph - 1], stops)[:, None]
    prgb *= (0.84 + 0.16 * (pa[:, :, None]))
    ta = np.zeros((ph, pw), dtype=np.float32)
    ta[py:py + th, px:px + tw] = mS
    tc = np.zeros((ph, pw), dtype=np.float32)
    tc[py:py + th, px:px + tw] = mC
    trgb = np.zeros((ph, pw, 3), dtype=np.float32)
    trgb[:] = np.array([96, 8, 4], dtype=np.float32)
    out_a = np.clip(pa + ta * (1 - pa), 0, 1)
    out_rgb = (prgb * (pa * (1 - ta))[:, :, None] + trgb * ta[:, :, None]) / np.maximum(out_a, 1e-6)[:, :, None]
    aimg = Image.fromarray((out_a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10))
    glow = (np.asarray(aimg).astype(np.float32) / 255.0 * glow_amp)[:, :, None] * np.array((255, 110, 25), dtype=np.float32)[None, None, :]
    return {'rgb': out_rgb, 'a': out_a, 'glow': glow, 'w': pw, 'h': ph,
            'x': (W - pw) // 2, 'y': y}

print('renderizando textos...', flush=True)
TITLE = make_item('THE FIRE OF TERROR', 92, FIRE, tracking=7, stroke_w=4,
                  maxw=1000, y=252, glow_r=18, glow_col=(255, 96, 14), glow_amp=0.62)
BANNER = make_plaque('REGGAETON VERSION', 48, 880, y=352, tracking=10, glow_amp=0.55)
DATE = make_item('31 DE OCTUBRE', 72, MAGMA, tracking=10, stroke_w=3,
                 maxw=940, y=1396, glow_r=13, glow_col=(255, 80, 10), glow_amp=0.55)
VENUE = make_item('DISCO EL EMPERADOR', 42, GOLDBONE, tracking=8, stroke_w=2,
                  maxw=900, y=1486, glow_r=9, glow_col=(255, 120, 30), glow_amp=0.45,
                  font_path=FONT_SANS)
DJS = make_item('JESUS TORRES • KENN DJ • JESUS MADERO', 38, BONE, tracking=8,
                stroke_w=1, maxw=980, y=1558, glow_r=10, glow_col=(255, 120, 30), glow_amp=0.5,
                font_path=FONT_SANS)
SPECIAL = make_item('(SPECIAL SET)', 26, SILVER, tracking=6, stroke_w=1,
                    maxw=900, y=1620, glow_r=6, glow_col=(255, 110, 30), glow_amp=0.3,
                    font_path=FONT_SANS)
EXTRA = make_item('PREMIOS: PRIMER LUGAR 300$ • OPEN DOOR 9:00PM', 26, BONE,
                  tracking=5, stroke_w=1, maxw=1010, y=1666, glow_r=6,
                  glow_col=(255, 110, 30), glow_amp=0.3, font_path=FONT_SANS)
LOGOS = make_item('ELEMENTS EVENTS  •  DISCO EL EMPERADOR', 26, SILVER,
                  tracking=6, stroke_w=0, maxw=960, y=1718, glow_r=8,
                  glow_col=(255, 110, 30), glow_amp=0.35, font_path=FONT_SANS, rules=True)
print('textos OK:', [(it['w'], it['h']) for it in (TITLE, BANNER, DATE, VENUE, DJS, SPECIAL, EXTRA, LOGOS)], flush=True)

def composite_item(img, it, alpha_scale, dy=0.0, glow_scale=1.0):
    if alpha_scale <= 0.004:
        return
    y0 = int(it['y'] + dy); x0 = it['x']; h = it['h']; w = it['w']
    if y0 + h <= 0 or y0 >= H:
        return
    sy0, sy1 = max(0, y0), min(H, y0 + h)
    ky0 = sy0 - y0
    reg = img[sy0:sy1, x0:x0 + w]
    reg += it['glow'][ky0:ky0 + (sy1 - sy0)] * glow_scale
    af = (it['a'][ky0:ky0 + (sy1 - sy0)] * alpha_scale)[:, :, None]
    reg *= (1.0 - af)
    reg += it['rgb'][ky0:ky0 + (sy1 - sy0)] * af

# ---------------------------------------------------------------- cámaras
def ease_io(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)

def ease_io_cubic(u):
    u = min(max(u, 0.0), 1.0)
    return 4 * u * u * u if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2

def ease_out(u):
    u = min(max(u, 0.0), 1.0)
    return 1 - (1 - u) ** 3

def cam_box(seg, t):
    """Devuelve caja (l, u, r, d) en el lienzo CWxCH."""
    starts = (0.0, 7.5, 15.0, 22.5)
    u = (t - starts[seg]) / 7.5
    ts = t - starts[seg]
    if seg == 0:                                   # macro zoom-out con retroceso
        e = ease_io_cubic(u)
        s = 1.38 - 0.38 * e
        cx = CW * (0.30 + 0.20 * e)
        cy = CH * (0.395 + 0.105 * e)
    elif seg == 1:                                 # paneo orbital 180°
        s = 1.17 - 0.09 * ease_io(u)
        pan = ease_io(u)
        cw_ = CW / s
        mgx = (CW - cw_) * 0.5 * 0.9
        cx = CW / 2 + mgx * (2 * pan - 1)
        cy = CH * (0.52 - 0.045 * np.sin(np.pi * min(max(u, 0), 1)))
    elif seg == 2:                                 # tilt descendente + vibración
        s = 1.26 - 0.08 * ease_out(u)
        vv = ease_io(u)
        cx = CW * 0.5
        cy = CH * (0.34 + 0.30 * vv)
        if ts < 1.5:                               # sacudida sísmica
            amp = 11 * np.exp(-ts * 2.4)
            cx += rng.uniform(-1, 1) * amp
            cy += rng.uniform(-1, 1) * amp * 0.6
        else:
            cx += rng.uniform(-1, 1) * 1.4
            cy += rng.uniform(-1, 1) * 1.0
    else:                                          # dolly-out a póster fijo
        e = ease_io(min(u / 0.52, 1.0))
        s = 1.15 - 0.15 * e
        cx = CW * 0.5
        cy = CH * (0.5 - 0.018 * e)
    cw_, ch_ = CW / s, CH / s
    l = min(max(cx - cw_ / 2, 0), CW - cw_)
    up = min(max(cy - ch_ / 2, 0), CH - ch_)
    return int(l), int(up), int(l + cw_), int(up + ch_)

SEG_IDX = lambda t: 0 if t < 7.5 else (1 if t < 15.0 else (2 if t < 22.5 else 3))

T_XF0, T_XF1 = 24.9, 25.7          # fundido hacia el flyer real

def endcard_box(t):
    """Push-in lento sobre el flyer final (póster estático animado)."""
    s = 1.0 + 0.05 * ease_io(min(max((t - T_XF1) / 4.2, 0.0), 1.0))
    cw_, ch_ = CW / s, CH / s
    l = (CW - cw_) / 2
    up = (CH - ch_) / 2
    return int(l), int(up), int(l + cw_), int(up + ch_)

def overlay_fade(t):
    if t < T_XF0:
        return 1.0
    u = min(max((t - T_XF0) / (T_XF1 - T_XF0), 0.0), 1.0)
    return 1.0 - (u * u * (3 - 2 * u))

def base_frame(t):
    seg = SEG_IDX(t)
    box = cam_box(seg, t)
    img = SRCS[seg].crop(box).resize((W, H), Image.Resampling.LANCZOS)
    a = np.asarray(img, dtype=np.uint8)
    fl = np.empty((H, W, 3), dtype=np.float32)
    fl[:, :, 0] = LUT_R[a[:, :, 0]]
    fl[:, :, 1] = LUT_G[a[:, :, 1]]
    fl[:, :, 2] = LUT_B[a[:, :, 2]]
    # fundido hacia la end-card (flyer real) en el bloque 4
    if seg == 3 and t > T_XF0:
        al = overlay_fade(t)          # 1 -> 0
        w_ = 1.0 - al
        e = np.asarray(END.crop(endcard_box(t)).resize((W, H), Image.Resampling.LANCZOS), dtype=np.uint8)
        fl[:, :, 0] = fl[:, :, 0] * al + LUT_R[e[:, :, 0]] * w_
        fl[:, :, 1] = fl[:, :, 1] * al + LUT_G[e[:, :, 1]] * w_
        fl[:, :, 2] = fl[:, :, 2] * al + LUT_B[e[:, :, 2]] * w_
        return fl
    # fundido corto entre bloques
    for tb in T_BLOCKS:
        dt = t - tb
        if -0.02 < dt < 0.22 and seg > 0:
            al = dt / 0.22
            al = al * al * (3 - 2 * al)
            boxp = cam_box(seg - 1, t)
            prev = SRCS[seg - 1].crop(boxp).resize((W, H), Image.Resampling.LANCZOS)
            ap = np.asarray(prev, dtype=np.uint8)
            fl[:, :, 0] = fl[:, :, 0] * al + LUT_R[ap[:, :, 0]] * (1 - al)
            fl[:, :, 1] = fl[:, :, 1] * al + LUT_G[ap[:, :, 1]] * (1 - al)
            fl[:, :, 2] = fl[:, :, 2] * al + LUT_B[ap[:, :, 2]] * (1 - al)
            break
    return fl

# ---------------------------------------------------------------- bucle principal
def alpha_window(t, t0, t1):
    if t < t0:
        return 0.0, 0.0
    u = min((t - t0) / (t1 - t0), 1.0)
    return ease_out(u), 1 - ease_out(u)

proc = subprocess.Popen(
    [FFMPEG, '-y', '-loglevel', 'error',
     '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '24', '-i', '-',
     '-an', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
     '-pix_fmt', 'yuv420p', '-movflags', '+faststart', 'video_build/silent.mp4'],
    stdin=subprocess.PIPE)

t_start = time.time()
for fi in range(NF):
    t = fi / FPS
    img = base_frame(t)

    # flicker cálido (vela / lava)
    fl = 1.0 + 0.026 * np.sin(6.283 * 2.1 * t) + 0.020 * np.sin(6.283 * 6.7 * t + 1.0) \
            + 0.012 * np.sin(6.283 * 13.9 * t + 2.5)
    img *= fl

    # humo drifting
    xoff = int(t * 16) % W
    img += (SMOKE[:, xoff:xoff + W] * SMOKE_ROW)[:, :, None] * SMOKE_TINT[None, None, :] * 9.0

    # pulso del corazón de rubí (post 22.5, hasta que aparece el flyer)
    if 22.5 < t < T_XF1:
        p = max(0.0, np.sin(6.283 * 1.15 * (t - 22.5))) ** 1.6
        img[:, :, 0] *= 1 + 0.05 * p
        img[:, :, 1] *= 1 + 0.012 * p

    # brasas
    draw_embers(img, t)

    # ---------- textos (se funden al aparecer el flyer real) ----------
    ov = overlay_fade(t)
    if ov > 0.01:
        # título: cae del cielo 8.30 -> 9.40, flicker, pulso posterior
        aT, dA = alpha_window(t, 8.30, 9.40)
        aT *= ov
        if aT > 0:
            dy = -170 * dA
            flick = 0.965 + 0.035 * np.sin(6.283 * 8.1 * t) + 0.02 * rng.uniform(-1, 1)
            glow = 1.0 + dA * 1.6
            if 22.5 < t < T_XF1:
                glow += 0.55 * (max(0.0, np.sin(6.283 * 1.15 * (t - 22.5))) ** 1.6)
            composite_item(img, TITLE, min(1.0, aT * flick), dy, glow)
            img *= (BAND_TOP[:, None, None] * aT + (1 - aT))
        # banner REGGAETON VERSION: 9.70 -> 10.45
        aN, dN = alpha_window(t, 9.70, 10.45)
        aN *= ov
        if aN > 0:
            composite_item(img, BANNER, aN, -28 * dN, 0.9 + dN * 1.2)
        # fecha magma: brota 15.90 -> 17.10
        aD, dD = alpha_window(t, 15.90, 17.10)
        aD *= ov
        if aD > 0:
            g = 0.9 + dD * 1.5
            if 22.5 < t < T_XF1:
                g += 0.30 * (max(0.0, np.sin(6.283 * 1.15 * (t - 22.5))) ** 1.6)
            composite_item(img, DATE, aD, 110 * dD, g)
        # venue
        aV, dV = alpha_window(t, 16.05, 17.25)
        aV *= ov
        if aV > 0:
            composite_item(img, VENUE, aV, 80 * dV, 0.6)
        # DJs
        aJ, dJ = alpha_window(t, 16.15, 17.35)
        aJ *= ov
        if aJ > 0:
            composite_item(img, DJS, aJ, 70 * dJ, 0.55)
        # special set
        aS, dS = alpha_window(t, 16.35, 17.55)
        aS *= ov
        if aS > 0:
            composite_item(img, SPECIAL, aS, 40 * dS, 0.4)
        # premios / open door
        aX, _ = alpha_window(t, 23.25, 24.25)
        aX *= ov
        if aX > 0:
            composite_item(img, EXTRA, aX, 0.0, 0.35)
        # logos inferiores
        aL, _ = alpha_window(t, 23.20, 24.20)
        aL *= ov
        if aL > 0:
            composite_item(img, LOGOS, aL, 0.0, 0.35)
        # banda inferior de legibilidad cuando hay textos abajo
        aB = max(aD, aJ, aL, aV, aX)
        if aB > 0:
            img *= (BAND_BOT[:, None, None] * min(aB, 1.0) + (1 - min(aB, 1.0)))

    # flash ígneo final
    if t > 28.55:
        fsh = np.exp(-(t - 28.55) * 6.0)
        img += np.array([255, 196, 118], dtype=np.float32)[None, None, :] * fsh * 0.85

    # viñeta
    img *= VIG[:, :, None]

    # fades
    if t < 0.5:
        img *= (t / 0.5)
    if t > 29.0:
        img *= max(0.0, np.cos((t - 29.0) / 1.0 * np.pi / 2) ** 1.3)

    # grano IMAX 70mm
    img += rng.standard_normal((H, W, 1), dtype=np.float32) * 5.5

    proc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())

    if fi % 48 == 0:
        el = time.time() - t_start
        print(f'frame {fi}/{NF}  {el:.0f}s  eta {el / max(fi, 1) * (NF - fi):.0f}s', flush=True)

proc.stdin.close()
proc.wait()
print('silent.mp4 OK', proc.returncode, flush=True)
