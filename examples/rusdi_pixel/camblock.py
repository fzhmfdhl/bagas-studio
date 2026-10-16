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

