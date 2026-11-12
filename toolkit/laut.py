#!/usr/bin/env python3
"""Mesin carousel berita Laut (Instagram 4:5, 1080x1350).

Pakai:
    python3 toolkit/laut.py spek.json keluaran/
    # -> keluaran/slide_01.jpg ... slide_NN.jpg (JPG kualitas 88) + keluaran/lembar.jpg (pratinjau semua slide)

Spek (JSON):
{
  "akun": "@namaakun",              # boleh kosong; tampil di pojok kiri atas tiap slide
  "nama": "NAMA MEDIA",             # boleh kosong; wordmark di slide penutup
  "tema": "laut",                   # laut | pasir | arang | merah (palet, lihat TEMA)
  "kategori": "EKONOMI",            # chip di sampul, maks 18 huruf
  "waktu": "12 Nov 2026 · 09.40 WITA",
  "slides": [
    {"tipe": "sampul", "judul": "Harga *beras* naik lagi di 12 provinsi", "sub": "1 kalimat penjelas, boleh kosong",
     "ikon": "wheat"},
    {"tipe": "isi", "label": "Apa yang terjadi", "judul": "maks 2 baris", "teks": "2-4 kalimat pendek.", "ikon": "trending-up"},
    {"tipe": "angka", "label": "Angkanya", "angka": "Rp15.400", "satuan": "per kg", "teks": "1-2 kalimat konteks.", "ikon": "receipt"},
    {"tipe": "poin", "label": "Yang perlu kamu tahu", "poin": ["3-4 poin pendek"], "ikon": "list-checks"},
    {"tipe": "penutup", "tanya": "Pertanyaan pendek untuk komentar?", "sumber": ["Kompas", "BPS"]}
  ]
}
Kata di antara *bintang* diwarnai aksen. Ikon = nama berkas di assets/lucide (tanpa .svg).
Teks yang tidak muat pada ukuran huruf terkecil membuat skrip berhenti dengan pesan GAGAL: perpendek teksnya.
"""
import os, sys, json, re, glob, tempfile
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'assets', 'fonts')
W, H = 1080, 1350
MX = 84                      # margin kiri-kanan
TOP, BOT = 150, 1350 - 130   # area isi

TEMA = {
    'laut':  dict(bg='#0D2433', bg2='#12344A', ink='#F3EFE6', mute='#8FB1C4', acc='#FF6B3D', chip='#FF6B3D', chip_fg='#0D2433', grid='#16405A'),
    'pasir': dict(bg='#F3EEE3', bg2='#E8E0CF', ink='#14212B', mute='#6F7A80', acc='#D2462B', chip='#14212B', chip_fg='#F3EEE3', grid='#E2D9C6'),
    'arang': dict(bg='#141518', bg2='#1E2025', ink='#F1F1EE', mute='#9A9DA4', acc='#F5C518', chip='#F5C518', chip_fg='#141518', grid='#23262C'),
    'merah': dict(bg='#B3261E', bg2='#C2332A', ink='#FFF6F0', mute='#F2B8AE', acc='#FFD25A', chip='#FFF6F0', chip_fg='#B3261E', grid='#BE3028'),
}


def F(name, size):
    return ImageFont.truetype(os.path.join(FONT, name), size)


BOLD, MED, REG, MONO = 'InterDisplay-Bold.otf', 'Inter-Medium.otf', 'Inter-Regular.otf', 'SpaceMono-Bold.ttf'


def tokens(s):
    """'Harga *beras* naik' -> [('Harga',0),('beras',1),('naik',0)]"""
    out, hl = [], False
    for part in re.split(r'(\*)', s or ''):
        if part == '*':
            hl = not hl
            continue
        for w in part.split():
            out.append((w, hl))
    return out


def wrap(tk, font, width, draw):
    lines, cur = [], []
    for w, h in tk:
        test = ' '.join(x for x, _ in cur + [(w, h)])
        if cur and draw.textlength(test, font=font) > width:
            lines.append(cur)
            cur = [(w, h)]
        else:
            cur.append((w, h))
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, fname, width, max_h, smax, smin, lh=1.12, max_lines=99):
    tk = tokens(text)
    for s in range(smax, smin - 1, -2):
        f = F(fname, s)
        ls = wrap(tk, f, width, draw)
        if any(draw.textlength(' '.join(w for w, _ in l), font=f) > width for l in ls):
            continue
        if len(ls) <= max_lines and len(ls) * s * lh <= max_h:
            return f, ls, s
    raise SystemExit('GAGAL: teks terlalu panjang untuk kotaknya: %r' % (text[:80],))


def put_lines(draw, x, y, lines, f, s, col, acc, lh=1.12):
    sp = draw.textlength(' ', font=f)
    for l in lines:
        xx = x
        for w, h in l:
            draw.text((xx, y), w, font=f, fill=acc if h else col)
            xx += draw.textlength(w, font=f) + sp
        y += s * lh
    return y


IC_CACHE = {}


def ikon(name, col, size):
    key = (name, col, size)
    if key in IC_CACHE:
        return IC_CACHE[key]
    sys.path.insert(0, os.path.join(ROOT, 'toolkit'))
    import lucide
    d = tempfile.mkdtemp()
    p = lucide.render(d, ['%s:%s' % (name, col)], size=size, stroke=1.5)[0]
    im = Image.open(p).convert('RGBA')
    IC_CACHE[key] = im
    return im


def base(T, akun, n, N, waktu=None):
    im = Image.new('RGB', (W, H), T['bg'])
    d = ImageDraw.Draw(im)
    for x in range(0, W, 54):                      # grid titik tipis
        for y in range(0, H, 54):
            d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=T['grid'])
    f = F(MONO, 26)
    if akun:
        d.text((MX, 64), akun, font=f, fill=T['ink'])
    d.text((W - MX, 64), '%02d/%02d' % (n, N), font=f, fill=T['mute'], anchor='ra')
    d.line((MX, 112, W - MX, 112), fill=T['mute'], width=2)
    if waktu:
        d.text((MX, H - 78), waktu, font=F(MONO, 22), fill=T['mute'])
    return im, d


def watermark(im, name, T, size, xy, alpha=.10):
    try:
        ic = ikon(name, T['ink'], size)
    except Exception:
        return
    a = ic.split()[3].point(lambda v: int(v * alpha))
    ic2 = ic.copy(); ic2.putalpha(a)
    im.paste(ic2, xy, ic2)


def badge_icon(im, d, name, T, x, y, s=96):
    try:
        ic = ikon(name, T['chip_fg'], int(s * .62))
    except Exception:
        return
    d.rounded_rectangle((x, y, x + s, y + s), 22, fill=T['chip'])
    im.paste(ic, (int(x + s * .19), int(y + s * .19)), ic)


def s_sampul(sl, T, spec, n, N):
    im, d = base(T, spec.get('akun'), n, N, spec.get('waktu'))
    watermark(im, sl.get('ikon') or 'newspaper', T, 620, (W - 560, 560), .08)
    kat = (spec.get('kategori') or 'BERITA').upper()[:18]
    f = F(MONO, 30)
    tw = d.textlength(kat, font=f)
    d.rounded_rectangle((MX, 190, MX + tw + 44, 246), 10, fill=T['chip'])
    d.text((MX + 22, 218), kat, font=f, fill=T['chip_fg'], anchor='lm')
    fh, ls, s = fit(d, sl['judul'], BOLD, W - 2 * MX, 640, 118, 64, 1.06, 7)
    y = 300
    y = put_lines(d, MX, y, ls, fh, s, T['ink'], T['acc'], 1.06)
    if sl.get('sub'):
        fs, l2, s2 = fit(d, sl['sub'], MED, W - 2 * MX, 1080 - y - 40, 40, 28, 1.3, 4)
        put_lines(d, MX, y + 36, l2, fs, s2, T['mute'], T['acc'], 1.3)
    d.text((W - MX, H - 78), 'geser  →', font=F(MONO, 24), fill=T['ink'], anchor='ra')
    return im


def s_isi(sl, T, spec, n, N):
    im, d = base(T, spec.get('akun'), n, N)
    if sl.get('ikon'):
        badge_icon(im, d, sl['ikon'], T, W - MX - 96, 170)
    d.text((MX, 196), (sl.get('label') or '').upper()[:28], font=F(MONO, 28), fill=T['acc'])
    th = 0
    if sl.get('judul'):
        fh, ls, s = fit(d, sl['judul'], BOLD, W - 2 * MX, 320, 84, 52, 1.08, 3)
        th = len(ls) * s * 1.08 + 44
    ft, lt, st = fit(d, sl.get('teks', ''), MED, W - 2 * MX, 1150 - 300 - th, 52, 30, 1.38)
    tot = th + len(lt) * st * 1.38
    y = 300 + max(0, (1150 - 300 - tot) * .38)
    if sl.get('judul'):
        y = put_lines(d, MX, y, ls, fh, s, T['ink'], T['acc'], 1.08) + 44
    put_lines(d, MX, y, lt, ft, st, T['ink'], T['acc'], 1.38)
    return im


def s_angka(sl, T, spec, n, N):
    im, d = base(T, spec.get('akun'), n, N)
    if sl.get('ikon'):
        badge_icon(im, d, sl['ikon'], T, W - MX - 96, 170)
    d.text((MX, 196), (sl.get('label') or '').upper()[:28], font=F(MONO, 28), fill=T['acc'])
    fa, la, sa = fit(d, sl['angka'], BOLD, W - 2 * MX, 300, 220, 96, 1.0, 1)
    d.text((MX, 330), sl['angka'], font=fa, fill=T['acc'])
    y = 330 + sa * 1.2
    if sl.get('satuan'):
        d.text((MX, y), sl['satuan'], font=F(MED, 44), fill=T['ink'])
        y += 80
    d.line((MX, y + 20, MX + 160, y + 20), fill=T['acc'], width=6)
    ft, lt, st = fit(d, sl.get('teks', ''), MED, W - 2 * MX, TOP + 1000 - y - 70, 46, 30, 1.38)
    put_lines(d, MX, y + 70, lt, ft, st, T['ink'], T['acc'], 1.38)
    return im


def s_poin(sl, T, spec, n, N):
    im, d = base(T, spec.get('akun'), n, N)
    if sl.get('ikon'):
        badge_icon(im, d, sl['ikon'], T, W - MX - 96, 170)
    d.text((MX, 196), (sl.get('label') or '').upper()[:28], font=F(MONO, 28), fill=T['acc'])
    pts = sl.get('poin') or []
    if not 2 <= len(pts) <= 5:
        raise SystemExit('GAGAL: slide poin butuh 2-5 poin')
    room = (1150 - 300) / len(pts) - 56
    lay = [fit(d, p, MED, W - 2 * MX - 96, room, 50, 30, 1.3) for p in pts]
    tot = sum(len(l) * s * 1.3 + 56 for f, l, s in lay) - 56
    y = 300 + max(0, (1150 - 300 - tot) * .38)
    for i, (fp, lp, sp) in enumerate(lay):
        d.text((MX, y + 6), '%02d' % (i + 1), font=F(MONO, 36), fill=T['acc'])
        y = put_lines(d, MX + 96, y, lp, fp, sp, T['ink'], T['acc'], 1.3) + 56
        if i < len(lay) - 1:
            d.line((MX + 96, y - 30, W - MX, y - 30), fill=T['mute'], width=1)
    return im


def s_penutup(sl, T, spec, n, N):
    im, d = base(T, spec.get('akun'), n, N)
    nama = spec.get('nama') or ''
    if nama:
        d.text((W / 2, 300), nama.upper(), font=F(BOLD, 64), fill=T['ink'], anchor='mm')
    if sl.get('tanya'):
        fq, lq, sq = fit(d, sl['tanya'], BOLD, W - 2 * MX, 420, 76, 48, 1.1, 5)
        y = 470
        put_lines(d, MX, y, lq, fq, sq, T['ink'], T['acc'], 1.1)
    d.rounded_rectangle((MX, 960, W - MX, 1050), 18, fill=T['chip'])
    d.text((W / 2, 1005), 'Tulis pendapatmu di komentar', font=F(MED, 36), fill=T['chip_fg'], anchor='mm')
    src = sl.get('sumber') or []
    if src:
        fs, ls, ss = fit(d, 'Sumber: ' + ', '.join(src), REG, W - 2 * MX, 110, 26, 20, 1.3, 3)
        put_lines(d, MX, 1090, ls, fs, ss, T['mute'], T['mute'], 1.3)
    if spec.get('akun'):
        d.text((W / 2, H - 78), 'ikuti ' + spec['akun'] + ' untuk kabar tercepat', font=F(MONO, 24), fill=T['ink'], anchor='mm')
    return im


TIPE = {'sampul': s_sampul, 'isi': s_isi, 'angka': s_angka, 'poin': s_poin, 'penutup': s_penutup}


def render(spec, out):
    os.makedirs(out, exist_ok=True)
    T = TEMA.get(spec.get('tema') or 'laut', TEMA['laut'])
    N = len(spec['slides'])
    if not 3 <= N <= 8:
        raise SystemExit('GAGAL: carousel harus 3-8 slide')
    paths = []
    for i, sl in enumerate(spec['slides']):
        fn = TIPE.get(sl.get('tipe'))
        if not fn:
            raise SystemExit('GAGAL: tipe slide tidak dikenal: %r' % sl.get('tipe'))
        im = fn(sl, T, spec, i + 1, N)
        p = os.path.join(out, 'slide_%02d.jpg' % (i + 1))
        im.save(p, quality=88, optimize=True)
        paths.append(p)
    th = [Image.open(p).resize((270, 338)) for p in paths]
    sheet = Image.new('RGB', (270 * len(th) + 10 * (len(th) + 1), 358), '#888888')
    for i, t in enumerate(th):
        sheet.paste(t, (10 + i * 280, 10))
    sheet.save(os.path.join(out, 'lembar.jpg'), quality=85)
    return paths


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    for p in render(json.load(open(sys.argv[1])), sys.argv[2]):
        print(p)
