import math, random, subprocess, wave, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

D = '/tmp/claude-0/w/vid/'
FPS = 24
BW, BH = 540, 960          # base canvas (sprites native 1px)
OUT = D + 'rusdi_intro4.mp4'
random.seed(7)

FB = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def F(sz): return ImageFont.truetype(FB, sz)
f14, f18, f22, f28, f40, f56 = F(14), F(18), F(22), F(28), F(40), F(56)

# ---------- sprites ----------
def load(n): return Image.open(D + n + '.png').convert('RGBA')
def recol(im):
    a = np.array(im).astype(float)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    mx = a[..., :3].max(2); mn = a[..., :3].min(2); sat = (mx - mn) / (mx + 1e-6)
    beige = (sat < 0.22) & (mx > 95) & (r >= b) & (al > 0) & (r - b > 4)
    L = (0.3 * r + 0.59 * g + 0.11 * b) / 255
    t = np.clip((L - 0.35) / 0.55, 0, 1)[..., None]
    col = np.array([46, 74, 52]) * (1 - t) + np.array([92, 130, 96]) * t
    o = a.copy(); o[beige, :3] = col[beige]
    pink = (r > 190) & (g < 175) & (b > 140) & (al > 0)
    o[pink, :3] = [70, 70, 80]
    im2 = Image.fromarray(o.astype('uint8'))
    # tufts of messy hair like Rusdi's avatar
    d = ImageDraw.Draw(im2)
    bb = im2.getbbox(); top = bb[1]
    # find hair top x-range
    arr = np.array(im2)
    cols = [x for x in range(arr.shape[1]) if arr[top + 3, x, 3] > 0]
    if cols:
        cx = (cols[0] + cols[-1]) // 2
        for dx, h in [(-14, 6), (-6, 9), (3, 7), (12, 8), (19, 5)]:
            x = cx + dx
            d.polygon([(x - 3, top + 6), (x + 3, top + 6), (x + 1, top + 6 - h)], fill=(24, 22, 26, 255))
    return im2

_h0 = load('rusdi_h_0')
def _bob(im, dy):
    o = Image.new('RGBA', (im.width, im.height + 2)); o.alpha_composite(im, (0, dy)); return o
R_STAND = [_bob(_h0, 1 if i in (4, 5, 6) else 0) for i in range(12)]
R_WALK = [load('rusdi_h_%d' % i) for i in (7, 8, 9, 10)]
R_SIT = [load('rusdi_k_%d' % i) for i in (11, 11, 12, 12, 9, 9, 11, 12)]
B_SIT = [load('bagas_q_%d' % i) for i in range(8)]
AV = load('av_R')
SKIN = AV.getpixel((60, 86))
def av_frame(open_):
    a = AV.copy(); d = ImageDraw.Draw(a)
    if open_:
        d.rectangle([66, 89, 75, 94], fill=(120, 40, 40, 255))
        d.rectangle([67, 90, 74, 91], fill=(250, 250, 250, 255))
        d.rectangle([68, 93, 73, 94], fill=(200, 90, 90, 255))
    return a
AV_C, AV_O = av_frame(False), av_frame(True)

def paste(img, sp, x, y, flip=False):
    s = sp.transpose(Image.FLIP_LEFT_RIGHT) if flip else sp
    img.alpha_composite(s, (int(x), int(y)))

# ---------- pixel props (drawn at half res then x2) ----------
def office(mode='pagi', clock='06:00'):
    W, H = 270, 480
    im = Image.new('RGBA', (W, H)); d = ImageDraw.Draw(im)
    night = mode == 'malam'
    wall = (58, 52, 92) if night else (238, 222, 196)
    wall2 = (48, 43, 78) if night else (226, 206, 176)
    d.rectangle([0, 0, W, 190], fill=wall)
    for x in range(0, W, 18): d.rectangle([x, 0, x + 8, 190], fill=wall2)
    d.rectangle([0, 182, W, 190], fill=(40, 36, 60) if night else (170, 130, 95))
    # floor tiles
    for y in range(190, H, 14):
        for x in range(0, W, 14):
            c = ((x // 14 + y // 14) % 2)
            d.rectangle([x, y, x + 13, y + 13], fill=((70, 62, 98) if c else (62, 55, 88)) if night else ((196, 160, 120) if c else (184, 148, 108)))
    # window
    d.rectangle([150, 26, 250, 110], fill=(40, 30, 40))
    if night:
        d.rectangle([154, 30, 246, 106], fill=(22, 26, 60))
        for sx, sy in [(165, 40), (190, 58), (230, 45), (210, 80), (175, 90), (240, 95)]: d.point((sx, sy), fill=(255, 255, 210))
        d.ellipse([214, 36, 232, 54], fill=(250, 240, 190)); d.ellipse([220, 34, 236, 50], fill=(22, 26, 60))
    else:
        for i in range(76):
            yy = 30 + i; k = i / 76
            d.line([154, yy, 246, yy], fill=(int(255 - 30 * k), int(170 + 50 * k), int(120 + 100 * k)))
        d.ellipse([186, 72, 214, 100], fill=(255, 226, 120))
        d.rectangle([154, 92, 246, 106], fill=(120, 110, 150))
        for bx, bh in [(158, 10), (172, 18), (190, 8), (206, 22), (226, 12), (238, 16)]: d.rectangle([bx, 106 - bh, bx + 10, 106], fill=(90, 80, 120))
    d.rectangle([198, 26, 202, 110], fill=(40, 30, 40)); d.rectangle([150, 66, 250, 69], fill=(40, 30, 40))
    # clock
    d.ellipse([40, 30, 76, 66], fill=(250, 248, 240), outline=(40, 36, 50), width=3)
    d.line([58, 48, 58, 36], fill=(40, 36, 50), width=2); d.line([58, 48, 58, 60] if clock == '06:00' else [58, 48, 68, 48], fill=(198, 40, 40), width=2)
    # poster
    d.rectangle([92, 34, 132, 84], fill=(198, 40, 40)); d.rectangle([96, 38, 128, 60], fill=(247, 201, 72))
    d.rectangle([98, 66, 126, 69], fill=(255, 255, 255)); d.rectangle([98, 73, 118, 76], fill=(255, 255, 255))
    # plant
    d.rectangle([14, 156, 30, 186], fill=(150, 90, 60)); d.ellipse([6, 128, 38, 162], fill=(60, 140, 80)); d.ellipse([14, 118, 32, 140], fill=(80, 170, 100))
    return im.resize((W * 2, H * 2), Image.NEAREST)

def desk(w=120, lamp=False, night=False):
    im = Image.new('RGBA', (w // 2, 50)); d = ImageDraw.Draw(im)
    d.rectangle([0, 10, w // 2, 16], fill=(150, 98, 62)); d.rectangle([0, 16, w // 2, 19], fill=(110, 70, 45))
    d.rectangle([3, 19, 7, 50], fill=(110, 70, 45)); d.rectangle([w // 2 - 8, 19, w // 2 - 4, 50], fill=(110, 70, 45))
    d.rectangle([w // 4 - 10, -2 + 0, w // 4 + 10, 9], fill=(40, 44, 60)); d.rectangle([w // 4 - 8, 1, w // 4 + 8, 7], fill=(120, 200, 255) if not night else (90, 120, 200))
    if lamp:
        d.rectangle([w // 2 - 14, 2, w // 2 - 12, 10], fill=(60, 60, 70)); d.rectangle([w // 2 - 18, 0, w // 2 - 8, 3], fill=(247, 201, 72))
    return im.resize((w, 100), Image.NEAREST)

def icon(kind, s=4):
    g = {
        'riset': ["...XXXX.....", "..X....X....", ".X......X...", ".X......X...", ".X......X...", ".X......X...", "..X....X....", "...XXXXOO...", ".......OOO..", "........OOO.", ".........OO.", "............"],
        'copy': ["XXXXXXXX....", "X......X....", "X.XXXX.X....", "X......X..O.", "X.XXXX.X.OO.", "X......XOO..", "X.XXX..OO...", "X.....OO....", "X....OOX....", "X....O.X....", "XXXXXXXX....", "............"],
        'cek': ["XXXXXXXXXX..", "X........X..", "X.OO.XXX.X..", "X..O.....X..", "X........X..", "X.OO.XXX.X..", "X..O.....X..", "X........X..", "X.OO.XXX.X..", "X..O.....X..", "XXXXXXXXXX..", "............"],
        'jadwal': [".X....X.....", "XXXXXXXXXX..", "XOOOOOOOOX..", "X........X..", "X.XX.XX..X..", "X........X..", "X.XX.XO..X..", "X.....OO.X..", "X.XX.XO..X..", "X........X..", "XXXXXXXXXX..", "............"],
        'heart': [".XX.XX.", "XXXXXXX", "XXXXXXX", ".XXXXX.", "..XXX..", "...X..."],
        'check': ["......X", ".....XX", "X...XX.", "XX.XX..", ".XXX...", "..X...."],
    }[kind]
    w, h = len(g[0]), len(g)
    im = Image.new('RGBA', (w * s, h * s)); d = ImageDraw.Draw(im)
    for y, row in enumerate(g):
        for x, ch in enumerate(row):
            if ch == 'X': d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=(27, 27, 31))
            if ch == 'O': d.rectangle([x * s, y * s, x * s + s - 1, y * s + s - 1], fill=(198, 40, 40))
    return im

def tint(im, col):
    a = np.array(im); m = a[..., 3] > 0; a[m, :3] = col; return Image.fromarray(a)

def ptext(d, xy, s, font, fill, anchor='la', shadow=None):
    if shadow: d.text((xy[0] + 3, xy[1] + 3), s, font=font, fill=shadow, anchor=anchor)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)

def chip(img, txt, y=34):
    d = ImageDraw.Draw(img); d.fontmode = '1'
    w = d.textlength(txt, font=f18) + 28
    x = (BW - w) // 2
    d.rectangle([x, y, x + w, y + 34], fill=(27, 27, 31)); d.rectangle([x + 3, y + 3, x + w - 3, y + 31], fill=(198, 40, 40))
    ptext(d, (BW // 2, y + 17), txt, f18, (255, 255, 255), 'mm')

# ---------- script ----------
SC = [
    ('boot', []),
    ('intro', ["Halo! Aku Rusdi.", "Aku kepala staf konten di kantor kecil milik Jers."]),
    ('tugas', ["Tugasku ada empat.", "Riset tren tiap pagi, nulis copy, ngecek mutu desain, dan jadwalin tayang."]),
    ('k1', ["Jam enam pagi, aku riset apa yang lagi rame."]),
    ('k2', ["Aku tulis copy-nya, lalu kirim ke Jers buat disetujui."]),
    ('k3', ["Kalau Jers oke, aku antar ke meja Bagas."]),
    ('k4', ["Bagas mendesain, aku cek, lalu kontennya tayang sendiri."]),
    ('jers', ["Soal Jers? Menurutku dia bukan bos yang cuma nyuruh.", "Dia yang bangun kantor ini, meja demi meja.", "Revisinya detail. Kadang aku nulis ulang tiga kali.", "Tapi justru itu yang bikin kami makin pintar."]),
    ('outro', ["Besok jam enam pagi aku riset lagi.", "Sampai ketemu di konten berikutnya!"]),
    ('end', []),
]
CPS = 21.0
import json as _js
_AL = _js.load(open(D + 'vo/align.json'))['t3']['segs']
_w = wave.open(D + 'vo/t3.wav'); _VSR = _w.getframerate(); _VA = np.frombuffer(_w.readframes(_w.getnframes()), '<i2').astype(float) / 32768
_VA = _VA / (np.abs(_VA).max() + 1e-9) * .85
_ALL = [ln for _n, _ls in SC for ln in _ls]
VO = {}
for _i, _ln in enumerate(_ALL):
    _a, _b = _AL[_i]; _a = max(0, _a - .04); _b = _b + .08
    _seg = _VA[int(_a * _VSR):int(_b * _VSR)]
    _hop = _VSR // 100; _nn = len(_seg) // _hop
    _env = np.sqrt((_seg[:_nn * _hop].reshape(_nn, _hop) ** 2).mean(1))
    VO[_ln] = dict(dur=len(_seg) / _VSR, seg=_seg, env=_env)
def line_dur(t): return VO[t]['dur'] + 0.55
TL = []  # (scene, t0, t1, lines[(t0, text)])
t = 0.0
for name, lines in SC:
    st = t; L = []
    if name == 'boot': t += 3.2
    elif name == 'end': t += 3.0
    else:
        t += 0.35
        for ln in lines: L.append((t, ln)); t += line_dur(ln)
        t += 0.2
    TL.append((name, st, t, L))
TOTAL = t
print('durasi', round(TOTAL, 1))

def wrap(d, s, font, w):
    out, cur = [], ''
    for wd in s.split(' '):
        tt = (cur + ' ' + wd).strip()
        if d.textlength(tt, font=font) <= w: cur = tt
        else: out.append(cur); cur = wd
    out.append(cur); return out

BLIPS = []  # times of voice blips
def dialogue(img, L, lt, gt):
    cur = None
    for (t0, s) in L:
        if lt >= t0 - 0.35 + 0.35: cur = (t0, s)
    if not cur: return
    t0, s = cur; v = VO[s]; n = int(min(1, max(0, (lt - t0)) / max(.3, v['dur'] - .15)) * len(s)); shown = s[:n]
    fi = int((lt - t0) * 100); talking = 0 <= fi < len(v['env']) and v['env'][max(0, fi - 1):fi + 2].max() > .03
    d = ImageDraw.Draw(img); d.fontmode = '1'
    x0, y0, x1, y1 = 16, 600, BW - 16, 760
    d.rectangle([x0, y0, x1, y1], fill=(27, 27, 31)); d.rectangle([x0 + 4, y0 + 4, x1 - 4, y1 - 4], fill=(251, 245, 243)); d.rectangle([x0 + 8, y0 + 8, x1 - 8, y1 - 8], fill=(27, 27, 31))
    a = AV_O if (talking and int(gt * 14) % 2 == 0) else AV_C
    d.rectangle([x0 + 16, y0 + 18, x0 + 140, y0 + 142], fill=(198, 40, 40))
    img.alpha_composite(a, (x0 + 18, y0 + 20))
    # name tag
    d.rectangle([x0 + 10, y0 - 22, x0 + 110, y0 + 2], fill=(247, 201, 72)); ptext(d, (x0 + 60, y0 - 10), 'RUSDI', f18, (27, 27, 31), 'mm')
    lines = wrap(d, s, f22, x1 - x0 - 170)
    k = 0
    for i, ln in enumerate(lines):
        part = shown[k:k + len(ln)]; k += len(ln) + 1
        ptext(d, (x0 + 156, y0 + 24 + i * 30), part, f22, (255, 255, 255))
    if n >= len(s) and int(gt * 3) % 2 == 0:
        d.polygon([(x1 - 34, y1 - 30), (x1 - 20, y1 - 30), (x1 - 27, y1 - 22)], fill=(247, 201, 72))

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def pop(x):
    x = max(0, min(1, x)); c = 1.70158; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2

def footer(img, gt):
    d = ImageDraw.Draw(img); d.fontmode = '1'
    d.rectangle([150, 786, 390, 814], fill=(27, 27, 31))
    ptext(d, (BW // 2, 800), '@jerapahmerah_', f18, (251, 245, 243), 'mm')
    p = gt / TOTAL
    d.rectangle([60, 822, BW - 60, 828], fill=(80, 70, 90)); d.rectangle([60, 822, 60 + int((BW - 120) * p), 828], fill=(247, 201, 72))


import json as _json
from pano import build as _pbuild, PW as _PW, PH as _PH
ANCH = _json.load(open(D + 'anch.json'))
_P, META = _pbuild()
PANO = _P.resize((_PW * 2, _PH * 2), Image.NEAREST)
def _night(im):
    a = np.array(im).astype(float)
    a[..., 0] *= .42; a[..., 1] *= .46; a[..., 2] *= .70
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
PANO_N = _night(PANO)
_gl = Image.new('RGBA', PANO.size); _gd = ImageDraw.Draw(_gl)
for (x, y) in META['lamps']:
    for r in range(8, 0, -1):
        R_ = r * 18; _gd.ellipse([x * 2 - R_, y * 2 - R_ // 2 + 40, x * 2 + R_, y * 2 + R_ + 140], fill=(255, 200, 120, 7))
for (x0, y0, x1, y1) in META['mons']:
    _gd.ellipse([x0 * 2 - 30, y0 * 2 - 20, x1 * 2 + 30, y1 * 2 + 50], fill=(120, 180, 255, 26))
_a = np.array(PANO_N); _hole = _a[..., 3] == 0
PANO_N.alpha_composite(_gl)
_a = np.array(PANO_N); _a[_hole, 3] = 0; PANO_N = Image.fromarray(_a)
WINS = [(x0 * 2, y0 * 2, x1 * 2, y1 * 2) for (x0, y0, x1, y1) in META['wins']]
MONS = [(x0 * 2, y0 * 2, x1 * 2, y1 * 2) for (x0, y0, x1, y1) in META['mons']]
STEAM = (META['steam'][0] * 2, META['steam'][1] * 2)
_SC = {}
def spc(key, sc=1.0):
    k = (key, sc)
    if k not in _SC:
        im = load(key); _SC[k] = (im, ANCH[key][0], ANCH[key][1])
    return _SC[k]
_rnd = random.Random(11)
STARS = [(_rnd.randint(0, 2800), _rnd.randint(40, 280), _rnd.random()) for _ in range(160)]
CLOUDS = [(_rnd.randint(0, 2800), _rnd.randint(50, 170), _rnd.randint(50, 110)) for _ in range(14)]
BLD = []
_x = 0
while _x < 3400:
    _w = _rnd.randint(40, 110); _h = _rnd.randint(40, 150); BLD.append((_x, _w, _h, [(_rnd.random() < .33) for _ in range(80)])); _x += _w + _rnd.randint(0, 20)
def sky(cx0, t, night):
    s = Image.new('RGBA', (BW, BH)); d = ImageDraw.Draw(s)
    for y in range(0, 300, 4):
        k = y / 300
        col = (int(18 + 20 * k), int(22 + 26 * k), int(58 + 40 * k)) if night else (int(176 + 60 * k), int(214 + 30 * k), int(236 + 10 * k))
        d.rectangle([0, y, BW, y + 3], fill=col)
    if night:
        for (sx, sy, ph) in STARS:
            xx = (sx - cx0 * .2) % 2800
            if xx < BW and math.sin(t * 3 + ph * 9) > -.3: d.rectangle([xx, sy, xx + 1, sy + 1], fill=(255, 250, 220))
        mx = 380
        d.ellipse([mx, 60, mx + 36, 96], fill=(250, 240, 200)); d.ellipse([mx + 10, 54, mx + 46, 90], fill=(col))
    else:
        for (cx, cy, w) in CLOUDS:
            xx = (cx + t * 10 - cx0 * .25) % 3000 - 200
            d.rectangle([xx, cy, xx + w, cy + 14], fill=(255, 255, 255)); d.rectangle([xx + 12, cy - 10, xx + w - 18, cy], fill=(255, 255, 255))
    for (bx, w, h, lit) in BLD:
        xx = bx - cx0 * .35
        if xx < -120 or xx > BW + 10: continue
        y0 = 290 - h
        d.rectangle([xx, y0, xx + w, 300], fill=(30, 34, 70) if night else (165, 182, 196))
        i = 0
        for wy in range(y0 + 8, 290, 16):
            for wx in range(int(xx) + 6, int(xx + w) - 6, 14):
                on = lit[i % 80]; i += 1
                if night and on: d.rectangle([wx, wy, wx + 5, wy + 6], fill=(255, 214, 120))
                elif not night and on: d.rectangle([wx, wy, wx + 5, wy + 6], fill=(196, 210, 220))
    return s
def cam(mode, cx, sprites, t):
    night = mode == 'night'
    cx0 = int(max(0, min(2800 - BW, cx - BW / 2)))
    img = sky(cx0, t, night)
    img.alpha_composite((PANO_N if night else PANO).crop((cx0, 0, cx0 + BW, BH)))
    d = ImageDraw.Draw(img)
    if not night:
        sh = Image.new('RGBA', (BW, BH)); sd = ImageDraw.Draw(sh)
        for (x0, y0, x1, y1) in WINS:
            if x1 + 200 < cx0 or x0 > cx0 + BW: continue
            a = int(16 + 6 * math.sin(t * .8))
            sd.polygon([(x0 - cx0, y1 + 10), (x1 - cx0, y1 + 10), (x1 - cx0 + 180, 720), (x0 - cx0 + 180, 720)], fill=(255, 244, 210, a))
        img.alpha_composite(sh)
        for k in range(22):
            px = (k * 157 + t * 12) % BW; py = 320 + (k * 97 + t * 7 * (1 + k % 3)) % 360
            d.rectangle([px, py, px + 1, py + 1], fill=(255, 250, 230))
    for (x0, y0, x1, y1) in MONS:
        if x1 < cx0 or x0 > cx0 + BW: continue
        X0 = x0 - cx0
        d.rectangle([X0, y0, X0 + (x1 - x0), y1], fill=(28, 44, 70) if not night else (40, 70, 120))
        for li in range(4):
            ln = (int(t * 4) + li + x0) % 7
            w = 8 + (ln * 7) % 40
            d.rectangle([X0 + 4, y0 + 4 + li * 7, X0 + 4 + min(w, x1 - x0 - 8), y0 + 7 + li * 7], fill=[(120, 230, 140), (247, 201, 72), (130, 190, 255), (255, 255, 255)][ln % 4])
    sx, sy = STEAM
    if cx0 - 40 < sx < cx0 + BW + 40:
        for k in range(6):
            ph = (t * 1.2 + k / 6) % 1
            ox = int(math.sin(ph * 6 + k) * 6)
            d.rectangle([sx - cx0 + ox, sy - ph * 60, sx - cx0 + 4 + ox, sy - ph * 60 + 4], fill=(255, 255, 255))
    for key, x, y, flip, sc in sorted(sprites, key=lambda s: s[2]):
        im, ax, ay = spc(key)
        if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT); ax = im.width - ax
        img.alpha_composite(im, (int(x - ax - cx0), int(y - ay)))
    return img
def lerp(a, b, t): t = max(0, min(1, t)); return a + (b - a) * t
RWALK = ['rusdi_h_%d' % i for i in (7, 8, 9, 10)]
RCOF = ['rusdi_k_%d' % i for i in (11, 11, 12, 12, 9, 9, 11, 12)]
CATW = ['cat_%d' % i for i in (8, 9, 10, 11)]
def ridle(t): return 'rusdi_h_0'
DESK = (700, 565)
RS = BS = 1.0

def frame(gt):
    for name, st, en, L in TL:
        if st <= gt < en: break
    lt = gt - st; dur = en - st
    if name == 'boot':
        img = Image.new('RGBA', (BW, BH), (10, 10, 16, 255)); d = ImageDraw.Draw(img); d.fontmode = '1'
        a = min(1, lt / 0.8)
        ptext(d, (BW // 2, 360), 'KANTOR', f56, (247, 201, 72) if a > .5 else (90, 80, 40), 'mm', shadow=(198, 40, 40))
        ptext(d, (BW // 2, 425), 'AGENT', f56, (247, 201, 72) if a > .5 else (90, 80, 40), 'mm', shadow=(198, 40, 40))
        txt = '> memuat RUSDI.EXE' + ('_' if int(gt * 4) % 2 else ' ')
        ptext(d, (BW // 2, 520), txt[:int(lt * 14)] if lt * 14 < len(txt) else txt, f22, (120, 230, 140), 'mm')
        p = ease((lt - 0.8) / 2.0)
        d.rectangle([120, 560, 420, 584], outline=(120, 230, 140), width=3); d.rectangle([126, 566, 126 + int(288 * p), 578], fill=(120, 230, 140))
        if lt > 2.9: img.paste((255, 255, 255, 255), [0, 0, BW, BH])
        return img
    if name == 'end':
        img = cam('day', 1400 + lt * 20, [], gt)
        img.alpha_composite(Image.new('RGBA', (BW, BH), (20, 18, 30, 200)))
        d = ImageDraw.Draw(img); d.fontmode = '1'
        s = pop(lt / 0.5)
        im, ax, ay = spc('rusdi_h_0', 1.0); img.alpha_composite(im, (BW // 2 - im.width // 2, 150 + int((1 - s) * 60)))
        ptext(d, (BW // 2, 420), 'RUSDI', f56, (247, 201, 72), 'mm', shadow=(198, 40, 40))
        ptext(d, (BW // 2, 475), 'kepala staf konten', f22, (251, 245, 243), 'mm')
        if int(gt * 2.5) % 2 == 0 or lt < .6:
            d.rectangle([150, 530, 390, 586], fill=(27, 27, 31)); d.rectangle([154, 534, 386, 582], fill=(198, 40, 40))
            ptext(d, (BW // 2, 558), 'FOLLOW', f28, (255, 255, 255), 'mm')
        ptext(d, (BW // 2, 630), '@jerapahmerah_', f28, (251, 245, 243), 'mm')
        if lt > dur - .5: img.alpha_composite(Image.new('RGBA', (BW, BH), (0, 0, 0, int(255 * (lt - (dur - .5)) / .5))))
        return img
    wf = RWALK[int(gt * 8) % 4]
    if name == 'intro':
        T = 1.8
        if lt < T: sp = [(wf, lerp(300, DESK[0], lt / T), DESK[1], False, RS)]
        else: sp = [(ridle(lt), DESK[0], DESK[1], False, RS)]
        img = cam('day', lerp(420, 700, ease(lt / 2.2)), sp + ([(CATW[int(gt * 6) % 4], 1000 - lt * 90, 615, False, 1)] if lt < 9 else []), gt)
        d = ImageDraw.Draw(img); d.fontmode = '1'; chip(img, 'PERKENALAN')
        if 1.9 < lt < 3.4:
            b = pop((lt - 1.9) / .3)
            d.rectangle([300, 250 - int(20 * b), 330, 280 - int(20 * b)], fill=(255, 255, 255), outline=(27, 27, 31), width=3); ptext(d, (315, 265 - int(20 * b)), '!', f22, (198, 40, 40), 'mm')
    elif name == 'tugas':
        img = cam('day', 1000 + lt * 40, [(RCOF[int(lt * 3) % 8], 1300, 565, False, RS)], gt)
        img.alpha_composite(Image.new('RGBA', (BW, 590), (20, 18, 30, 175)), (0, 0))
        d = ImageDraw.Draw(img); d.fontmode = '1'; chip(img, 'TUGAS RUSDI')
        items = [('riset', 'RISET'), ('copy', 'COPY'), ('cek', 'CEK MUTU'), ('jadwal', 'JADWAL')]
        st2 = L[1][0] - st if len(L) > 1 else 1.5
        for k, (ic, lab) in enumerate(items):
            p = pop((lt - st2 - k * 0.75) / 0.35)
            if p <= 0: continue
            cx = 140 + (k % 2) * 260; cy = 190 + (k // 2) * 200
            w, h = int(210 * p), int(170 * p)
            if w < 14 or h < 14: continue
            d.rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], fill=(27, 27, 31))
            d.rectangle([cx - w // 2 + 4, cy - h // 2 + 4, cx + w // 2 - 4, cy + h // 2 - 4], fill=(251, 245, 243) if k % 3 else (247, 201, 72))
            if p > .7:
                im = icon(ic, 6); img.alpha_composite(im, (cx - im.width // 2 + 12, cy - 70))
                ptext(d, (cx, cy + 52), lab, f22, (27, 27, 31), 'mm')
    elif name in ('k1', 'k2', 'k3', 'k4'):
        idx = int(name[1])
        if name == 'k1':
            img = cam('day', 760, [(RCOF[int(lt * 3) % 8], 640, DESK[1], False, RS)], gt)
            d = ImageDraw.Draw(img); d.fontmode = '1'
            d.rectangle([330, 110, 520, 186], fill=(27, 27, 31)); ptext(d, (425, 148), '06:00', f40, (120, 230, 140) if int(gt * 2) % 2 else (90, 200, 120), 'mm')
            d.rectangle([330, 200, 520, 360], fill=(27, 27, 31)); d.rectangle([336, 206, 514, 354], fill=(251, 245, 243))
            for bb in range(5):
                hh = int(min(1, max(0, (lt - .3 - bb * .25) / .4)) * (24 + bb * 22))
                d.rectangle([348 + bb * 32, 340 - hh, 370 + bb * 32, 340], fill=(198, 40, 40) if bb == 4 else (247, 201, 72))
            mg = icon('riset', 4); paste(img, mg, 440 + int(math.sin(gt * 3) * 8), 216)
        elif name == 'k2':
            img = cam('day', 700, [(ridle(lt), 560, DESK[1], False, RS)], gt)
            d = ImageDraw.Draw(img); d.fontmode = '1'
            d.rectangle([24, 110, 214, 400], fill=(27, 27, 31)); d.rectangle([30, 116, 208, 394], fill=(251, 245, 243))
            nl = int(lt * 3.5)
            for i in range(min(nl, 9)):
                ww = 140 if i % 3 else 100
                d.rectangle([46, 136 + i * 28, 46 + ww, 146 + i * 28], fill=(27, 27, 31) if i else (198, 40, 40))
            pc = icon('copy', 4); paste(img, pc, 160 + int(math.sin(gt * 8) * 6), 128 + min(nl, 9) * 28)
            px, py = 360, 110
            d.rectangle([px, py, px + 156, py + 290], fill=(27, 27, 31)); d.rectangle([px + 8, py + 18, px + 148, py + 272], fill=(60, 56, 80))
            if lt > 1.2:
                b = pop((lt - 1.2) / .3)
                d.rectangle([px + 14, py + 40, px + 142, py + 40 + int(84 * b)], fill=(251, 245, 243))
                if b > .8:
                    ptext(d, (px + 24, py + 52), 'RUSDI', f14, (198, 40, 40)); ptext(d, (px + 24, py + 74), 'Copy siap.', f18, (27, 27, 31)); ptext(d, (px + 24, py + 98), 'ACC, Jers?', f18, (27, 27, 31))
            if lt > 2.6:
                b = pop((lt - 2.6) / .3)
                d.rectangle([px + 30, py + 160, px + 126, py + 160 + int(56 * b)], fill=(46, 143, 91))
                if b > .8: ptext(d, (px + 78, py + 188), 'SETUJU', f18, (255, 255, 255), 'mm')
        elif name == 'k3':
            T = 2.6; x0, x1 = 760, 1520
            if lt < T: sp = [(wf, lerp(x0, x1, lt / T), 565, False, RS)]
            else: sp = [('rusdi_h_0', x1, 565, False, RS)]
            sp.append(('bagas_q_%d' % (int(lt * 5) % 8), 1700, 560, False, BS))
            img = cam('day', min(1640, max(700, lerp(x0, x1, lt / T) + 120)), sp, gt)
            d = ImageDraw.Draw(img); d.fontmode = '1'
            if lt > 2.6:
                b = pop((lt - 2.6) / .3)
                d.rectangle([150, 170 - int(10 * b), 250, 196 - int(10 * b)], fill=(27, 27, 31)); ptext(d, (200, 183 - int(10 * b)), 'BAGAS', f18, (247, 201, 72), 'mm')
                d.rectangle([290, 300, 320, 336], fill=(251, 245, 243), outline=(27, 27, 31), width=2); d.line([296, 310, 314, 310], fill=(198, 40, 40), width=2); d.line([296, 320, 312, 320], fill=(27, 27, 31), width=2)
        elif name == 'k4':
            img = cam('day', 1420, [(RCOF[int(lt * 3) % 8], 1180, 565, False, RS)], gt)
            d = ImageDraw.Draw(img); d.fontmode = '1'
            px, py = 170, 110
            d.rectangle([px, py, px + 200, py + 360], fill=(27, 27, 31)); d.rectangle([px + 8, py + 20, px + 192, py + 340], fill=(251, 245, 243))
            for k in range(9):
                p = pop((lt - .2 - k * .18) / .25)
                if p <= 0: continue
                cx = px + 18 + (k % 3) * 58; cy = py + 40 + (k // 3) * 58; s = int(52 * p)
                d.rectangle([cx, cy, cx + s, cy + s], fill=[(198, 40, 40), (247, 201, 72), (46, 74, 52), (232, 88, 78), (47, 75, 124)][k % 5])
            if lt > 2.2:
                b = pop((lt - 2.2) / .35); w = int(170 * b)
                d.rectangle([BW // 2 - w // 2, 300, BW // 2 + w // 2, 350], fill=(46, 143, 91), outline=(27, 27, 31), width=4)
                if b > .8: ptext(d, (BW // 2, 325), 'TAYANG', f28, (255, 255, 255), 'mm')
            for k in range(6):
                hy = 470 - ((lt * 70 + k * 60) % 300); hx = 400 + int(math.sin(gt * 2 + k) * 30) + (k % 2) * 40
                if lt > 1.0: paste(img, tint(icon('heart', 5), (232, 88, 78)), hx, hy)
        chip(img, 'CARA KERJA  %d/4' % idx)
        d = ImageDraw.Draw(img)
        for k in range(4): d.rectangle([186 + k * 46, 76, 186 + k * 46 + 30, 82], fill=(198, 40, 40) if k < idx else (120, 110, 130))
    elif name == 'jers':
        img = cam('night', 2380 - lt * 6, [(ridle(lt), 2160, 575, False, RS)], gt)
        d = ImageDraw.Draw(img); d.fontmode = '1'; chip(img, 'MENURUT RUSDI')
        # Jers ID card
        b = pop(lt / .5)
        if b > .1:
            cx, cy = 400, 200; w, h = int(180 * b), int(120 * b)
            if w > 20:
                d.rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], fill=(27, 27, 31)); d.rectangle([cx - w // 2 + 4, cy - h // 2 + 4, cx + w // 2 - 4, cy + h // 2 - 4], fill=(247, 201, 72))
                if b > .8:
                    ptext(d, (cx, cy - 26), 'JERS', f28, (27, 27, 31), 'mm'); ptext(d, (cx, cy + 6), 'pendiri kantor', f14, (27, 27, 31), 'mm'); ptext(d, (cx, cy + 28), '@jerapahmerah_', f14, (198, 40, 40), 'mm')
        nh = sum(1 for (t0, s) in L if t0 <= gt)
        for k in range(nh * 3):
            hx = 40 + (k * 53) % 300; hy = 120 + ((k * 37) % 140) + int(math.sin(gt * 2 + k) * 6)
            ic = icon('heart', 4) if k % 2 else icon('check', 4)
            paste(img, tint(ic, (247, 201, 72) if k % 2 == 0 else (232, 88, 78)), hx, hy)
    elif name == 'outro':
        img = cam('day', 760, [(ridle(lt), 600, DESK[1], False, RS)], gt)
        d = ImageDraw.Draw(img); d.fontmode = '1'; chip(img, 'SAMPAI BESOK')
        d.rectangle([330, 110, 520, 186], fill=(27, 27, 31)); ptext(d, (425, 148), '06:00', f40, (120, 230, 140), 'mm')
        d.rectangle([340, 196, 510, 226], fill=(27, 27, 31)); ptext(d, (425, 211), 'riset lagi', f18, (251, 245, 243), 'mm')
    Labs = [(t0 - st, s) for (t0, s) in L]
    dialogue(img, Labs, lt, gt)
    footer(img, gt)
    if lt < .25:
        col = (255, 255, 255, int(255 * (1 - lt / .25))) if name == 'intro' else (0, 0, 0, int(200 * (1 - lt / .25)))
        img.alpha_composite(Image.new('RGBA', (BW, BH), col))
    return img

# ---------- audio ----------
SR = 44100
N = int(TOTAL * SR) + SR
au = np.zeros(N)
def sq(f, n, duty=.5):
    t = np.arange(n) / SR; return np.where((t * f) % 1 < duty, 1.0, -1.0)
def env(n, a=.005, r=.08):
    e = np.ones(n); ai = int(a * SR); ri = int(r * SR)
    if ai: e[:ai] = np.linspace(0, 1, ai)
    if ri and ri < n: e[-ri:] *= np.linspace(1, 0, ri)
    return e
# music (skip boot), 104 bpm
bpm = 104; beat = 60 / bpm
prog = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [59, 62, 67])]
mf = lambda m: 440 * 2 ** ((m - 69) / 12)
t0m = 3.2; tt = t0m; bi = 0
au_main = au; au = np.zeros(N)
while tt < TOTAL - .2:
    root, ch = prog[(bi // 8) % 4]
    i0 = int(tt * SR); n = int(beat / 2 * SR)
    night = any(nm == 'jers' and s0 <= tt < e0 for nm, s0, e0, _ in TL)
    vol = .05 if night else .07
    if bi % 2 == 0:
        seg = sq(mf(root - 12 + (0 if bi % 4 == 0 else 7)), n, .5) * env(n, .003, .1) * vol * 1.1
        au[i0:i0 + n] += seg[:max(0, min(n, N - i0))]
    note = ch[(bi) % 3] + (12 if (bi // 3) % 2 else 0)
    seg = sq(mf(note), n, .25) * env(n, .003, .12) * vol * .55
    au[i0:i0 + n] += seg[:max(0, min(n, N - i0))]
    if bi % 2 == 1:
        nn = int(.03 * SR); au[i0:i0 + nn] += np.random.uniform(-1, 1, nn) * env(nn, .001, .025) * vol * .5
    tt += beat / 2; bi += 1
duck = np.ones(N)
for name, st, en, L in TL:
    for (t0, s_) in L:
        i0 = int(t0 * SR); i1 = int((t0 + VO[s_]['dur']) * SR); duck[max(0, i0 - 2000):min(N, i1 + 4000)] = .45
duck = np.convolve(duck, np.ones(2205) / 2205, 'same')
au = au_main + au * duck
# boot chime
for k, m in enumerate([72, 76, 79, 84]):
    i0 = int((2.2 + k * .11) * SR); n = int(.22 * SR); au[i0:i0 + n] += sq(mf(m), n, .5) * env(n, .002, .15) * .12
# voice over (ElevenLabs, Pratama)
for name, st, en, L in TL:
    for (t0, s_) in L:
        seg = VO[s_]['seg']
        if _VSR != SR:
            seg = np.interp(np.arange(int(len(seg) * SR / _VSR)) * _VSR / SR, np.arange(len(seg)), seg)
        i0 = int(t0 * SR); m = min(len(seg), N - i0)
        if m > 0: au[i0:i0 + m] += seg[:m] * 1.05
# page-turn swoosh at scene starts
for name, st, en, L in TL[1:]:
    i0 = int(st * SR); n = int(.12 * SR)
    if i0 + n < N: au[i0:i0 + n] += np.random.uniform(-1, 1, n) * np.linspace(0, 1, n) ** 2 * env(n, .001, .05) * .06
au = np.clip(au, -1, 1)
au = au[:int(TOTAL * SR)]
with wave.open(D + 'audio.wav', 'w') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((au * 32000).astype('<i2').tobytes())

# ---------- render ----------
if len(sys.argv) > 1 and sys.argv[1] == 'still':
    for k, ts in enumerate([1.5, 6.5, 13, 20, 26, 31, 36.5, 42, 52, 64, TOTAL - 1.5]):
        if ts < TOTAL: frame(ts).convert('RGB').save(D + 'st%02d.png' % k)
    sys.exit()
nf = int(TOTAL * FPS)
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1080x1920', '-r', str(FPS), '-i', '-', '-i', D + 'audio.wav',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k', '-shortest', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(nf):
    im = frame(i / FPS).convert('RGB').resize((1080, 1920), Image.NEAREST)
    p.stdin.write(im.tobytes())
p.stdin.close(); p.wait()
print('ok', OUT)
