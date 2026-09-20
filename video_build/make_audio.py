#!/usr/bin/env python3
"""THE FIRE OF TERROR — banda sonora sintetizada.
Dark cinematic reggaeton/trap híbrido 92 BPM con SFX según el JSON:
viento helado, lava lejana, crepitar de vela, truenos, whoosh de guadaña,
fractura sísmica, dembow que entra gradualmente, clímax y explosión final.
"""
import numpy as np
import wave
import os

SR = 44100
DUR = 30.0
N = int(SR * DUR)
rng = np.random.default_rng(666)

L = np.zeros(N, dtype=np.float64)
R = np.zeros(N, dtype=np.float64)

def put(sig, t0, amp=1.0, pan=0.5):
    """Inserta sig (mono) en el campo estéreo. pan 0=L, 1=R."""
    i0 = int(t0 * SR)
    if i0 >= N:
        return
    seg = sig[: max(0, min(len(sig), N - i0))]
    if len(seg) == 0:
        return
    gl = np.sqrt(1 - pan)
    gr = np.sqrt(pan)
    L[i0:i0 + len(seg)] += seg * amp * gl
    R[i0:i0 + len(seg)] += seg * amp * gr

def put_stereo(lsig, rsig, t0, amp=1.0):
    i0 = int(t0 * SR)
    n = min(len(lsig), N - i0)
    if n <= 0:
        return
    L[i0:i0 + n] += lsig[:n] * amp
    R[i0:i0 + n] += rsig[:n] * amp

def exp_env(n, attack=0.005, decay=0.3):
    t = np.arange(n) / SR
    a = np.minimum(t / max(attack, 1e-4), 1.0)
    return a * np.exp(-t / max(decay, 1e-3))

def lowpass(x, alpha):
    """Filtro un polo (alpha ~0.01..0.3)."""
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += alpha * (x[i] - acc)
        y[i] = acc
    return y

def fast_lowpass(x, taps):
    k = np.ones(taps) / taps
    return np.convolve(x, k, mode='same')

def brown_noise(n):
    w = rng.standard_normal(n)
    b = np.cumsum(w)
    b = b - np.linspace(b[0], b[-1], n)
    b /= (np.max(np.abs(b)) + 1e-9)
    return b

def sine_sweep(f0, f1, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    # frecuencia descendiendo exponencialmente
    k = np.log(f1 / f0)
    phase = 2 * np.pi * f0 * (np.exp(k * t / dur) - 1) * dur / k
    return np.sin(phase)

# ============================================================
# 1) CAMAS AMBIENTALES (0-30s)
# ============================================================
# Viento helado sibilante: ruido marrón filtrado, modulado lento
n_wind = N
wind_l = fast_lowpass(brown_noise(n_wind), 900)
wind_r = fast_lowpass(brown_noise(n_wind), 900)
t_all = np.arange(N) / SR
wind_mod = 0.55 + 0.30 * np.sin(2 * np.pi * 0.07 * t_all) + 0.15 * np.sin(2 * np.pi * 0.19 * t_all + 1.3)
sibil = fast_lowpass(rng.standard_normal(N), 60) - fast_lowpass(rng.standard_normal(N), 400)
wind_l = wind_l * wind_mod + lowpass(sibil, 0.09) * wind_mod * 0.6
wind_r = wind_r * wind_mod + lowpass(sibil[::-1].copy(), 0.09) * wind_mod * 0.6
wl = wind_l / (np.max(np.abs(wind_l)) + 1e-9)
wr = wind_r / (np.max(np.abs(wind_r)) + 1e-9)
put_stereo(wl, wr, 0.0, amp=0.16)

# Drone sub 30Hz amenazante con wobble
drone = np.sin(2 * np.pi * (30 + 1.5 * np.sin(2 * np.pi * 0.11 * t_all)) * t_all)
drone += 0.4 * np.sin(2 * np.pi * 45.3 * t_all)
put_stereo(drone, drone, 0.0, amp=0.10)

# Rugido de magma: ruido grave que CRECE (bloque 2 crescendo, bloques 3-4 fuerte)
lava = fast_lowpass(brown_noise(N), 500)
lava_env = np.ones(N) * 0.25
i75, i15, i225 = int(7.5 * SR), int(15 * SR), int(22.5 * SR)
lava_env[:i75] = 0.25
lava_env[i75:i15] = np.linspace(0.25, 1.0, i15 - i75)          # "rugido de magma creciente"
lava_env[i15:] = np.linspace(1.0, 1.35, N - i15)               # lava activa
lava_env[int(28.9 * SR):] *= np.linspace(1, 0.12, N - int(28.9 * SR))
lava = lava * lava_env
put_stereo(lava, np.roll(lava, 4000), 0.0, amp=0.13)

# ============================================================
# 2) SFX BLOQUE 1 (0-7.5): truenos distantes + crepitar de vela
# ============================================================
def thunder(t0, amp):
    n = int(2.4 * SR)
    th = fast_lowpass(brown_noise(n), 1400)
    e = exp_env(n, attack=0.06, decay=0.55)
    thump = np.sin(2 * np.pi * 48 * np.arange(n) / SR) * exp_env(n, 0.01, 0.22) * 0.7
    sig = th * e + thump
    put(sig, t0, amp, pan=0.35)
    put(sig * 0.5, t0 + 0.45, amp * 0.5, pan=0.6)   # eco lejano

thunder(2.2, 0.55)
thunder(5.8, 0.38)

def crackle(t0, t1, rate, amp, bright=False):
    n_burst = int(0.004 * SR) if bright else int(0.002 * SR)
    times = []
    t = t0
    while t < t1:
        t += rng.exponential(1.0 / rate)
        times.append(t)
    for tc in times:
        b = rng.standard_normal(n_burst) * np.hanning(n_burst)
        put(b, tc, amp * rng.uniform(0.4, 1.0), pan=rng.uniform(0.3, 0.7))

crackle(0.2, 7.4, rate=3.5, amp=0.06)          # vela
# ============================================================
# 3) SFX BLOQUE 2 (7.5-15): whoosh guadaña + fuego del título
# ============================================================
def whoosh(t0, dur=0.7, amp=0.5, pan_from=0.2, pan_to=0.8):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    mod = sine_sweep(3200, 500, dur)          # barrido aire->metal
    ring = noise * mod
    ring = fast_lowpass(np.abs(ring), 25) * np.sign(ring)
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    sig = ring * e / (np.max(np.abs(ring * e)) + 1e-9)
    nn = 24
    # paneo L->R
    for i in range(nn):
        a = i / nn
        put(sig[i * n // nn:(i + 1) * n // nn], t0 + a * dur, amp,
            pan=pan_from + (pan_to - pan_from) * a)

whoosh(8.0, dur=0.75, amp=0.55)                      # alza la guadaña
crackle(8.4, 15.0, rate=9, amp=0.07, bright=True)    # título en fuego

# ============================================================
# 4) SFX BLOQUE 3 (15-22.5): fractura sísmica + corte de aire
# ============================================================
def rock_fracture(t0, amp=0.9):
    n = int(0.9 * SR)
    crack = rng.standard_normal(n) * exp_env(n, 0.002, 0.05)
    crack = crack - fast_lowpass(crack, 300)           # brillante y seco
    body = fast_lowpass(brown_noise(int(1.6 * SR)), 900) * exp_env(int(1.6 * SR), 0.01, 0.3)
    thump = np.sin(2 * np.pi * 55 * np.arange(int(0.6 * SR)) / SR) * exp_env(int(0.6 * SR), 0.004, 0.16)
    put(crack, t0, amp, pan=0.5)
    put(body, t0, amp * 0.8, pan=0.5)
    put(thump, t0, amp * 0.9, pan=0.5)
    # escombros
    for i in range(14):
        put(rng.standard_normal(90) * np.hanning(90), t0 + 0.1 + rng.uniform(0, 0.9),
            amp * 0.12 * rng.uniform(0.3, 1), pan=rng.uniform(0.2, 0.8))

rock_fracture(15.18, amp=1.0)                        # grietas sísmicas
whoosh(16.35, dur=0.5, amp=0.6, pan_from=0.7, pan_to=0.25)  # corte de aire
crackle(15.6, 18.5, rate=16, amp=0.09, bright=True)  # magma texto chispeando

# ============================================================
# 5) MÚSICA: DARK REGGAETON 92 BPM (entra 15.5s, clímax 22.5s)
# ============================================================
BPM = 92.0
BEAT = 60.0 / BPM
STEP = BEAT / 2          # corcheas
BAR = 4 * BEAT
T_MUS = 15.5
T_CLIMAX = 22.5
T_STOP = 28.55

D2, C2, BB1, A1, F2 = 73.416, 65.406, 58.270, 55.000, 87.307
D4, F4, A4, C5 = 293.66, 349.23, 440.0, 523.25
D5, A5, G4 = 587.33, 440.0 * 2, 392.0

def kick():
    n = int(0.32 * SR)
    body = sine_sweep(155, 42, 0.32) * exp_env(n, 0.002, 0.11)
    click = rng.standard_normal(int(0.006 * SR)) * np.hanning(int(0.006 * SR))
    sig = body * 1.0
    sig[:len(click)] += click * 0.5
    return sig

def snare():
    n = int(0.22 * SR)
    noise = rng.standard_normal(n)
    noise = noise - fast_lowpass(noise, 350)
    body = np.sin(2 * np.pi * 190 * np.arange(n) / SR) * 0.5
    return (noise * 0.8 + body) * exp_env(n, 0.001, 0.05)

def hat(dur=0.045, amp=1.0, open_=False):
    n = int((0.14 if open_ else dur) * SR)
    noise = rng.standard_normal(n)
    noise = noise - fast_lowpass(noise, 800)
    return noise * exp_env(n, 0.0008, 0.012 if not open_ else 0.05) * amp

def sub_note(freq, dur=0.42):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
    return sig * exp_env(n, 0.008, dur * 0.5)

def saw(freq, n):
    t = np.arange(n) / SR
    ph = (t * freq) % 1.0
    return 2 * ph - 1

def stab():
    n = int(0.16 * SR)
    sig = (saw(D4, n) + saw(F4 * 1.003, n) + saw(A4 * 0.997, n)) / 3
    sig = fast_lowpass(sig, 60)
    return sig * exp_env(n, 0.004, 0.05)

def bell(freq, dur=0.5):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = (np.sin(2 * np.pi * freq * t)
           + 0.45 * np.sin(2 * np.pi * freq * 2.76 * t)
           + 0.2 * np.sin(2 * np.pi * freq * 5.4 * t))
    return sig * exp_env(n, 0.003, 0.18)

KICK, SNARE, HAT, OHAT, STAB = kick(), snare(), hat(), hat(open_=True), stab()

def mus_gain(t):
    """Fade-in 15.5-19.5, boost en clímax."""
    if t < T_MUS:
        return 0.0
    g = min(1.0, (t - T_MUS) / 4.0) * 0.85
    if t >= T_CLIMAX:
        g = 1.0
    return g

bar = 0
t_b = T_MUS
bass_pat = [[D2, D2, F2, D2], [D2, C2, BB1, A1]]
while t_b < T_MUS + 200:
    if t_b >= T_STOP:
        break
    climax = t_b + BAR > T_CLIMAX
    pat = bass_pat[bar % 2]
    for step in range(8):
        ts = t_b + step * STEP
        g = mus_gain(ts)
        if g <= 0 or ts >= T_STOP:
            continue
        if step in (0, 2, 4, 6):                       # dembow kick
            put(KICK, ts, 0.95 * g, pan=0.5)
            put(sub_note(pat[step // 2]), ts, 0.6 * g, pan=0.5)
        if step in (3, 7):                             # dembow snare
            put(SNARE, ts, 0.62 * g, pan=0.48)
        # hats en 16avos
        for sub in (0.0, 0.5):
            th = ts + sub * STEP
            if th < T_STOP and mus_gain(th) > 0:
                put(HAT, th, (0.16 + (0.10 if sub else 0)) * g, pan=0.55)
        if climax and step == 6:
            put(OHAT, ts, 0.30, pan=0.45)
        if climax and step in (0, 5):
            put(STAB, ts, 0.30, pan=0.42)
    if climax and bar % 2 == 0:                        # campanas siniestras
        mot = [(0, D5), (3, C5), (6, A4), (10, 349.23), (13, 392.0)]
        for st, fr in mot:
            tb2 = t_b + st * STEP
            if tb2 < T_STOP:
                b = bell(fr)
                put(b, tb2, 0.34, pan=0.6)
                put(b * 0.4, tb2 + STEP, 0.34 * 0.45, pan=0.35)   # delay
                put(b * 0.18, tb2 + 2 * STEP, 0.34 * 0.25, pan=0.65)
    t_b += BAR
    bar += 1

# ============================================================
# 6) EXPLOSIÓN FINAL + ECO APAGÁNDOSE (28.55s)
# ============================================================
def explosion(t0, amp):
    n = int(1.8 * SR)
    boom = fast_lowpass(brown_noise(n), 1100) * exp_env(n, 0.005, 0.32)
    drop = sine_sweep(70, 26, 1.2) * exp_env(int(1.2 * SR), 0.004, 0.5)
    shat = rng.standard_normal(int(0.4 * SR))
    shat = (shat - fast_lowpass(shat, 500)) * exp_env(int(0.4 * SR), 0.002, 0.07)
    sig = np.concatenate([boom, np.zeros(max(0, len(drop) - n))])
    sig = boom[:len(drop)] * 1.0 + drop * 0.9
    sig = np.concatenate([sig, np.zeros(0)])
    put(sig, t0, amp, pan=0.5)
    put(shat, t0, amp * 0.55, pan=0.5)
    put(sig * 0.35, t0 + 0.38, amp * 0.4, pan=0.3)   # eco 1
    put(sig * 0.14, t0 + 0.76, amp * 0.18, pan=0.7)  # eco 2

explosion(28.55, 1.0)

# ============================================================
# 7) MEZCLA / MASTER
# ============================================================
mix_l = np.tanh(L * 1.25) * 0.80
mix_r = np.tanh(R * 1.25) * 0.80
peak = max(np.max(np.abs(mix_l)), np.max(np.abs(mix_r)), 1e-9)
mix_l = mix_l / peak * 0.95
mix_r = mix_r / peak * 0.95

stereo = np.empty((N, 2), dtype=np.int16)
stereo[:, 0] = np.clip(mix_l, -1, 1) * 32767
stereo[:, 1] = np.clip(mix_r, -1, 1) * 32767

os.makedirs('video_build', exist_ok=True)
with wave.open('video_build/audio.wav', 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo.tobytes())
print('audio.wav OK:', N / SR, 's @', SR, 'Hz stereo')
