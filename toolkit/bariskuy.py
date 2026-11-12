#!/usr/bin/env python3
"""Mesin desain baris.kuy (BARIS KUY! | media info Paskibra Makassar) untuk Asmara. Instagram 4:5 (1080x1350).

Pakai:
    python3 toolkit/bariskuy.py spek.json keluaran/
    # -> slide_01.jpg ... (satu per item `slides`) + lembar.jpg (pratinjau)

Spek:
{
  "slides": [
    {"tipe": "a", "foto": "/path/foto1.jpg", "judul": "Pendaftaran Paskibraka 2026 resmi dibuka", "kredit": "COURTESY OF instagram.com/dispora.makassar"},
    {"tipe": "b", "foto": "/path/foto2.jpg", "judul": "...", "kredit": "..."},
    {"tipe": "meme", "foto": "/path/foto3.jpg", "atas": "Pendaftaran Paskibraka dibuka", "sub": "siswa kelas X be like"}
  ]
}
Tipe:
  a    = foto penuh, kotak merah melayang di bawah berisi judul, logo BARIS KUY! di pojok kanan atas kotak.
  b    = foto di atas, blok merah penuh di bawah berisi judul besar, logo di batas foto.
  meme = blok merah di atas (atas + sub), logo, lalu GAMBAR MEME DARI JERS apa adanya di bawah (tulisan meme, mis. "ON MY WAY",
         sudah ada di gambarnya; mesin TIDAK menambah teks apa pun di atas foto).
Judul otomatis HURUF BESAR. Teks yang tidak muat pada ukuran terkecil -> berhenti dengan GAGAL: perpendek.
DESAIN DIKUNCI oleh Jers (12 Nov 2026): jangan mengubah warna, font, atau tata letak.
"""
import os, sys, json, math
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FD = os.path.join(ROOT, 'assets', 'fonts')
W, H = 1080, 1350
RED, WH, INK = '#A8121B', '#FFFFFF', '#111111'
HB, MD = 'Poppins-Bold.ttf', 'Poppins-Medium.ttf'


def F(n, s):
    return ImageFont.truetype(os.path.join(FD, n), s)


_D = ImageDraw.Draw(Image.new('L', (1, 1)))


def wrap(t, f, w):
    o, c = [], ''
    for x in t.split():
        n = (c + ' ' + x).strip()
        if c and _D.textlength(n, font=f) > w:
            o.append(c); c = x
        else:
            c = n
    return o + ([c] if c else [])


def fit(t, fn, w, max_lines, smax, smin):
    for s in range(smax, smin - 1, -2):
        f = F(fn, s); ls = wrap(t, f, w)
        if len(ls) <= max_lines and all(_D.textlength(l, font=f) <= w for l in ls):
            return f, ls, s
    raise SystemExit('GAGAL: teks terlalu panjang: %r' % t[:90])


def cover(p, w, h, fy=.5):
    k = max(w / p.width, h / p.height)
    p = p.resize((int(p.width * k + .5), int(p.height * k + .5)), Image.LANCZOS)
    y = int((p.height - h) * fy)
    return p.crop(((p.width - w) // 2, y, (p.width - w) // 2 + w, y + h))


def load(p):
    if p and os.path.exists(p):
        return Image.open(p).convert('RGB')
    im = Image.new('RGB', (W, H), '#5A0A0F')
    return im


def star(d, cx, cy, r, col=WH):
    for i in range(6):
        a = i * math.pi / 3
        d.line((cx - math.cos(a) * r, cy - math.sin(a) * r, cx + math.cos(a) * r, cy + math.sin(a) * r), fill=col, width=max(3, int(r * .55)))
    d.ellipse((cx - r * .45, cy - r * .45, cx + r * .45, cy + r * .45), fill=col)


def logo(im, x, y, s):
    """BARIS / KUY! bertumpuk, miring, rata kanan di x."""
    L = Image.new('RGBA', (int(s * 5), int(s * 2.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(L); f = F(HB, s)
    d.text((L.width - 10, 0), 'BARIS', font=f, fill=WH, anchor='ra')
    d.text((L.width - 10, s * .92), 'KUY!', font=f, fill=WH, anchor='ra')
    L = L.transform(L.size, Image.AFFINE, (1, .18, -s * .3, 0, 1, 0), Image.BICUBIC)
    a = L.split()[3].point(lambda v: int(v * .45))
    sh = Image.new('RGBA', L.size, (40, 0, 0, 255)); sh.putalpha(a)
    im.paste(sh, (int(x - L.width + 4), int(y + 4)), sh)
    im.paste(L, (int(x - L.width), int(y)), L)


def credit(d, x, y, t, size=22):
    if t:
        f, ls, s = fit(t, MD, W - 2 * x, 2, size, 16)
        for l in ls:
            d.text((x, y), l, font=f, fill=WH); y += s * 1.3


def t_a(sl):
    im = cover(load(sl.get('foto')), W, H); d = ImageDraw.Draw(im)
    x0, x1 = 110, W - 110
    f, ls, s = fit(sl['judul'].upper(), HB, x1 - x0 - 80, 4, 50, 34)
    h = 74 + (len(ls) - 1) * s * 1.1 + s + 40
    y0 = H - 230 - h
    d.rectangle((x0, y0, x1, y0 + h), fill=RED)
    star(d, x0 + 44, y0 + 40, 14)
    y = y0 + 70
    for l in ls:
        d.text((x0 + 40, y), l, font=f, fill=WH); y += s * 1.1
    logo(im, x1 - 6, y0 - 118, 62)
    d = ImageDraw.Draw(im)
    credit(d, 70, H - 100, sl.get('kredit'))
    return im


def t_b(sl):
    PH = 760
    im = Image.new('RGB', (W, H), RED); im.paste(cover(load(sl.get('foto')), W, PH), (0, 0)); d = ImageDraw.Draw(im)
    f, ls, s = fit(sl['judul'].upper(), HB, W - 140, 5, 64, 38)
    star(d, 90, PH + 66, 16)
    y = PH + 104
    for l in ls:
        d.text((70, y), l, font=f, fill=WH); y += s * 1.08
    credit(d, 70, H - 92, sl.get('kredit'), 24)
    logo(im, W - 50, PH - 150, 70)
    return im


def outline(d, xy, t, f, fill=WH, stroke=INK, sw=8, anchor='ms'):
    d.text(xy, t, font=f, fill=fill, stroke_width=sw, stroke_fill=stroke, anchor=anchor)


def t_meme(sl):
    TOP = 330
    im = Image.new('RGB', (W, H), RED)
    im.paste(cover(load(sl.get('foto')), W, H - TOP, .35), (0, TOP)); d = ImageDraw.Draw(im)
    star(d, 86, 70, 15)
    f, ls, s = fit(sl.get('atas', '').upper(), HB, W - 300, 2, 64, 40)
    y = 110
    for l in ls:
        d.text((70, y), l, font=f, fill=WH); y += s * 1.06
    if sl.get('sub'):
        fs, l2, s2 = fit(sl['sub'].upper(), MD, W - 300, 1, 36, 24)
        d.text((70, y + 14), l2[0], font=fs, fill=WH)
    logo(im, W - 40, TOP - 130, 64)
    return im


TIPE = {'a': t_a, 'b': t_b, 'meme': t_meme}


def render(sp, out):
    os.makedirs(out, exist_ok=True)
    ps = []
    for i, sl in enumerate(sp['slides']):
        fn = TIPE.get(sl.get('tipe'))
        if not fn:
            raise SystemExit('GAGAL: tipe harus a, b, atau meme')
        p = os.path.join(out, 'slide_%02d.jpg' % (i + 1)); fn(sl).save(p, quality=90, optimize=True); ps.append(p)
    n = len(ps); sh = Image.new('RGB', (n * 415 + 10, 526), '#888888')
    for i, p in enumerate(ps):
        sh.paste(Image.open(p).resize((405, 506)), (10 + i * 415, 10))
    sh.save(os.path.join(out, 'lembar.jpg'), quality=85)
    return ps


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    for p in render(json.load(open(sys.argv[1])), sys.argv[2]):
        print(p)
