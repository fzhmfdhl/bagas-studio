"""Mesin kartu Pembicaraan Dewasa v2 (rapi, terpusat, tanpa teks bertumpuk).

Prinsip:
  - Tiap kartu = daftar BLOK yang ditumpuk vertikal lalu DIPUSATKAN di zona ZT..ZB.
  - Setiap blok punya slot tetap. Tidak ada teks yang dipakai ulang di slot yang sama, tidak ada teks
    samar (hantu) di belakang teks lain, tidak ada watermark di bawah teks.
  - Pemeriksa tumpang tindih teks (cek_tumpuk) wajib lulus pada frame lengkap.
"""
import os, sys, re, math, json, subprocess, difflib
REPO = '/home/claude/bagas-studio'
sys.path.insert(0, REPO); sys.path.insert(0, os.path.join(REPO, 'examples', 'nabila_podcast'))
import gerak as G
from gerak import (Frame, rrect, krom, caption, font, tw, seg, out_cubic, out_expo, out_back, cl, lerp,
                   rgba, P, S, BOLD, MED, HEAVY, MONO, cek_gerak, ikon, X0, X1)
from PIL import Image, ImageDraw
from dewasa import LABEL

GX0, GX1 = 180, 900
ZT, ZB = 460, 1296          # zona isi (dipusatkan di sini); seluruh susunan digeser turun supaya terasa di tengah layar
CAPY = 1378                 # pusat pill caption
G.TOPY = 310; G.BARY = 1440; G.CAPY = CAPY
NBAB = 5

ABYSS, ICE, CYAN, WHITE = '#071620', '#D8EAF2', '#42C9E6', '#F4FAFC'
TH = {
    'dark': dict(bg=ABYSS, dot='#102B3A', head=ICE, hl=CYAN, mute='#7C98A7', panel='#0E2634', pfg=ICE, pmute='#8FB0C0',
                 line='#1A3C4F', acc=CYAN, ic=ICE, ic2=CYAN, chip_bg=ICE, chip_fg=ABYSS, cnt_bg=CYAN, cnt_fg=ABYSS,
                 pill_bg=ICE, pill_fg=ABYSS, pill_hl='#0C6E85'),
    'ice': dict(bg=ICE, dot='#C6DCE7', head=ABYSS, hl='#0C6E85', mute='#4F7488', panel='#F4FAFC', pfg=ABYSS, pmute='#4F7488',
                line='#BBD6E2', acc='#0C6E85', ic=ABYSS, ic2='#0C6E85', chip_bg=ABYSS, chip_fg=ICE, cnt_bg=ABYSS,
                cnt_fg=ICE, pill_bg=ABYSS, pill_fg=ICE, pill_hl=CYAN),
    'cyan': dict(bg=CYAN, dot='#39B3CF', head=ABYSS, hl=WHITE, mute='#0B3A4A', panel=ABYSS, pfg=ICE, pmute='#9FC3D2',
                 line='#123B4D', acc=ABYSS, ic=ICE, ic2=CYAN, chip_bg=ABYSS, chip_fg=ICE, cnt_bg=ABYSS, cnt_fg=CYAN,
                 pill_bg=ABYSS, pill_fg=ICE, pill_hl=CYAN),
}


def palof(th):
    return dict(ink=th['bg'], paper=th['head'], acc=th['acc'], acc2=th['hl'], mute=th['mute'], head=th['head'],
                chip_bg=th['chip_bg'], chip_fg=th['chip_fg'], cnt_bg=th['cnt_bg'], cnt_fg=th['cnt_fg'], bar=th['acc'],
                pill_bg=th['pill_bg'], pill_fg=th['pill_fg'], pill_hl=th['pill_hl'])


# ---------- ikon ----------
ICDIR = os.environ.get('DW_ICONS', '/tmp/dw_ic')
_ICN = {}


def ic(name, col):
    k = (name, col)
    if k not in _ICN:
        p = os.path.join(ICDIR, '%s_c%s.png' % (name, col.lstrip('#')))
        _ICN[k] = p
    return _ICN[k]


def make_icons(specs):
    os.makedirs(ICDIR, exist_ok=True)
    subprocess.run(['python3', os.path.join(REPO, 'toolkit', 'lucide.py'), ICDIR] + specs, check=True, stdout=subprocess.DEVNULL)


# ---------- teks tercatat (untuk cek tumpuk) ----------
def T(fr, x, y, s, f, col, a=1., anchor='la'):
    if not s or a <= 0:
        return
    bx = f.getbbox(s, anchor=anchor)
    fr.__dict__.setdefault('tb', []).append(((x * S + bx[0]) / S, (y * S + bx[1]) / S, (x * S + bx[2]) / S, (y * S + bx[3]) / S, s, a))
    G.text(fr, x, y, s, f, col, a, anchor)


def cek_tumpuk(fr, nama=''):
    tb = [b for b in fr.__dict__.get('tb', []) if b[5] >= .95]
    bad = []
    for i in range(len(tb)):
        for j in range(i + 1, len(tb)):
            a, b = tb[i], tb[j]
            ox = min(a[2], b[2]) - max(a[0], b[0]); oy = min(a[3], b[3]) - max(a[1], b[1])
            if ox > 2 and oy > 2:
                bad.append('%r menimpa %r' % (a[4][:22], b[4][:22]))
    for b in tb:
        if b[0] < GX0 - 6 or b[2] > GX1 + 6:
            bad.append('%r keluar grid (%d..%d)' % (b[4][:22], b[0], b[2]))
    if bad:
        raise ValueError('kartu %s: %s' % (nama, '; '.join(bad)))


def wrapx(s, f, mw):
    out = []; cur = ''
    for w in s.split():
        q = (cur + ' ' + w).strip()
        if tw(q, f) <= mw:
            cur = q
        else:
            if cur: out.append(cur)
            cur = w
    if cur: out.append(cur)
    return out


def pa(t, ti, d=.35):
    return out_cubic(seg(t, ti, ti + d))


# ============================== BLOK ==============================
def b_title(ctx, lines, hl=(), ti=0.0, sizes=(92, 64)):
    th = ctx['th']
    for sz in sizes:
        f = font(HEAVY, sz)
        if all(tw(l, f) <= GX1 - GX0 for l in lines): break
    lh = sz * 1.1
    h = lh * len(lines)

    def draw(fr, y, t):
        i = 0
        for bi, l in enumerate(lines):
            x = GX0
            for w in l.split(' '):
                p = out_expo(seg(t, ti + i * .09, ti + i * .09 + .4))
                c = th['hl'] if w.lower().strip('.,?!') in hl else th['head']
                T(fr, x, y + bi * lh + 22 * (1 - p), w, f, c, p)
                x += tw(w + ' ', f); i += 1
    return dict(h=h, gap=24, draw=draw, ti=ti)


def b_plat(ctx, nama, ti):
    c = LABEL[nama]; bg = '#%02X%02X%02X' % c['bg']; fg = '#%02X%02X%02X' % c['fg']
    f = font(MONO, 32); w = tw(nama, f) + 56; h = 60

    def draw(fr, y, t):
        p = out_back(seg(t, ti, ti + .3))
        if p <= 0: return
        a = cl(p * 3)
        rrect(fr, (GX0, y, GX0 + w, y + h), 6, bg, a)
        G.text(fr, GX0 + w / 2, y + h / 2, nama, f, fg, a, anchor='mm')
    return dict(h=h, gap=24, draw=draw, ti=ti, plat=(nama, ti))


def b_mono(ctx, s, ti, col=None, size=30):
    f = font(MONO, size)

    def draw(fr, y, t):
        p = pa(t, ti, .3)
        T(fr, GX0, y, s, f, col or ctx['th']['hl'], p)
    return dict(h=size * 1.25, gap=40, draw=draw, ti=ti)


def b_rows(ctx, items, tis, rowh=100, fsize=42, pad=40):
    rowh = int(rowh * 1.14)
    """Panel berisi baris ikon + teks. Garis pembagi tampak dari awal; baris muncul di waktunya."""
    th = ctx['th']
    n = len(items); H = pad * 2 + n * rowh
    tmax = GX1 - GX0 - pad * 2 - 44 - 28
    f = font(MED, fsize)
    while fsize > 36 and any(tw(s, f) > tmax for _, s in items):
        fsize -= 2; f = font(MED, fsize)
    for _, s in items:
        assert tw(s, f) <= tmax, 'baris terlalu panjang: %r (%d > %d)' % (s, tw(s, f), tmax)

    def draw(fr, y, t):
        p0 = pa(t, min(tis) - .25, .3)
        rrect(fr, (GX0, y, GX1, y + H), 12, th['panel'], p0, shadow=16 if th is TH['ice'] else 0)
        for i, (nm, s) in enumerate(items):
            ry = y + pad + i * rowh
            if i:
                fr.draw().line(P(GX0 + pad, ry, GX1 - pad, ry), fill=rgba(th['line'], p0), width=int(2 * S))
            p = pa(t, tis[i], .35)
            if p <= 0: continue
            dx = (1 - p) * -26
            ikon(fr, ic(nm, th['ic2'] if i == len(items) - 1 else th['ic']) if False else ic(nm, th['ic']),
                 GX0 + pad + 22 + dx, ry + rowh / 2, 44, p)
            T(fr, GX0 + pad + 44 + 28 + dx, ry + rowh / 2, s, f, th['pfg'], p, anchor='lm')
    return dict(h=H, gap=48, draw=draw, ti=min(tis))


def b_big(ctx, val, sub, ti, vsize=140):
    th = ctx['th']
    for sz in (vsize, 92, 64):
        f = font(HEAVY, sz)
        if tw(val, f) <= GX1 - GX0: break
    fs = font(MONO, 30); h = sz * 1.1 + 12 + 40

    def draw(fr, y, t):
        p = out_expo(seg(t, ti, ti + .5))
        if p <= 0: return
        T(fr, GX0, y + 24 * (1 - p), val, f, th['hl'], p)
        T(fr, GX0, y + sz * 1.1 + 12, sub, fs, th['mute'], p)
    return dict(h=h, gap=48, draw=draw, ti=ti)


def b_claim(ctx, line, nota, ti, strike=None, size=48):
    """Kartu klaim: aksen kiri, kalimat klaim, catatan mono. strike: waktu garis coret mulai (atau None)."""
    th = ctx['th']; f = font(MED, size); fm = font(MONO, 28)
    ls = wrapx(line, f, GX1 - GX0 - 96 - 12)
    lh = size * 1.28; H = 44 + len(ls) * lh + 20 + 34 + 44

    def draw(fr, y, t):
        p = pa(t, ti, .4)
        if p <= 0: return
        rrect(fr, (GX0, y, GX1, y + H), 12, th['panel'], p, shadow=16 if th is TH['ice'] else 0)
        rrect(fr, (GX0, y, GX0 + 8, y + H), 4, th['acc'] if th is not TH['dark'] else CYAN, p)
        for i, l in enumerate(ls):
            T(fr, GX0 + 48, y + 44 + i * lh, l, f, th['pfg'], p)
            if strike is not None:
                q = out_cubic(seg(t, strike + i * .25, strike + i * .25 + .45))
                if q > 0:
                    yy = y + 44 + i * lh + size * .56
                    fr.draw().line(P(GX0 + 48, yy, GX0 + 48 + tw(l, f) * q, yy), fill=rgba('#B5282A'), width=int(7 * S))
        T(fr, GX0 + 48, y + 44 + len(ls) * lh + 20, nota, fm, th['pmute'], p)
    return dict(h=H, gap=48, draw=draw, ti=ti)


def b_squeeze(ctx, ti, tend):
    """Dua lapisan es bergerak lurus saling mendekat, terowongan di tengah menyempit."""
    th = ctx['th']; H = 460; fm = font(MONO, 28)

    def draw(fr, y, t):
        p0 = pa(t, ti, .3)
        if p0 <= 0: return
        rrect(fr, (GX0, y, GX1, y + 380), 12, '#BBD6E2' if th is TH['ice'] else th['panel'], p0)
        q = in_out_(seg(t, ti + .2, tend))
        top_h = lerp(110, 168, q); bot_h = lerp(110, 168, q)
        gap = 380 - top_h - bot_h
        rrect(fr, (GX0 + 24, y + 24, GX1 - 24, y + 24 + top_h - 24), 8, '#8FB9CC', p0)
        rrect(fr, (GX0 + 24, y + 380 - 24 - (bot_h - 24), GX1 - 24, y + 380 - 24), 8, '#8FB9CC', p0)
        ty0 = y + top_h; ty1 = y + 380 - bot_h
        rrect(fr, (GX0 + 24, ty0, GX1 - 24, ty1), 6, ABYSS, p0)
        T(fr, GX0, y + 380 + 24, 'LAPISAN ES TERUS BERGERAK', fm, th['mute'], p0)
    return dict(h=H, gap=48, draw=draw, ti=ti)


def in_out_(x): return G.in_out(x)


def b_bar(ctx, a, b, ti, tend, tag):
    """Garis waktu horizontal a -> b dengan pengisi bergerak."""
    th = ctx['th']; fm = font(MONO, 30); fb = font(HEAVY, 64); H = 64 + 28 + 14 + 30

    def draw(fr, y, t):
        p = pa(t, ti, .3)
        if p <= 0: return
        T(fr, GX0, y, a, fb, th['head'], p)
        T(fr, GX1, y, b, fb, th['hl'], p, anchor='ra')
        by = y + 64 + 28
        rrect(fr, (GX0, by, GX1, by + 14), 7, th['line'], p)
        q = in_out_(seg(t, ti + .3, tend))
        rrect(fr, (GX0, by, GX0 + (GX1 - GX0) * q + 14, by + 14), 7, th['hl'], p)
        T(fr, GX0, by + 14 + 18, tag, fm, th['mute'], p)
    return dict(h=H, gap=48, draw=draw, ti=ti)


def b_scan(ctx, ti, tend):
    """Panel kisi; garis pindai turun lurus dan membuka blok bangunan (tegak, sejajar grid)."""
    th = ctx['th']; PH = 400; fm = font(MONO, 28)
    blocks = [(0, 1, 2, 3), (3, 0, 6, 2), (0, 4, 3, 6), (4, 3, 6, 6)]   # (kolom0,baris0,kolom1,baris1) pada kisi 6x6, tidak saling menimpa

    def draw(fr, y, t):
        p0 = pa(t, ti, .3)
        if p0 <= 0: return
        rrect(fr, (GX0, y, GX1, y + PH), 12, th['panel'], p0)
        cw = (GX1 - GX0 - 80) / 6; ch = (PH - 80) / 6
        d = fr.draw()
        for k in range(7):
            d.line(P(GX0 + 40 + k * cw, y + 40, GX0 + 40 + k * cw, y + PH - 40), fill=rgba(th['line'], p0), width=int(2 * S))
            d.line(P(GX0 + 40, y + 40 + k * ch, GX1 - 40, y + 40 + k * ch), fill=rgba(th['line'], p0), width=int(2 * S))
        q = in_out_(seg(t, ti + .2, tend)); sy = y + 40 + q * (PH - 80)
        for (c0, r0, c1, r1) in blocks:
            by0 = y + 40 + r0 * ch
            if sy >= by0:
                bb = min(sy, y + 40 + r1 * ch)
                rrect(fr, (GX0 + 40 + c0 * cw + 6, by0 + 6, GX0 + 40 + c1 * cw - 6, bb - 6 if bb - 6 > by0 + 6 else by0 + 7), 4, CYAN, p0 * .9)
        if 0 < q < 1:
            d.line(P(GX0 + 24, sy, GX1 - 24, sy), fill=rgba(WHITE), width=int(5 * S))
        T(fr, GX0, y + PH + 24, 'PESAWAT RADAR NASA · UJI ALAT', fm, th['mute'], p0)
    return dict(h=PH + 24 + 40, gap=48, draw=draw, ti=ti)


def b_strata(ctx, ti):
    """Kolom inti es: tiga lapisan, satu lapisan kosong bergaris putus (klaim tanpa sampel)."""
    th = ctx['th']; fm = font(MONO, 28); H = 3 * 48 + 2 * 12 + 24 + 30

    def draw(fr, y, t):
        p = pa(t, ti, .3)
        if p <= 0: return
        for i in range(3):
            yy = y + i * 60
            if i == 1:
                dd = fr.draw()
                for k in range(0, int(GX1 - GX0), 36):
                    dd.line(P(GX0 + k, yy, GX0 + k + 20, yy), fill=rgba(th['hl'], p), width=int(3 * S))
                    dd.line(P(GX0 + k, yy + 48, GX0 + k + 20, yy + 48), fill=rgba(th['hl'], p), width=int(3 * S))
            else:
                rrect(fr, (GX0, yy, GX1, yy + 48), 6, th['panel'], p)
        T(fr, GX0, y + 3 * 60 - 12 + 24, 'LAPISAN KE-2 · TANPA SAMPEL', fm, th['mute'], p)
    return dict(h=H, gap=48, draw=draw, ti=ti)


def b_text(ctx, s, ti, size=44, col=None, weight=MED, gap=48):
    th = ctx['th']; f = font(weight, size)
    ls = wrapx(s, f, GX1 - GX0); lh = size * 1.3

    def draw(fr, y, t):
        p = pa(t, ti, .35)
        for i, l in enumerate(ls):
            T(fr, GX0, y + i * lh + 18 * (1 - p), l, f, col or th['head'], p)
    return dict(h=lh * len(ls), gap=gap, draw=draw, ti=ti)


def b_pills(ctx, items, ti):
    th = ctx['th']; f = font(MONO, 30); H = 60

    def draw(fr, y, t):
        x = GX0
        for i, s in enumerate(items):
            p = pa(t, ti + i * .15, .3)
            w = tw(s, f) + 48
            if p > 0:
                rrect(fr, (x, y, x + w, y + H), 30, th['panel'], p)
                G.text(fr, x + w / 2, y + H / 2, s, f, th['pfg'], p, anchor='mm')
            x += w + 16
    return dict(h=H, gap=48, draw=draw, ti=ti)


def b_wordmark(ctx, ti):
    th = ctx['th']; f = font(MONO, 32)

    def draw(fr, y, t):
        p = pa(t, ti, .4); x = GX0
        for ch in 'JERSTALK':
            T(fr, x, y, ch, f, th['hl'], p); x += tw(ch, f) + 14
    return dict(h=40, gap=24, draw=draw, ti=ti)


def b_rule(ctx, ti):
    th = ctx['th']

    def draw(fr, y, t):
        p = out_cubic(seg(t, ti, ti + .5))
        if p > 0:
            rrect(fr, (GX0, y, GX0 + (GX1 - GX0) * p, y + 4), 2, th['hl'])
    return dict(h=4, gap=40, draw=draw, ti=ti)


def b_years(ctx, years, on, ti):
    """Pita tahun berpetak (tegak, sejajar), satu petak menyala."""
    th = ctx['th']; f = font(MONO, 30); H = 84; w = (GX1 - GX0) / len(years)

    def draw(fr, y, t):
        p = pa(t, ti, .4)
        if p <= 0: return
        rrect(fr, (GX0, y, GX1, y + H), 8, th['panel'], p)
        for i, yr in enumerate(years):
            x = GX0 + i * w
            if yr == on:
                rrect(fr, (x, y, x + w, y + H), 8, th['hl'], p)
            if i:
                fr.draw().line(P(x, y, x, y + H), fill=rgba(th['bg'], p), width=int(3 * S))
            G.text(fr, x + w / 2, y + H / 2, yr, f, th['bg'] if yr == on else th['pfg'], p, anchor='mm')
    return dict(h=H, gap=48, draw=draw, ti=ti)


def b_cta(ctx, ti):
    th = ctx['th']; f = font(MONO, 32)

    def draw(fr, y, t):
        for i, s in enumerate(['TULIS DI KOMENTAR', '@jerapahmerah_', '#PembicaraanDewasa']):
            p = pa(t, ti + i * .35, .35)
            w = tw(s, f) + 56
            if p > 0:
                rrect(fr, (GX0, y + i * 88, GX0 + w, y + i * 88 + 64), 32, th['hl'] if i == 0 else th['panel'], p)
                G.text(fr, GX0 + w / 2, y + i * 88 + 32, s, f, th['bg'] if i == 0 else th['pfg'], p, anchor='mm')
    return dict(h=64 + 2 * 88, gap=48, draw=draw, ti=ti)


# ============================== RENDER KARTU ==============================
def layout(blocks, shrink=True):
    tot = sum(b['h'] for b in blocks) + sum(b['gap'] for b in blocks[:-1])
    top = ZT + max(0, (ZB - ZT - tot) / 2)
    ys = []; y = top
    for b in blocks:
        ys.append(y); y += b['h'] + b['gap']
    return ys, tot


def render_card(ctx, blocks, t, bab, label, ptotal, cap=None, full=False):
    th = ctx['th']; pal = palof(th)
    fr = Frame(th['bg'], th['dot'])
    krom(fr, t, ptotal, bab, NBAB, pal, label)
    ys, tot = layout(blocks)
    for b, y in zip(blocks, ys):
        b['draw'](fr, y, t)
    if cap:
        kata, aktif, tin = cap
        caption(fr, kata, aktif, tin, t, pal, ())
    return fr
