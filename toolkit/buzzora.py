#!/usr/bin/env python3
"""Mesin carousel BUZZORA (@buzzora.feed): 2 slide Instagram 4:5 (1080x1350).

Slide 1 = sampul berita, 6 varian tata letak yang dipakai BERGANTIAN (v1..v6).
Slide 2 = CTA tetap ("follow for more", foto keyboard + lonceng).
Font: Plus Jakarta Sans (ExtraBold judul, Medium teks). Warna: maroon + hitam + putih + merah muda.

Pakai:
    python3 toolkit/buzzora.py spek.json keluaran/ [foto.jpg]
    # -> slide_01.jpg            sampul (pakai foto bila diberikan; tanpa foto = latar grafis maroon)
    #    slide_01_overlay.png    lapisan sampul tanpa foto (area foto transparan) untuk tombol "Pasang foto" di kantor
    #    slide_02.jpg            CTA
    #    foto.json               {"x","y","w","h","bw","r"} kotak foto + hitam-putih? + radius sudut
    #    lembar.jpg              pratinjau dua slide

Spek:
{
  "varian": "v3",                    # v1..v6 (lihat VARIAN); wajib, pilih bergantian dari riwayat
  "akun": "@buzzora.feed",
  "kategori": "Berita Ekonomi",      # label kecil (v2, v5, v6)
  "judul": "Harga beras naik di 12 provinsi",   # 3-9 kata; otomatis HURUF BESAR
  "sorot": "naik",                   # kata/frasa di judul yang disorot (v1: baris berisi sorot diberi kotak; v4: kata dipil maroon)
  "sub": "Beras medium tembus Rp15 ribu per kilo, pemerintah siapkan operasi pasar.",  # 1 kalimat, maks ~18 kata
  "sumber": "Kompas"                 # nama sumber singkat untuk kaki slide
}
Teks yang tidak muat pada ukuran terkecil -> berhenti dengan GAGAL: perpendek.
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, 'assets', 'fonts')
CTA_BG = os.path.join(ROOT, 'assets', 'buzzora', 'cta_bg.jpg')
W, H = 1080, 1350
M = 72                                   # margin
MAR, MAR2, BLK, WH, ROSE, INK = '#8E1B2C', '#6E1222', '#0B0B0C', '#FFFFFF', '#F49AAA', '#111114'
XB, BD, MD = 'PlusJakartaSans-ExtraBold.ttf', 'PlusJakartaSans-Bold.ttf', 'PlusJakartaSans-Medium.ttf'
LEAD = .98                               # jarak antar baris judul (rapat)
VARIAN = {
    'v1': 'foto atas, judul tengah 3 baris, baris sorot dalam kotak maroon, ringkasan dalam kotak putih',
    'v2': 'foto penuh + gradasi gelap, label kategori, judul besar rata kiri',
    'v3': 'foto atas, pita BREAKING NEWS, panel putih berisi judul gelap dengan garis aksen',
    'v4': 'latar hitam, label BREAKING NEWS, foto berbingkai bulat, kartu putih dengan kata sorot dipil maroon',
    'v5': 'foto penuh hitam-putih digelapkan, pita gelap berisi judul merah muda rata kiri',
    'v6': 'foto penuh + gradasi, label kategori di tengah, judul merah muda rata tengah',
}


def F(n, s):
    return ImageFont.truetype(os.path.join(FD, n), s)


_D = ImageDraw.Draw(Image.new('L', (1, 1)))


def tw(t, f):
    return _D.textlength(t, font=f)


def wrap(t, f, width):
    out, cur = [], ''
    for w in t.split():
        c = (cur + ' ' + w).strip()
        if cur and tw(c, f) > width:
            out.append(cur); cur = w
        else:
            cur = c
    return out + ([cur] if cur else [])


def fit(t, fn, width, max_lines, smax, smin, min_lines=1):
    for s in range(smax, smin - 1, -2):
        f = F(fn, s)
        ls = wrap(t, f, width)
        if len(ls) <= max_lines and len(ls) >= min(min_lines, len(t.split())) and all(tw(l, f) <= width for l in ls):
            return f, ls, s
    raise SystemExit('GAGAL: teks terlalu panjang: %r' % t[:90])


def cap_box(f):
    """tinggi huruf kapital & offset atas (untuk menaruh kotak tepat di belakang teks)"""
    b = f.getbbox('HX')
    return b[1], b[3]


# ---------- elemen bersama ----------
def tag(d, x=M, y=56):
    f = F(XB, 30)
    a = tw('BUZZORA', f)
    d.rectangle((x, y, x + a + 28, y + 52), fill=BLK)
    d.text((x + 14, y + 26), 'BUZZORA', font=f, fill=WH, anchor='lm')
    b = tw('.FEED', f)
    d.rectangle((x + a + 28, y, x + a + 28 + b + 24, y + 52), fill=MAR)
    d.text((x + a + 40, y + 26), '.FEED', font=f, fill=WH, anchor='lm')


def foot(d, src):
    y = H - 88
    f = F(BD, 26)
    t = 'Baca di caption'
    w = tw(t, f)
    d.rounded_rectangle((M, y - 30, M + w + 86, y + 30), 10, fill=MAR)
    d.text((M + 22, y), t, font=f, fill=WH, anchor='lm')
    ax = M + w + 40
    d.line((ax, y, ax + 24, y), fill=WH, width=4)
    d.line((ax + 13, y - 11, ax + 24, y), fill=WH, width=4)
    d.line((ax + 13, y + 11, ax + 24, y), fill=WH, width=4)
    if src:
        d.text((W - M, y), 'Sumber: ' + src, font=F(MD, 24), fill=WH, anchor='rm')


def chip(d, x, y, t, anchor='l', fill=MAR, fg=WH):
    f = F(BD, 26)
    w = tw(t, f) + 40
    if anchor == 'c':
        x -= w / 2
    d.rounded_rectangle((x, y, x + w, y + 50), 10, fill=fill)
    d.text((x + 20, y + 25), t, font=f, fill=fg, anchor='lm')
    return w


def lines_text(d, x, y, ls, f, s, fill, anchor='l', lead=LEAD):
    for l in ls:
        if anchor == 'c':
            d.text((x, y), l, font=f, fill=fill, anchor='ma')
        else:
            d.text((x, y), l, font=f, fill=fill)
        y += s * lead
    return y


def sub_text(d, x, y, t, width, fill, anchor='l', size=30, max_lines=3):
    f, ls, s = fit(t, MD, width, max_lines, size, 24)
    for l in ls:
        d.text((x, y), l, font=f, fill=fill, anchor='ma' if anchor == 'c' else 'la')
        y += s * 1.32
    return y


def shade(L, y0, y1, a1=235, col=(11, 11, 12)):
    g = Image.new('L', (1, H), 0)
    for y in range(H):
        g.putpixel((0, y), 0 if y < y0 else (a1 if y >= y1 else int(a1 * ((y - y0) / (y1 - y0)) ** 1.2)))
    S = Image.new('RGBA', (W, H), col + (255,))
    S.putalpha(g.resize((W, H)))
    return Image.alpha_composite(L, S)


# ---------- varian ----------
def v1(sp):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L); d.rectangle((0, 640, W, H), fill=BLK)
    L = shade(L, 400, 640, 255); d = ImageDraw.Draw(L)
    tag(d)
    f, ls, s = fit(sp['judul'].upper(), XB, W - 2 * M - 40, 3, 84, 54, 2)
    k = next((i for i, l in enumerate(ls) if sp.get('sorot') and sp['sorot'].upper() in l), min(1, len(ls) - 1))
    top, bot = cap_box(f)
    f2, l2, s2 = fit(sp['sub'], MD, W - 2 * M - 120, 3, 30, 24)
    hb = len(l2) * s2 * 1.32 + 44
    hj = (len(ls) - 1) * s * 1.06 + bot - top + 28
    y = 600 + max(0, (H - 160 - 600 - (hj + 40 + hb)) / 2) - top + 14
    PAD, GAP = 20, 30
    for i, l in enumerate(ls):
        if i == k:
            y += GAP if i else 0
            bx = d.textbbox((W / 2, y), l, font=f, anchor='ma')
            cy = (y + top + y + bot) / 2                    # tengah huruf kapital
            hh = (bot - top) / 2 + PAD
            d.rectangle((bx[0] - PAD - 6, cy - hh, bx[2] + PAD + 6, cy + hh), fill=MAR)
        d.text((W / 2, y), l, font=f, fill=WH, anchor='ma')
        y += s * 1.06 + (GAP if i == k else 0)
    y = y - s * 1.06 - (GAP if k == len(ls) - 1 else 0) + bot + 14 + 40
    d.rounded_rectangle((M + 30, y, W - M - 30, y + hb), 12, fill=WH)
    yy = y + 22
    for l in l2:
        d.text((W / 2, yy), l, font=f2, fill=INK, anchor='ma'); yy += s2 * 1.32
    foot(d, sp.get('sumber'))
    return L, dict(x=0, y=0, w=W, h=640, bw=False, r=0)


def v2(sp):
    L = shade(Image.new('RGBA', (W, H), (0, 0, 0, 0)), 330, 1010)
    d = ImageDraw.Draw(L); tag(d)
    f, ls, s = fit(sp['judul'].upper(), XB, W - 2 * M, 4, 120, 70, 2)
    f2, l2, s2 = fit(sp['sub'], MD, W - 2 * M - 160, 3, 30, 24)
    hs = len(l2) * s2 * 1.32
    yb = H - 160 - hs                     # atas ringkasan
    yt = yb - 36 - len(ls) * s * LEAD     # atas judul
    chip(d, M, yt - 74, sp.get('kategori') or 'Berita')
    lines_text(d, M, yt, ls, f, s, WH)
    y = yb
    for l in l2:
        d.text((M, y), l, font=f2, fill=WH); y += s2 * 1.32
    foot(d, sp.get('sumber'))
    return L, dict(x=0, y=0, w=W, h=H, bw=False, r=0)


def v3(sp):
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    PY = 560
    d.rectangle((0, PY + 70, W, H - 150), fill=WH)
    d.rectangle((0, H - 150, W, H), fill=BLK)
    fb = F(XB, 40)
    wb = tw('BREAKING NEWS', fb)
    d.polygon([(0, PY), (M + wb + 40, PY), (M + wb + 90, PY + 70), (0, PY + 70)], fill=MAR)
    d.text((M, PY + 35), 'BREAKING NEWS', font=fb, fill=WH, anchor='lm')
    tag(d)
    f, ls, s = fit(sp['judul'].upper(), XB, W - 2 * M - 40, 3, 86, 56, 2)
    top, bot = cap_box(f)
    hh = (len(ls) - 1) * s * LEAD + bot
    fs_, ls_, ss_ = fit(sp['sub'], MD, W - 2 * M - 40, 3, 31, 24)
    tot = hh - top + 40 + len(ls_) * ss_ * 1.32
    y = PY + 70 + (H - 150 - PY - 70 - tot) / 2 - top
    d.rectangle((M, y + top, M + 8, y + hh), fill=MAR)
    lines_text(d, M + 36, y, ls, f, s, INK)
    y += hh + 40
    sub_text(d, M, y, sp['sub'], W - 2 * M - 40, '#2A2A2E', size=31)
    foot(d, sp.get('sumber'))
    return L, dict(x=0, y=0, w=W, h=PY + 70, bw=False, r=0)


def v4(sp):
    L = Image.new('RGBA', (W, H), (11, 11, 12, 255))
    PX0, PY0, PX1, PY1 = 60, 150, W - 60, 690
    hole = Image.new('L', (W, H), 255)
    ImageDraw.Draw(hole).rounded_rectangle((PX0, PY0, PX1, PY1), 36, fill=0)
    L.putalpha(hole)
    d = ImageDraw.Draw(L)
    fb = F(XB, 40); wb = tw('BREAKING NEWS', fb)
    d.rounded_rectangle((W / 2 - wb / 2 - 30, 96, W / 2 + wb / 2 + 30, 176), 12, fill=MAR)
    d.text((W / 2, 136), 'BREAKING NEWS', font=fb, fill=WH, anchor='mm')
    f, ls, s = fit(sp['judul'].upper(), XB, W - 2 * 60 - 100, 3, 74, 48, 2)
    f2, l2, s2 = fit(sp['sub'], MD, W - 2 * 60 - 120, 3, 29, 24)
    top, bot = cap_box(f)
    hc = 46 + (len(ls) - 1) * s * 1.06 + bot + 30 + len(l2) * s2 * 1.32 + 40
    y0 = PY1 + 40 + max(0, (H - 150 - PY1 - 40 - hc) / 2)
    d.rounded_rectangle((60, y0, W - 60, y0 + hc), 36, fill=WH)
    y = y0 + 46 - top
    sor = (sp.get('sorot') or '').upper()
    for l in ls:
        if sor and sor in l:
            a, _, b = l.partition(sor)
            parts = [(a.strip(), False), (sor, True), (b.strip(), False)]
        else:
            parts = [(l, False)]
        parts = [p for p in parts if p[0]]
        gap = 18
        tot = sum(tw(t, f) + (28 if h else 0) for t, h in parts) + gap * (len(parts) - 1)
        x = W / 2 - tot / 2
        for t, h in parts:
            w = tw(t, f)
            if h:
                d.rounded_rectangle((x, y + top - 12, x + w + 28, y + bot + 12), 12, fill=MAR)
                d.text((x + 14, y), t, font=f, fill=WH); x += w + 28 + gap
            else:
                d.text((x, y), t, font=f, fill=INK); x += w + gap
        y += s * 1.06
    y = y - s * 1.06 + bot + 30
    for l in l2:
        d.text((W / 2, y), l, font=f2, fill='#2A2A2E', anchor='ma'); y += s2 * 1.32
    foot(d, sp.get('sumber'))
    return L, dict(x=PX0, y=PY0, w=PX1 - PX0, h=PY1 - PY0, bw=False, r=36)


def v5(sp):
    L = Image.new('RGBA', (W, H), (11, 11, 12, 120))
    d = ImageDraw.Draw(L)
    f, ls, s = fit(sp['judul'].upper(), XB, W - 2 * M, 3, 96, 60, 2)
    f2, l2, s2 = fit(sp['sub'], MD, W - 2 * M - 120, 2, 30, 24)
    top, bot = cap_box(f)
    hb = 40 + 50 + 30 + (len(ls) - 1) * s * LEAD + bot + 30 + len(l2) * s2 * 1.32 + 40
    y0 = 560
    d.rectangle((0, y0, W, y0 + hb), fill=(11, 11, 12, 245))
    tag(d)
    d.text((M, y0 + 40), sp.get('kategori') or 'Berita', font=F(BD, 30), fill=WH)
    y = y0 + 120 - top
    y = lines_text(d, M, y, ls, f, s, ROSE)
    y = y - s * LEAD + bot + 30
    for l in l2:
        d.text((M, y), l, font=f2, fill=WH); y += s2 * 1.32
    foot(d, sp.get('sumber'))
    return L, dict(x=0, y=0, w=W, h=H, bw=True, r=0)


def v6(sp):
    L = shade(Image.new('RGBA', (W, H), (0, 0, 0, 0)), 470, 1000, 245)
    d = ImageDraw.Draw(L); tag(d)
    f, ls, s = fit(sp['judul'].upper(), XB, W - 2 * M, 3, 96, 60, 2)
    f2, l2, s2 = fit(sp['sub'], MD, W - 2 * M - 160, 3, 31, 24)
    hs = len(l2) * s2 * 1.32
    yb = H - 170 - hs
    yt = yb - 40 - len(ls) * s * LEAD
    chip(d, W / 2, yt - 76, sp.get('kategori') or 'Berita', 'c')
    lines_text(d, W / 2, yt, ls, f, s, ROSE, 'c')
    y = yb
    for l in l2:
        d.text((W / 2, y), l, font=f2, fill=WH, anchor='ma'); y += s2 * 1.32
    foot(d, sp.get('sumber'))
    return L, dict(x=0, y=0, w=W, h=H, bw=False, r=0)


VFN = {'v1': v1, 'v2': v2, 'v3': v3, 'v4': v4, 'v5': v5, 'v6': v6}


def fallback(w, h):
    im = Image.new('RGB', (w, h), '#1A0509')
    g = Image.new('RGB', (w, h), '#1A0509'); dd = ImageDraw.Draw(g)
    dd.ellipse((-w * .4, -h * .5, w * .6, h * .5), fill=MAR)
    im = Image.blend(im, g.filter(ImageFilter.GaussianBlur(160)), 1.0)
    dd = ImageDraw.Draw(im)
    for i in range(-h, w, 40):
        dd.line((i, 0, i + h, h), fill='#24080D', width=2)
    return im


def cover(p, w, h):
    k = max(w / p.width, h / p.height)
    p = p.resize((int(p.width * k + .5), int(p.height * k + .5)), Image.LANCZOS)
    return p.crop(((p.width - w) // 2, (p.height - h) // 2, (p.width - w) // 2 + w, (p.height - h) // 2 + h))


def compose(L, box, photo=None):
    base = Image.new('RGB', (W, H), BLK)
    p = cover(Image.open(photo).convert('RGB'), box['w'], box['h']) if photo else fallback(box['w'], box['h'])
    if box['bw']:
        p = ImageOps.grayscale(p).convert('RGB')
    base.paste(p, (box['x'], box['y']))
    return Image.alpha_composite(base.convert('RGBA'), L).convert('RGB')


def cta(akun):
    b = Image.open(CTA_BG).convert('RGB')
    b = b.resize((W, int(b.height * W / b.width)), Image.LANCZOS)
    SH = 300
    base = b.crop((0, 0, W, 60)).resize((W, H)).filter(ImageFilter.GaussianBlur(40))
    ph = Image.new('RGB', (W, H)); ph.paste(b.crop((0, 0, W, H - SH)), (0, SH))
    mk = Image.new('L', (W, H), 0); mk.paste(Image.linear_gradient('L').resize((W, 260)), (0, SH)); mk.paste(255, (0, SH + 260, W, H))
    im = Image.composite(ph, base, mk)
    g = Image.new('L', (1, H), 0)
    for y in range(H - 280, H):
        g.putpixel((0, y), int(210 * (y - (H - 280)) / 280))
    im.paste(Image.new('RGB', (W, H), '#0B0507'), (0, 0), g.resize((W, H)))
    d = ImageDraw.Draw(im)
    C, P = '#F7E3E6', (244, 154, 170)
    d.text((W / 2, 330), 'follow for more', font=F(XB, 96), fill=C, anchor='ms')
    f2 = F(MD, 50); t = 'kabar tercepat tiap hari'; w = tw(t, f2); x = W / 2 - (w + 62) / 2
    d.line((x + 4, 398, x + 38, 364), fill=P, width=7); d.line((x + 12, 364, x + 40, 364), fill=P, width=7); d.line((x + 38, 362, x + 38, 390), fill=P, width=7)
    d.text((x + 62, 400), t, font=f2, fill=C, anchor='ls')
    fl = F(MD, 30); y = H - 84
    d.text((M + 8, y), 'Berita Viral', font=fl, fill=WH, anchor='lm')
    w2 = tw(akun, fl)
    d.rounded_rectangle((W - M - 8 - w2 - 56, y - 31, W - M - 8, y + 31), 31, outline=WH, width=3)
    d.text((W - M - 8 - w2 / 2 - 28, y), akun, font=fl, fill=WH, anchor='mm')
    return im


def render(sp, out, photo=None):
    os.makedirs(out, exist_ok=True)
    v = sp.get('varian') or 'v1'
    if v not in VFN:
        raise SystemExit('GAGAL: varian harus v1..v6')
    L, box = VFN[v](sp)
    L.save(os.path.join(out, 'slide_01_overlay.png'))
    json.dump(box, open(os.path.join(out, 'foto.json'), 'w'))
    p1 = os.path.join(out, 'slide_01.jpg'); compose(L, box, photo).save(p1, quality=90, optimize=True)
    p2 = os.path.join(out, 'slide_02.jpg'); cta(sp.get('akun') or '@buzzora.feed').save(p2, quality=90, optimize=True)
    sh = Image.new('RGB', (2 * 405 + 30, 526), '#888888')
    for i, p in enumerate((p1, p2)):
        sh.paste(Image.open(p).resize((405, 506)), (10 + i * 415, 10))
    sh.save(os.path.join(out, 'lembar.jpg'), quality=85)
    return [p1, p2]


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    for p in render(json.load(open(sys.argv[1])), sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None):
        print(p)
