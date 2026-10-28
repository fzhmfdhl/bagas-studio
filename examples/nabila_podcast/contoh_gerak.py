"""CONTOH (bukan template): 9 detik bagian motion dengan bahasa editing acuan Jers.

Menunjukkan cara memakai gerak.py: latar grid + lingkaran, krom bab, judul tersusun kata per kata,
kartu UI tiruan yang "dikerjakan" (baris muncul, dicoret, kursor memilih), stiker, sapuan pecahan,
adegan gelap dengan mesin tik, dan adegan warna penuh dengan ikon watermark berputar.
Episode sungguhan memakai palet, metafora, dan isi sendiri.

    python3 examples/nabila_podcast/contoh_gerak.py /tmp/out.mp4
"""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gerak import *

ROOT_ = ROOT
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/contoh_gerak.mp4'
IC = '/tmp/ic_gerak'
INK, PAPER, ACC, ACC2, MUTE = '#1D2A5A', '#EEF1F6', '#F2C230', '#4F86D6', '#8A94B3'
subprocess.run(['python3', os.path.join(ROOT, 'toolkit', 'lucide.py'), IC] +
               ['%s:%s' % (n, INK) for n in ('bot', 'pen-tool', 'image', 'mic', 'calendar-days', 'mouse-pointer-2', 'target')] +
               ['check:%s' % ACC2], check=True, stdout=subprocess.DEVNULL)
def ic(n, c=INK): return os.path.join(IC, '%s_c%s.png' % (n, c[1:]))

TERANG = dict(ink=INK, paper=PAPER, acc=ACC, acc2=ACC2, mute=MUTE, head=INK)
GELAP = dict(TERANG, head=PAPER, mute='#9AA6CC', chip_bg=PAPER, chip_fg=INK, pill_bg=PAPER, pill_fg=INK, pill_hl=ACC2)
KUNING = dict(TERANG, head=INK, acc2=PAPER, mute=INK, cnt_bg=INK, cnt_fg=ACC, bar=INK, pill_hl=ACC)
T_ALL = 9.0
CAP = [  # (mulai, kata-kata, kata kunci)
    (0.15, ['Lima', 'alat', 'AI'], ()), (1.15, ['satu', 'yang', 'kepakai'], ('kepakai',)),
    (2.55, ['bayar', 'lima'], ()), (3.35, ['pakai', 'satu'], ('satu',)),
    (5.15, ['bukan', 'soal', 'alatnya'], ('bukan',)), (6.25, ['tapi', 'kebiasaan'], ('kebiasaan',)),
    (7.55, ['satu', 'alat'], ('satu',)), (8.2, ['sampai', 'jago'], ('jago',))]

def cap(fr, t, pal):
    cur = [c for c in CAP if c[0] <= t]
    if not cur: return
    t0, ws, hl = cur[-1]
    act = min(len(ws) - 1, int((t - t0) / .22))
    caption(fr, ws, act, t0, t, pal, hl)

ROWS = [('bot', 'Asisten AI'), ('pen-tool', 'Penulis AI'), ('image', 'Gambar AI'), ('mic', 'Suara AI'), ('calendar-days', 'Jadwal AI')]

def adegan_a(t):
    fr = Frame(PAPER, '#C9D1E3'); latar(fr, t, ring='#E1E6F0'); krom(fr, t, t / T_ALL, 1, 4, TERANG, '// 01 · masalahnya')
    judul(fr, X0, 430, ['Lima alat AI.', 'Satu yang', 'kepakai.'], t, .15, font(BOLD, 104), TERANG, hl=('kepakai',), step=.13)
    if t > 1.4: rrect(fr, (X0 + 8, 950, X0 + 148, 1090), 30, ACC2, out_cubic(seg(t, 1.4, 1.6)))
    for i, (n, nm) in enumerate(ROWS):
        p = out_back(seg(t, .55 + i * .1, .9 + i * .1)); x = X0 + 18 + i * 140; y = 960
        mati = i > 0 and t > 1.4
        rrect(fr, (x, y + 20 * (1 - p), x + 120, y + 120 + 20 * (1 - p)), 24, '#FFFFFF', cl(p) * (.45 if mati else 1), shadow=14)
        ikon(fr, ic(n), x + 60, y + 60 + 20 * (1 - p), 54, cl(p) * (.35 if mati else 1))
    stiker(fr, 760, 905, t, 1.45, '× boros', TERANG, rot=-7)
    cap(fr, t, TERANG); return fr

def adegan_b(t):
    fr = Frame(PAPER, '#C9D1E3'); latar(fr, t, ring='#E1E6F0'); krom(fr, t, t / T_ALL, 2, 4, TERANG, '// 02 · langganan bulanan')
    judul(fr, X0, 350, ['Bayar lima,', 'pakai satu.'], t, 2.45, font(BOLD, 76), TERANG, hl=('satu.',))
    a = out_cubic(seg(t, 2.6, 2.9)); y0 = 600 + 30 * (1 - a)
    rrect(fr, (X0, y0, X1, y0 + 560), 22, '#FFFFFF', a, shadow=26)
    rrect(fr, (X0, y0, X1, y0 + 64), 22, INK, a); rrect(fr, (X0, y0 + 40, X1, y0 + 64), 0, INK, a)
    text(fr, X0 + 28, y0 + 32, 'langganan · bulan ini', font(MONO, 20), PAPER, a, anchor='lm')
    for i, (n, nm) in enumerate(ROWS):
        p = out_expo(seg(t, 2.8 + i * .12, 3.2 + i * .12)); y = y0 + 100 + i * 92
        if p <= 0: continue
        dead = i > 0 and t > 3.55 + i * .1
        al = p * (.38 if dead else 1)
        ikon(fr, ic(n), X0 + 62, y + 30 - 14 * (1 - p), 44, al)
        text(fr, X0 + 110, y + 30 - 14 * (1 - p), nm, font(MED, 34), INK, al, anchor='lm')
        rrect(fr, (X1 - 110, y + 12, X1 - 40, y + 48), 18, ACC2 if not dead else '#C9D1E3', al)
        if i > 0: coret(fr, X0 + 100, y + 31, X0 + 110 + tw(nm, font(MED, 34)) + 10, seg(t, 3.55 + i * .1, 3.8 + i * .1), INK, 6)
    k = out_cubic(seg(t, 3.9, 4.5)); kursor(fr, ic('mouse-pointer-2'), lerp(820, X0 + 260, k), lerp(1150, y0 + 118, k), cl((t - 3.85) * 5))
    if t > 4.5: ikon(fr, ic('check', ACC2), X1 - 160, y0 + 130, 46, out_back(seg(t, 4.5, 4.75)))
    stiker(fr, 760, y0 + 600, t, 4.55, 'cukup ini', TERANG, rot=5)
    cap(fr, t, TERANG); return fr

def adegan_c(t):
    fr = Frame(INK, '#2A3870'); krom(fr, t, t / T_ALL, 3, 4, GELAP, '// 03 · kuncinya')
    p = out_back(seg(t, 5.1, 5.45), 1.4); f = font(HEAVY, 168)
    text(fr, X0, 400 + 40 * (1 - p), 'BUKAN', f, ACC, cl(p))
    judul(fr, X0, 610, ['soal alatnya.'], t, 5.5, font(BOLD, 66), GELAP)
    a = out_cubic(seg(t, 5.9, 6.2)); y0 = 790 + 24 * (1 - a)
    rrect(fr, (X0, y0, X1, y0 + 270), 20, PAPER, a, shadow=20)
    text(fr, X0 + 30, y0 + 34, 'LATIHAN · 7 HARI', font(MONO, 19), ACC2, a)
    s, on = ketik('Pakai satu alat sampai|benar-benar jago.', t, 6.2, 30)
    rows = s.split('|')
    for k, ln in enumerate(rows):
        text(fr, X0 + 30, y0 + 80 + k * 52, ln, font(MED, 38), INK, a)
    if a > 0 and on and int(t * 4) % 2 == 0:
        cx = X0 + 34 + tw(rows[-1], font(MED, 38)); cy = y0 + 84 + (len(rows) - 1) * 52
        rrect(fr, (cx, cy, cx + 4, cy + 40), 1, INK, a)
    b = out_back(seg(t, 7.0, 7.25)); rrect(fr, (X1 - 210, y0 + 196, X1 - 30, y0 + 250), 27, ACC, cl(b))
    if b > 0: text(fr, X1 - 120, y0 + 223, 'Mulai →', font(BOLD, 28), INK, cl(b), anchor='mm')
    stiker(fr, 790, y0 - 18, t, 6.75, 'cuma itu?', GELAP, rot=-8, bg=PAPER, fg=INK, size=30)
    cap(fr, t, GELAP); return fr

def adegan_d(t):
    fr = Frame(ACC); ikon(fr, ic('target'), 540, 800, 980, .12, rot=(t - 7.4) * 18, bebas=True)
    krom(fr, t, t / T_ALL, 4, 4, KUNING)
    judul(fr, CX, 560, ['SATU ALAT.', 'SAMPAI JAGO.'], t, 7.5, font(HEAVY, 92), KUNING, hl=('jago',), step=.14, anchor='ma')
    b = out_back(seg(t, 8.25, 8.55)); w = 330
    rrect(fr, (CX - w / 2, 900, CX + w / 2, 980), 40, INK, cl(b))
    if b > 0: text(fr, CX, 940, 'coba seminggu.', font(BOLD, 36), ACC, cl(b), anchor='mm')
    cap(fr, t, KUNING); return fr

def frame(t):
    if t < 2.4: fr = adegan_a(t)
    elif t < 5.0: fr = adegan_b(t)
    elif t < 7.4: fr = adegan_c(t)
    else: fr = adegan_d(t)
    sapuan(fr, seg(t, 4.7, 5.3), [ACC, ACC2, INK])
    sapuan(fr, seg(t, 7.1, 7.7), [INK, ACC2, ACC])
    return fr.out()

if __name__ == '__main__':
    n = int(T_ALL * FPS)
    ff = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H), '-r', str(FPS), '-i', '-',
                           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', OUT], stdin=subprocess.PIPE)
    for i in range(n):
        ff.stdin.write(frame(i / FPS).tobytes())
    for nm, t in (('A', 2.0), ('B', 4.7), ('C', 7.2), ('D', 8.9)):   # cek kerapian di frame tengah tiap adegan
        cek_gerak({'A': adegan_a, 'B': adegan_b, 'C': adegan_c, 'D': adegan_d}[nm](t), nm)
    ff.stdin.close(); ff.wait(); print(OUT)
