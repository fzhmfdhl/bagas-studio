#!/usr/bin/env python3
"""Mesin carousel BUZZORA (gaya media berita cepat ala USS Feeds), Instagram 4:5, 1080x1350, 2 slide.

Pakai:
    python3 toolkit/buzzora.py spek.json keluaran/
    # -> keluaran/slide_01.jpg      sampul berita (latar grafis maroon, tanpa foto)
    #    keluaran/slide_01_overlay.png  lapisan sampul dengan area foto TRANSPARAN (kantor menempelkan foto dari Jers di bawahnya)
    #    keluaran/slide_02.jpg      CTA follow
    #    keluaran/lembar.jpg        pratinjau dua slide berdampingan

Spek (JSON):
{
  "akun": "@buzzora",
  "kategori": "VIRAL",                         # chip kecil, maks 16 huruf
  "judul": "USS JAKARTA",                      # baris besar, 1-4 kata, otomatis HURUF BESAR
  "sub": "Hadirkan 270 brand lifestyle & diskon sneakers jadi Rp50 ribu, weekend ini",  # 1 kalimat, maks ~16 kata
  "ikon": "footprints",                        # ikon Lucide untuk latar grafis bila tanpa foto
  "lokasi": "Jakarta"                          # opsional, tampil kecil di atas kotak judul
}
Teks yang tidak muat pada ukuran terkecil -> berhenti dengan GAGAL: perpendek.
"""
import os, sys, json, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'assets', 'fonts')
W, H = 1080, 1350
MAROON, DEEP, INK, CREAM, WHITE = '#7A0F1F', '#2B0710', '#14060A', '#F7EBDD', '#FFFFFF'
BOX = (56, 846, W - 56, 1190)          # kotak judul (x0, y0, x1, y1); bagian bawah boleh tumbuh
PHOTO = (0, 0, W, H)                    # area foto = penuh (di bawah overlay)


def F(n, s):
    return ImageFont.truetype(os.path.join(FONT, n), s)


HEAVY, BOLD, MED, MONO = 'Poppins-Bold.ttf', 'InterDisplay-Bold.otf', 'Poppins-Medium.ttf', 'SpaceMono-Bold.ttf'


def wrap(d, text, f, width):
    out, cur = [], ''
    for w in text.split():
        t = (cur + ' ' + w).strip()
        if cur and d.textlength(t, font=f) > width:
            out.append(cur); cur = w
        else:
            cur = t
    if cur:
        out.append(cur)
    return out


def fit(d, text, fn, width, max_lines, smax, smin):
    for s in range(smax, smin - 1, -2):
        f = F(fn, s)
        ls = wrap(d, text, f, width)
        if len(ls) <= max_lines and all(d.textlength(l, font=f) <= width for l in ls):
            return f, ls, s
    raise SystemExit('GAGAL: teks terlalu panjang: %r' % text[:80])


def icon(name, col, size):
    sys.path.insert(0, os.path.join(ROOT, 'toolkit'))
    import lucide
    p = lucide.render(tempfile.mkdtemp(), ['%s:%s' % (name, col)], size=size, stroke=1.3)[0]
    return Image.open(p).convert('RGBA')


def fallback_bg(ikon):
    """Latar grafis maroon bila tidak ada foto: gradasi + ikon raksasa + pola garis."""
    im = Image.new('RGB', (W, H), DEEP)
    g = Image.new('L', (1, H))
    for y in range(H):
        g.putpixel((0, y), int(255 * max(0, 1 - y / (H * .9))))
    top = Image.new('RGB', (W, H), MAROON)
    im = Image.composite(top, im, g.resize((W, H)))
    d = ImageDraw.Draw(im)
    for i in range(-H, W, 46):
        d.line((i, 0, i + H, H), fill='#3A0B15', width=2)
    try:
        ic = icon(ikon or 'newspaper', CREAM, 760)
        a = ic.split()[3].point(lambda v: int(v * .16))
        ic.putalpha(a)
        im.paste(ic, ((W - 760) // 2, 60), ic)
    except Exception:
        pass
    return im


def overlay(spec):
    """Lapisan transparan: gradasi bawah, kotak judul maroon, label, tag merek."""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    grad = Image.new('L', (1, H))
    for y in range(H):
        grad.putpixel((0, y), int(215 * max(0, (y - 560) / (H - 560)) ** 1.4))
    shade = Image.new('RGBA', (W, H), (20, 4, 8, 255)); shade.putalpha(grad.resize((W, H)))
    L = Image.alpha_composite(L, shade)
    d = ImageDraw.Draw(L)
    x0, y0, x1, _ = BOX
    pad = 36
    fj, lj, sj = fit(d, (spec.get('judul') or '').upper(), HEAVY, x1 - x0 - 2 * pad, 2, 104, 58)
    fs, ls, ss = fit(d, (spec.get('sub') or '').upper(), MED, x1 - x0 - 2 * pad, 4, 44, 28)
    hj, hs = len(lj) * sj * 1.02, len(ls) * ss * 1.22
    h = pad + hj + 14 + hs + pad + 10
    y1 = min(H - 120, y0 + h)
    y0 = y1 - h
    d.rectangle((x0, y0, x1, y1), fill=MAROON)
    d.rectangle((x0, y0, x0 + 14, y1), fill=CREAM)                       # garis aksen kiri
    kat = (spec.get('kategori') or '').upper()[:16]
    if kat:
        fk = F(MONO, 26); tw = d.textlength(kat, font=fk)
        d.rectangle((x0, y0 - 52, x0 + tw + 36, y0), fill=CREAM)
        d.text((x0 + 18, y0 - 26), kat, font=fk, fill=MAROON, anchor='lm')
    if spec.get('lokasi'):
        d.text((x1, y0 - 26), spec['lokasi'], font=F(MED, 26), fill=CREAM, anchor='rm')
    y = y0 + pad - sj * .12
    for l in lj:
        d.text((x0 + pad + 8, y), l, font=fj, fill=WHITE); y += sj * 1.02
    y += 14
    for l in ls:
        d.text((x0 + pad + 8, y), l, font=fs, fill=CREAM); y += ss * 1.22
    # tag merek di sudut kanan bawah kotak
    tag = 'BUZZORA'
    ft = F(HEAVY, 34); tw = d.textlength(tag, font=ft)
    tx1, ty0 = x1 - 24, y1 - 22
    d.rectangle((tx1 - tw - 40, ty0, tx1, ty0 + 56), fill=WHITE)
    d.text((tx1 - tw / 2 - 20, ty0 + 28), tag, font=ft, fill=MAROON, anchor='mm')
    # akun di atas
    d.text((56, 60), (spec.get('akun') or '@buzzora'), font=F(MONO, 26), fill=WHITE)
    return L


def cta(spec):
    im = Image.new('RGB', (W, H), MAROON)
    d = ImageDraw.Draw(im)
    for i in range(-H, W, 46):
        d.line((i, 0, i + H, H), fill='#861527', width=2)
    d.text((W / 2, 470), 'BUZZORA', font=F(HEAVY, 170), fill=WHITE, anchor='mm')
    d.rectangle((W / 2 - 330, 575, W / 2 + 330, 582), fill=CREAM)
    d.text((W / 2, 650), 'kabar tercepat, tanpa ribet', font=F(MED, 40), fill=CREAM, anchor='mm')
    d.rounded_rectangle((W / 2 - 300, 800, W / 2 + 300, 910), 55, fill=WHITE)
    d.text((W / 2, 855), 'FOLLOW ' + (spec.get('akun') or '@buzzora').upper(), font=F(HEAVY, 44), fill=MAROON, anchor='mm')
    d.text((W / 2, 1010), 'Berita lengkap ada di caption', font=F(MED, 34), fill=WHITE, anchor='mm')
    d.text((W / 2, 1060), 'nyalakan notifikasi biar nggak ketinggalan', font=F(MED, 28), fill=CREAM, anchor='mm')
    return im


def render(spec, out, photo=None):
    os.makedirs(out, exist_ok=True)
    ov = overlay(spec)
    ov.save(os.path.join(out, 'slide_01_overlay.png'))
    bg = fallback_bg(spec.get('ikon'))
    if photo:
        ph = Image.open(photo).convert('RGB')
        s = max(W / ph.width, H / ph.height)
        ph = ph.resize((int(ph.width * s + .5), int(ph.height * s + .5)), Image.LANCZOS)
        bg = ph.crop(((ph.width - W) // 2, (ph.height - H) // 2, (ph.width - W) // 2 + W, (ph.height - H) // 2 + H))
    s1 = Image.alpha_composite(bg.convert('RGBA'), ov).convert('RGB')
    p1 = os.path.join(out, 'slide_01.jpg'); s1.save(p1, quality=90, optimize=True)
    p2 = os.path.join(out, 'slide_02.jpg'); cta(spec).save(p2, quality=90, optimize=True)
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
