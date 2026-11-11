#!/usr/bin/env python3
"""Mesin Reels "Seri AI" (teks + ikon, tanpa wajah) untuk @jerapahmerah_.

Palet kunci: maroon #6B1423 (utama) + putih (sekunder) + pink pucat #F2C9D0 (aksen kecil). Font hanya Space Mono.
Video disusun dari SPEC (JSON), bukan dari kode baru. Intro titik, sampul (frame 0-4) dan penutup bersifat tetap;
isi tengahnya = daftar adegan dari perpustakaan di bawah.

  python3 toolkit/seri.py cek    spec.json lembar.png [detik ...]   # lembar cek + garis zona aman (WAJIB dilihat)
  python3 toolkit/seri.py render spec.json final.mp4                # render penuh (2 proses, ~2 menit)
  python3 toolkit/seri.py contoh                                    # cetak spec contoh (Salah kaprah #01)

SPEC:
  {"seri": "SALAH KAPRAH #01", "handle": "@jerapahmerah_",
   "intro": ["KERJA", "KREATIF,", "DIBANTU", "AI."],           # tagline intro (4 kata, huruf besar)
   "sampul": {"baris": ["Prompt", "panjang"], "kata_a": "=", "sorot": "bagus?", "pose": "shock"},
   "adegan": [ {"tipe": "...", ...parameter..., "trans": "dorong_atas"}, ... ],
   "penutup": {"baris1": "simpan, coba besok pagi.", "baris2": "ikuti untuk seri berikutnya.", "pose": "wave"}}

Tipe adegan (perpustakaan): kata_besar, salah, daftar, hitung, langkah   (lihat fungsi sc_* untuk parameternya)
Transisi masuk adegan (field "trans"): lingkaran | dorong_atas | dorong_kiri | garis   (adegan pertama selalu "banjir")
Aturan kerapian terpasang di mesin: semua rata tengah, kolom daftar tetap, ikon sejajar tengah tinggi huruf,
isi di tengah layar (y 480-1250), karakter hanya di sampul dan penutup.
"""
import json, math, os, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from multiprocessing import Pool

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS = 1080, 1920, 30
RED, DK, CR, MU = '#6B1423', '#3E0A14', '#FFFFFF', '#F2C9D0'   # maroon, maroon gelap, putih, pink pucat
LY = 1380                                                       # garis lantai (karakter berdiri di sini)
ADV = 0.612                                                     # lebar huruf Space Mono = 0.612 x ukuran
POSES = ['wave', 'idle', 'show', 'talk', 'idea', 'laugh', 'shock']
C, IC, SPEC = {}, {}, {}


# ---------------------------------------------------------------- dasar
def rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def clamp(x): return max(0.0, min(1.0, x))
def seg(t, a, b): return clamp((t - a) / (b - a))
def eo(x): x = clamp(x); return 1 - (1 - x) ** 3
def eio(x): x = clamp(x); return x * x * (3 - 2 * x)
def ob(x, s=1.7): x = clamp(x); return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def FN(n, s): return ImageFont.truetype(os.path.join(ROOT, 'assets', 'fonts', 'SpaceMono-%s.ttf' % n), int(s))
def new(bg): return Image.new('RGBA', (W, H), rgb(bg))
def fitsize(text, size, maxw=880): return min(size, maxw / (max(1, len(text)) * ADV))


def layer_text(img, xy, text, font, fill, alpha=1.0, anchor='la'):
    if alpha <= 0 or not text: return
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text(xy, text, font=font, fill=rgb(fill) + (255,), anchor=anchor)
    if alpha < 1: lay.putalpha(lay.split()[3].point(lambda v: int(v * alpha)))
    img.alpha_composite(lay)


def typed(img, xy, text, size, fill, u, u0, cps, caret=None, bold='Bold', caret_hold=0.5):
    n = min(len(text), int(max(0, u - u0) * cps))
    layer_text(img, xy, text[:n], FN(bold, size), fill)
    if caret and u0 <= u < u0 + len(text) / cps + caret_hold and (int(u * 4) % 2 == 0 or n < len(text)):
        cx = xy[0] + n * ADV * size
        ImageDraw.Draw(img).rectangle((cx + 4, xy[1] + size * 0.18, cx + 4 + size * 0.34, xy[1] + size * 0.98), fill=rgb(caret))


def reveal(img, xy, text, font, fill, p, anchor='la', xmask=None):
    """Teks naik dari balik garis (p 0..1 masuk, 1..2 keluar ke atas)."""
    if p <= 0 or p >= 2: return
    x, y = xy; bb = font.getbbox(text, anchor=anchor)
    top, bot = int(y + bb[1] - 8), int(y + bb[3] + 12); h = bot - top
    off = (1 - eo(p)) * h if p <= 1 else -eo(p - 1) * h
    lay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((x, y + off), text, font=font, fill=rgb(fill) + (255,), anchor=anchor)
    a = np.array(lay.split()[3]); a[:max(0, top)] = 0; a[bot:] = 0
    if xmask is not None: a[:, :xmask[0]] = 0; a[:, xmask[1]:] = 0
    lay.putalpha(Image.fromarray(a)); img.alpha_composite(lay)


def tag(img, u, col, text, u0=0.1):
    reveal(img, (540, 290), text, FN('Bold', 28), col, seg(u, u0, u0 + 0.35), anchor='ma')


def hline(img, u, a, b, y, col, x0=100, x1=980):
    p = eio(seg(u, a, b))
    if p > 0: ImageDraw.Draw(img).line([(x0, y), (x0 + (x1 - x0) * p, y)], fill=rgb(col), width=2)


def sprite(name, h, outline, bw=6):
    im = Image.open(os.path.join(ROOT, 'assets', 'sprites', 'seri_jers_%s.png' % name)).convert('RGBA'); s = h / im.height
    im = im.resize((round(im.width * s), h), Image.NEAREST); a = im.split()[3]
    big = Image.new('L', (im.width + 4 * bw, im.height + 4 * bw), 0); big.paste(a, (2 * bw, 2 * bw))
    big = big.filter(ImageFilter.MaxFilter(2 * bw + 1))
    out = Image.new('RGBA', big.size, rgb(outline) + (0,)); out.putalpha(big)
    out.paste(im, (2 * bw, 2 * bw), im); return out


def char(img, pose, u, u0, cx=540, onmaroon=False):
    """Karakter (HANYA sampul dan penutup). Pop-in dari bawah garis lantai lalu bergoyang halus."""
    if u < u0: return
    sp = C[pose + ('_m' if onmaroon else '_w')]
    ps = ob(seg(u, u0, u0 + 0.5), 2.0); bob = round(5 * math.sin(2 * math.pi * 1.1 * (u - u0))) if u > u0 + 0.5 else 0
    sc = 0.75 + 0.25 * min(1, ps)
    sp = sp.resize((max(1, round(sp.width * sc)), max(1, round(sp.height * sc))), Image.BICUBIC)
    a = eo(seg(u, u0, u0 + 0.12))
    if a < 1: sp = sp.copy(); sp.putalpha(sp.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(sp, (int(cx - sp.width / 2), int(LY + 6 - sp.height + bob + 90 * (1 - min(1, ps)))))


def icon(img, name, hexcol, cx, cy, size, u, u0, alpha=1.0, out=None, shake=0):
    """Ikon Lucide (pop-in memantul, lalu mengambang). Warna: RED/CR/MU."""
    if u < u0 or alpha <= 0: return
    key = '%s_%s' % (name, hexcol.lstrip('#'))
    if key not in IC: IC[key] = Image.open(os.path.join(SPEC['_ic'], '%s_c%s.png' % (name, hexcol.lstrip('#')))).convert('RGBA')
    ps = ob(seg(u, u0, u0 + 0.45), 2.2); sc = 0.55 + 0.45 * min(1.08, ps)
    if out is not None and u > out: sc *= 1 - eio(seg(u, out, out + 0.25)); alpha *= 1 - seg(u, out, out + 0.25)
    if sc <= 0.02: return
    fl = 6 * math.sin(2 * math.pi * 0.9 * (u - u0)) if u > u0 + 0.45 else 0
    sx = shake * math.sin(u * 70) * (1 - seg(u, u0 + 0.1, u0 + 0.5))
    s_ = max(2, int(size * sc)); im = IC[key].resize((s_, s_), Image.BICUBIC)
    a = alpha * eo(seg(u, u0, u0 + 0.12))
    if a < 1: im.putalpha(im.split()[3].point(lambda v: int(v * a)))
    img.alpha_composite(im, (int(cx - s_ / 2 + sx), int(cy - s_ / 2 + fl)))


def circle_mask(cx, cy, r):
    y, x = np.mgrid[0:H, 0:W].astype('float32')
    return np.clip(r - np.sqrt((x - cx) ** 2 + (y - cy) ** 2) + 0.5, 0, 1)

def blend(a, b, m):
    A = np.asarray(a.convert('RGB')).astype('float32'); B = np.asarray(b.convert('RGB')).astype('float32')
    return Image.fromarray((A * (1 - m[..., None]) + B * m[..., None]).astype('uint8'))


# ---------------------------------------------------------------- bagian tetap: sampul + intro + penutup
def stack(img, u, y0, col, boxcol, txtin, baris, kata_a, sorot, ts=None, p_box=1.0):
    """Judul besar rata tengah: baris-baris, lalu baris terakhir "<kata_a> <sorot>" dengan kata sorot dalam kotak."""
    last = '%s %s' % (kata_a, sorot)
    sz = min(fitsize(max(list(baris) + [last], key=len), 160), 160); f = FN('Bold', sz); ad = ADV * sz; step = sz * 1.06
    pr = (lambda k: 1.0) if ts is None else (lambda k: seg(u, ts[k], ts[k] + 0.35))
    for k, b in enumerate(baris): reveal(img, (540, y0 + k * step), b, f, col, pr(k), anchor='ma')
    n = len(baris); y3 = y0 + n * step; x0 = 540 - len(last) * ad / 2; xb = x0 + (len(kata_a) + 1) * ad
    bb = f.getbbox(sorot); bx1 = int(xb - 14 + (len(sorot) * ad + 32) * p_box)
    reveal(img, (x0, y3), kata_a, f, col, pr(n))
    reveal(img, (xb, y3), sorot, f, col, pr(n + 1 if ts and len(ts) > n + 1 else n), xmask=(bx1, W))
    if p_box > 0:
        ImageDraw.Draw(img).rectangle((xb - 14, y3 + bb[1] - 14, bx1, y3 + bb[3] + 18), fill=rgb(boxcol))
        reveal(img, (xb, y3), sorot, f, txtin, 1.0, xmask=(0, bx1))


def cover():
    s = SPEC['sampul']; img = new(CR)
    layer_text(img, (540, 290), SPEC['seri'], FN('Bold', 28), RED, anchor='ma')
    stack(img, 99, 430, RED, RED, CR, s['baris'], s['kata_a'], s['sorot'])
    char(img, s.get('pose', 'shock'), 99, 0, 540)
    ImageDraw.Draw(img).line([(100, LY), (980, LY)], fill=rgb(RED), width=2)
    layer_text(img, (540, 1410), SPEC['handle'], FN('Regular', 28), RED, anchor='ma')
    return img


def intro(t):
    """Titik merah menulis tagline kata demi kata, memudar, titik membesar jadi lingkaran (banjir warna). t detik 0..3.3."""
    words = SPEC['intro']; img = new(CR); size = 40; full = ' '.join(words)
    x0 = (W - len(full) * ADV * size) / 2; ty = 960; times = [0.9, 1.35, 1.8, 2.25][:len(words)]
    ends = [x0 + len(' '.join(words[:k + 1])) * ADV * size for k in range(len(words))]
    fade = 1 - seg(t, 2.85, 3.15)
    for k, w in enumerate(words):
        if t >= times[k]:
            off = x0 + len(' '.join(words[:k])) * ADV * size + (ADV * size if k else 0)
            a = eo(seg(t, times[k], times[k] + 0.18)) * fade
            layer_text(img, (off, ty + 14 * (1 - eo(seg(t, times[k], times[k] + 0.18)))), w, FN('Bold', size), RED, a)
    r = 13; n = len(words) - 1
    if t < times[0]:
        p = eio(seg(t, 0.0, times[0])); cx = -30 + (x0 - 30 + 30) * p; cy = ty - 30 + 6 * math.sin(p * 9)
    elif t < 2.7:
        k = max(i for i in range(len(words)) if t >= times[i]); tgt = ends[k] - 16
        prev = ends[k - 1] - 16 if k else x0 - 30
        cx = prev + (tgt - prev) * eo(seg(t, times[k] - 0.18, times[k] + 0.18))
        cy = ty - 36 - 22 * math.sin(clamp((t - times[k]) / 0.35) * math.pi)
    else:
        cx0 = ends[n] - 16; cy0 = ty - 36; p = eio(seg(t, 2.7, 3.2))
        cx = cx0 + (540 - cx0) * p; cy = cy0 + (960 - cy0) * p; r = 13 + 40 * eio(seg(t, 3.0, 3.35))
    return img, (cx, cy, r)


def sc_penutup(u, P):
    """Penutup tetap: handle diketik, dua baris ajakan, garis lantai, karakter melambai."""
    img = new(CR); tag(img, u, RED, SPEC['seri'], 0.05)
    h = SPEC['handle']; typed(img, (540 - len(h) * ADV * 72 / 2, 620), h, 72, RED, u, 0.15, 22, caret=RED, caret_hold=1.2)
    reveal(img, (540, 760), P['baris1'], FN('BoldItalic', fitsize(P['baris1'], 56)), DK, seg(u, 0.85, 1.2), anchor='ma')
    reveal(img, (540, 860), P['baris2'], FN('Regular', fitsize(P['baris2'], 32)), RED, seg(u, 1.1, 1.45), anchor='ma')
    hline(img, u, 0.45, 0.95, LY, RED)
    char(img, P.get('pose', 'wave'), u, 0.65, 540)
    return img


# ---------------------------------------------------------------- perpustakaan adegan (u = detik sejak adegan mulai)
def sc_kata_besar(u, P):
    """Pernyataan besar + kata disorot kotak. P: baris[], kata_a, sorot, tag, ikon."""
    img = new(RED); tag(img, u, MU, P.get('tag', SPEC['seri']))
    if P.get('ikon'): icon(img, P['ikon'], CR, 540, 520, 170, u, 0.15)
    stack(img, u, 680, CR, CR, RED, P['baris'], P['kata_a'], P['sorot'], ts=[0.2 + 0.15 * k for k in range(len(P['baris']) + 2)],
          p_box=eio(seg(u, 0.95 + 0.15 * (len(P['baris']) - 2), 1.2 + 0.15 * (len(P['baris']) - 2))))
    return img

def sc_salah(u, P):
    """SALAH. besar bergetar + ikon silang. P: kata (default SALAH.), sub, ikon (default circle-x)."""
    img = new(CR); kata = P.get('kata', 'SALAH.'); sz = fitsize(kata, 230)
    sh = int(10 * math.sin(u * 70) * (1 - seg(u, 0.25, 0.6))) if u > 0.25 else 0
    reveal(img, (540 + sh, 560), kata, FN('Bold', sz), RED, seg(u, 0.0, 0.3), anchor='ma')
    reveal(img, (540, 845), P['sub'], FN('BoldItalic', fitsize(P['sub'], 40)), DK, seg(u, 0.4, 0.75), anchor='ma')
    icon(img, P.get('ikon', 'circle-x'), RED, 540, 1090, 260, u, 0.25, shake=14)
    return img

def dur_daftar(P): return 0.7 + 0.7 * (len(P['items']) - 1) + 1.0
def sc_daftar(u, P):
    """Daftar bergulir. P: judul, items[], ikon[] (satu per item), coret_pertama (bool). Kolom tetap, ikon sejajar tengah huruf."""
    items, icons = P['items'], P['ikon']; n = len(items)
    img = new(RED); f = FN('Bold', min(124, fitsize(max(items, key=len), 124, 700)))
    tag(img, u, MU, P.get('tag', 'YANG PERLU DIKETAHUI'))
    reveal(img, (540, 470), P['judul'], FN('Bold', fitsize(P['judul'], 52)), CR, seg(u, 0.1, 0.45), anchor='ma')
    moves = [0.7 + 0.7 * k for k in range(n - 1)]
    pos = sum(eio(seg(u, a, a + 0.28)) for a in moves)
    wmax = max(len(x) for x in items); fs = f.size; gx = 540 - (160 + wmax * ADV * fs) / 2; tx = gx + 160
    hb = f.getbbox('H'); xb = f.getbbox('x')
    for k, w in enumerate(items):
        d = k - pos
        if abs(d) > 1.4: continue
        y = 800 + d * 175; a = clamp(1 - abs(d) * 0.72)
        if k == 0: a *= eo(seg(u, 0.15, 0.45))
        cur = abs(d) < 0.5; last = k == n - 1
        col = (MU if last else CR) if cur else MU
        layer_text(img, (tx, y), w, f, col, alpha=a)
        icol = CR if (cur and not last) else MU
        icon(img, icons[k], icol, gx + 65, y + (hb[1] + hb[3]) / 2, 120, u, 0.15, alpha=a)
        if k == 0 and P.get('coret_pertama'):
            sp = eio(seg(u, 0.35, 0.55))
            if sp > 0:
                yy = y + (xb[1] + xb[3]) / 2; wl = f.getlength(w)
                ImageDraw.Draw(img).line([(tx - 6, yy), (tx - 6 + (wl + 12) * sp, yy)], fill=rgb(MU) + (int(255 * a),), width=9)
    return img

def dur_hitung(P): return 3.0
def sc_hitung(u, P):
    """Angka menghitung dari->ke, satuan berganti. P: dari, ke, satuan_a, satuan_b, penutup, ikon_a, ikon_b, tag."""
    img = new(CR); tag(img, u, RED, P.get('tag', 'YANG SEBENARNYA'), 0.15)
    icon(img, P['ikon_a'], RED, 540, 540, 190, u, 0.2, out=1.25); icon(img, P['ikon_b'], RED, 540, 540, 190, u, 1.45)
    p = eio(seg(u, 0.6, 1.3)); v = round(P['dari'] + (P['ke'] - P['dari']) * p)
    a = eo(seg(u, 0.15, 0.4))
    if a > 0: layer_text(img, (540, 680 + 30 * (1 - a)), str(v), FN('Bold', 300), RED, alpha=a, anchor='ma')
    sw = seg(u, 1.25, 1.55)
    reveal(img, (540, 1025), P['satuan_a'], FN('Bold', 84), DK, (seg(u, 0.25, 0.55) if sw <= 0 else 1 + sw), anchor='ma')
    reveal(img, (540, 1025), P['satuan_b'], FN('Bold', 84), DK, seg(u, 1.35, 1.65), anchor='ma')
    s = P['penutup']; sz = fitsize(s, 44, 880)
    typed(img, ((W - len(s) * ADV * sz) / 2, 1150), s, sz, RED, u, 1.7, 26, bold='BoldItalic', caret=RED)
    return img

def dur_langkah(P): return 0.45 * len(P['rows']) + 1.7
def sc_langkah(u, P):
    """Langkah 1-2-3 (ikon dalam lingkaran). P: tag, rows[{ikon, judul, sub}] (maks 4)."""
    rows = P['rows']; img = new(RED); d = ImageDraw.Draw(img); tag(img, u, MU, P.get('tag', 'LANGKAHNYA'), 0.15)
    n = len(rows); gap = 230 if n <= 3 else 200; y0 = 800 - (n * gap - 60) / 2
    wcol = max(len(r['judul']) for r in rows) * ADV * 96
    left = 540 - (128 + 40 + wcol) / 2
    for k, r in enumerate(rows):
        t0 = 0.3 + k * 0.45; y = y0 + k * gap
        wb = FN('Bold', 96).getbbox('Hj'); sb = FN('BoldItalic', 40).getbbox('ap')
        cx, cy = left + 64, y + (wb[1] + 118 + sb[3]) / 2
        p = eio(seg(u, t0, t0 + 0.4))
        if p > 0: d.arc((cx - 64, cy - 64, cx + 64, cy + 64), -90, -90 + 360 * p, fill=rgb(MU), width=5)
        icon(img, r['ikon'], CR, cx, cy, 74, u, t0 + 0.15)
        reveal(img, (left + 168, y), r['judul'], FN('Bold', 96), CR, seg(u, t0 + 0.1, t0 + 0.45))
        reveal(img, (left + 170, y + 118), r['sub'], FN('BoldItalic', 40), MU, seg(u, t0 + 0.35, t0 + 0.7))
    return img

SCENES = {'kata_besar': (sc_kata_besar, lambda P: 1.9), 'salah': (sc_salah, lambda P: 1.5), 'daftar': (sc_daftar, dur_daftar),
          'hitung': (sc_hitung, dur_hitung), 'langkah': (sc_langkah, dur_langkah)}


# ---------------------------------------------------------------- transisi + garis waktu
def push(a, b, p, axis):
    out = Image.new('RGB', (W, H))
    if axis == 'atas': o = int(H * p); out.paste(a.convert('RGB'), (0, -o)); out.paste(b.convert('RGB'), (0, H - o))
    else: o = int(W * p); out.paste(a.convert('RGB'), (-o, 0)); out.paste(b.convert('RGB'), (W - o, 0))
    return out

def stripes(a, b, u, n=6):
    m = np.zeros((H, W), 'float32'); bh = H // n
    for k in range(n):
        p = eio(seg(u, k * 0.05, k * 0.05 + 0.32)); m[k * bh:(k + 1) * bh, :int(W * p)] = 1
    return blend(a, b, m)

TR = {'lingkaran': 0.65, 'dorong_atas': 0.4, 'dorong_kiri': 0.4, 'garis': 0.55, 'banjir': 0.7}
ORIGINS = [(540, 1090), (160, 1560), (900, 1500), (314, 1082)]

def timeline(spec):
    """-> daftar (mulai, fungsi, param, transisi, durasi_trans). Intro 0-3.3 dtk; adegan pertama mulai 3.3 dengan banjir."""
    t = 3.3; out = []
    for k, a in enumerate(spec['adegan']):
        fn, dur = SCENES[a['tipe']]; tr = 'banjir' if k == 0 else a.get('trans', 'lingkaran')
        out.append((t, fn, a, tr, TR[tr])); t += dur(a)
    out.append((t, sc_penutup, spec['penutup'], 'lingkaran', TR['lingkaran']))
    return out, t + 2.3

def frame(i):
    t = i / FPS; tl = SPEC['_tl']
    if t < 5 / FPS: return cover().convert('RGB')
    if t < 3.3:
        img, (cx, cy, r) = intro(t); return blend(img, new(RED), circle_mask(cx, cy, r))
    k = max(j for j, s in enumerate(tl) if s[0] <= t); S, fn, P, tr, td = tl[k]; u = t - S
    cur = fn(u, P)
    if u >= td: return cur.convert('RGB')
    p = eio(u / td)
    if k == 0: return blend(intro(3.3)[0], cur, circle_mask(540, 960, 53 + 1500 * p ** 1.6))
    pv = tl[k - 1]; prev = pv[1](t - pv[0], pv[2])
    if tr == 'dorong_atas': return push(prev, cur, p, 'atas')
    if tr == 'dorong_kiri': return push(prev, cur, p, 'kiri')
    if tr == 'garis': return stripes(prev, cur, u)
    ox, oy = ORIGINS[k % len(ORIGINS)]
    return blend(prev, cur, circle_mask(ox, oy, 2300 * p ** 1.3))


# ---------------------------------------------------------------- penyiapan, cek, render
def prepare(spec):
    """Render ikon yang dipakai (maroon/putih/pink) dan muat sprite. Panggil sekali di proses utama."""
    sys.path.insert(0, os.path.join(ROOT, 'toolkit')); import lucide
    names = set()
    def scan(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k.startswith('ikon'): names.update(v if isinstance(v, list) else [v])
                else: scan(v)
        elif isinstance(o, list):
            for x in o: scan(x)
    scan(spec); names.add('circle-x'); names.discard(None)
    d = tempfile.mkdtemp(prefix='seri_ic_')
    lucide.render(d, ['%s:%s' % (n, c) for n in sorted(names) for c in (RED, CR, MU)])
    spec['_ic'] = d; spec['_tl'], spec['_T'] = timeline(spec)
    bind(spec)

def bind(spec):
    SPEC.clear(); SPEC.update(spec)
    for p in POSES: C[p + '_w'] = sprite(p, 330, DK); C[p + '_m'] = sprite(p, 330, CR)

def _work(a):
    i, d = a; frame(i).save(os.path.join(d, 'f_%05d.png' % i)); return i

def cek(spec, out, times=None):
    prepare(spec); T = spec['_T']
    times = times or [0, 1.5, 3.0, 3.6] + [round(s[0] + 0.25 * (s[3] != 'banjir') + 0.9, 2) for s in spec['_tl']] + [T - 0.2]
    ims = []
    for t in times:
        im = frame(min(int(T * FPS) - 1, int(t * FPS))).convert('RGB'); d = ImageDraw.Draw(im)
        d.rectangle((100, 235, 980, 1470), outline=(0, 160, 255), width=3); d.line([(540, 0), (540, H)], fill=(0, 200, 0), width=2)
        d.rectangle((940, 1150, 1080, 1920), outline=(255, 0, 255), width=3); ims.append(im.resize((216, 384)))
    cols = 9; rows = (len(ims) + cols - 1) // cols; sh = Image.new('RGB', (216 * cols, 384 * rows), (25, 25, 25))
    for k, im in enumerate(ims): sh.paste(im, ((k % cols) * 216, (k // cols) * 384))
    sh.save(out); print('ok', out, 'durasi %.1f dtk' % T)

def render(spec, out):
    prepare(spec); d = tempfile.mkdtemp(prefix='seri_fr_'); n = int(spec['_T'] * FPS)
    with Pool(2) as pl: list(pl.imap_unordered(_work, [(i, d) for i in range(n)], chunksize=4))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-framerate', str(FPS), '-i', os.path.join(d, 'f_%05d.png'), '-c:v', 'libx264',
                    '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], check=True)
    print('ok', out, '%.1f dtk' % spec['_T'])

CONTOH = {
  'seri': 'SALAH KAPRAH #01', 'handle': '@jerapahmerah_', 'intro': ['KERJA', 'KREATIF,', 'DIBANTU', 'AI.'],
  'sampul': {'baris': ['Prompt', 'panjang'], 'kata_a': '=', 'sorot': 'bagus?', 'pose': 'shock'},
  'adegan': [
    {'tipe': 'kata_besar', 'baris': ['Prompt', 'panjang'], 'kata_a': '=', 'sorot': 'bagus?', 'ikon': 'scroll-text'},
    {'tipe': 'salah', 'sub': 'panjang tidak sama dengan bagus.', 'trans': 'dorong_atas'},
    {'tipe': 'daftar', 'tag': 'YANG BIKIN HASIL BAGUS', 'judul': 'Prompt yang bagus itu', 'items': ['panjang.', 'jelas.', 'singkat.', 'spesifik.'],
     'ikon': ['scroll-text', 'eye', 'scissors', 'crosshair'], 'coret_pertama': True, 'trans': 'lingkaran'},
    {'tipe': 'hitung', 'dari': 500, 'ke': 3, 'satuan_a': 'kata', 'satuan_b': 'kalimat', 'ikon_a': 'file-text', 'ikon_b': 'zap',
     'penutup': 'hasilnya justru lebih tajam.', 'trans': 'garis'},
    {'tipe': 'langkah', 'tag': 'RUMUS 3 KALIMAT', 'rows': [
        {'ikon': 'target', 'judul': 'tujuan', 'sub': 'mau jadi apa.'}, {'ikon': 'users', 'judul': 'konteks', 'sub': 'untuk siapa.'},
        {'ikon': 'image', 'judul': 'contoh', 'sub': 'seperti ini.'}], 'trans': 'dorong_kiri'}],
  'penutup': {'baris1': 'simpan, coba besok pagi.', 'baris2': 'ikuti untuk seri berikutnya.', 'pose': 'wave'}}

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(1)
    if a[0] == 'contoh': print(json.dumps(CONTOH, ensure_ascii=False, indent=1))
    else:
        spec = json.load(open(a[1]))
        if a[0] == 'cek': cek(spec, a[2], [float(x) for x in a[3:]] or None)
        elif a[0] == 'render': render(spec, a[2])
