# CONTOH episode Pembicaraan Dewasa (Camp Century, v2). Jalur kerja: n.mp3/j.mp3 + nw.json/jw.json (transkrip berwaktu) + naskah di DB.
# Path DB dan RV di bawah khusus sesi itu; ganti untuk episode lain. Mesin kartu ada di kartu_dewasa.py.
import os, sys, re, json, math, difflib, subprocess, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DW_ICONS', '/tmp/dw_ic')
import numpy as np
from kartu_dewasa import *
import kartu_dewasa as eng
import panggung as PG
from toolkit.studio import load_wav, normalize, SR, place, duck, mix, save_wav
from dewasa import musik_misteri, stinger

RV = os.path.dirname(os.path.abspath(__file__)) + '/'
FPS = 30
GAP = .22; LEAD = .40; TAIL = 1.6; HEAD = 1.1
DB = json.load(open('/tmp/claude-0/-home-claude/510ae0f9-8eb4-5185-a2cb-2ea41c94d4fe/scratchpad/db/data/users/me/st_tokmw365hb12a.json'))
DB = DB.get('data', DB)
BARIS = DB['naskah']['baris']
NW = json.load(open(RV + 'nw.json'))['words']; JW = json.load(open(RV + 'jw.json'))['words']
PS = [0.06, 8.98, 22.28, 34.54, 44.26, 53.64, 62.44, 75.26, 83.9, 90.58, 98.82, 106.64, 114.4, 123.38, 133.02, 141.46, 150.28, 155.78]
RS = [0.08, 1.86, 3.0, 5.2, 6.08, 7.78, 8.96, 10.1, 11.4, 13.02]


def nrm(s): return re.sub(r'[^a-z0-9]', '', s.lower())


def align(text, tw_):
    """Kata naskah -> waktu dari transkrip berwaktu (pencocokan urutan, sisanya diinterpolasi)."""
    sw = text.split(); a = [nrm(w) for w in sw]; b = [nrm(w['text']) for w in tw_]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    t0 = [None] * len(sw); t1 = [None] * len(sw)
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            t0[i + k] = tw_[j + k]['start']; t1[i + k] = tw_[j + k]['end']
    # interpolasi
    lo = tw_[0]['start']; hi = tw_[-1]['end']
    i = 0
    while i < len(sw):
        if t0[i] is None:
            j = i
            while j < len(sw) and t0[j] is None: j += 1
            ta = t1[i - 1] if i > 0 else lo
            tb = t0[j] if j < len(sw) else hi
            L = [max(1, len(nrm(sw[k]))) for k in range(i, j)]; tot = sum(L); c = ta
            for k, l in zip(range(i, j), L):
                d = (tb - ta) * l / tot; t0[k] = c; t1[k] = c + d; c += d
            i = j
        else:
            i += 1
    return [dict(w=sw[k], t0=t0[k], t1=min(t1[k], t0[k] + 1.2)) for k in range(len(sw))]


# ---------- suara ----------
NA = normalize(load_wav(RV + 'n.mp3'), .9); JA = normalize(load_wav(RV + 'j.mp3'), .9)
items = []; ni = ji = 0
for i, b in enumerate(BARIS):
    if b['s'] == 'N':
        a0 = PS[ni]; nxt = PS[ni + 1] if ni + 1 < len(PS) else len(NA) / SR
        tr = [w for w in NW if a0 - .02 <= w['start'] < nxt - .02]
        end = min(nxt - .05, tr[-1]['end'] + .25)
        s0 = max(0, a0 - .06); src = NA; ni += 1
    else:
        a0 = RS[ji]; nxt = RS[ji + 1] if ji + 1 < len(RS) else len(JA) / SR
        tr = [w for w in JW if a0 - .02 <= w['start'] < nxt - .02]
        end = min(nxt - .05, tr[-1]['end'] + .12)
        s0 = max(0, a0 - .05); src = JA; ji += 1
    seg_ = src[int(s0 * SR):int(end * SR)].copy()
    f = int(.008 * SR); seg_[:f] *= np.linspace(0, 1, f); seg_[-f:] *= np.linspace(1, 0, f)
    items.append(dict(i=i, kind=b['s'], peran=b['peran'], text=b['t'], aud=seg_, s0=s0, tr=tr, dur=len(seg_) / SR))
t = LEAD
for it in items:
    it['t0'] = t; t += it['dur'] + GAP
DUR = t - GAP + TAIL
for k, it in enumerate(items):
    it['ws'] = 0. if k == 0 else it['t0'] - GAP / 2
    it['we'] = DUR if k == len(items) - 1 else it['t0'] + it['dur'] + GAP / 2
    off = it['t0'] - it['ws'] - it['s0']
    al = align(it['text'], it['tr'])
    it['words'] = [dict(w=w['w'], t0=w['t0'] + off, t1=w['t1'] + off) for w in al]
    # jendela wajah Nabila (bicara), di awal baris dan satu kali di tengah baris panjang
    fc = []
    if it['kind'] == 'N' and k != 0:
        fc.append((0., HEAD))
        wd = it['words']; span = it['we'] - it['ws']
        if span > 9.5:
            best = None
            for q in range(len(wd) - 1):
                if re.search(r'[.?!]$', wd[q]['w']):
                    m = wd[q + 1]['t0'] - .1
                    if HEAD + 2.2 < m < span - 3.2:
                        sc = abs(m - span / 2)
                        if best is None or sc < best[0]: best = (sc, m)
            if best: fc.append((best[1], best[1] + 1.25))
    it['faces'] = fc


def R(it, kw, off=-.04, nth=0):
    """Waktu (relatif awal jendela baris) kata pemicu; dijaga di luar jendela wajah."""
    k = nrm(kw); c = 0
    for w in it['words']:
        if nrm(w['w']).startswith(k):
            if c == nth:
                t_ = w['t0'] + off
                for (a, b) in it['faces']:
                    if a - .15 < t_ < b: t_ = b + .05
                return max(t_, 0)
            c += 1
    raise KeyError('kata pemicu %r tidak ada di baris %d' % (kw, it['i']))


def Rend(it, kw, nth=0):
    k = nrm(kw); c = 0
    for w in it['words']:
        if nrm(w['w']).startswith(k):
            if c == nth: return w['t1']
            c += 1
    raise KeyError(kw)


# ============================== KARTU ==============================
def H0(it): return (HEAD + .12) if it['faces'] else .1


def card_spec(it):
    i = it['i']; th = dict(TH['dark']); ctx = dict(th=th, it=it); h0 = H0(it)
    nm = 'dark'
    def mk(name):
        nonlocal th, ctx
        th = TH[name]; ctx = dict(th=th, it=it)
    if i == 0:
        d = [b_wordmark(ctx, .1), b_title(ctx, ['PEMBICARAAN'], ti=.2, sizes=(64,)),
             b_title(ctx, ['DEWASA'], ti=.45, sizes=(140,)), b_rule(ctx, .8),
             b_title(ctx, ['Kota Rahasia', 'di Bawah Es'], ('rahasia',), ti=1.0, sizes=(92,)),
             b_years(ctx, ['1959', '1963', '1966', '1997', '2024'], '1997', R(it, 'rahasia'))]
        d[0]['gap'] = 24; d[1]['gap'] = 0; d[2]['gap'] = 24
        d[4]['gap'] = 48
        return 1, 'hook', d, 'dark'
    if i == 2:
        mk('ice')
        return 2, 'yang terbukti', [b_title(ctx, ['CAMP', 'CENTURY'], ('century',), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                    b_mono(ctx, '1959 · GREENLAND · ANGKATAN DARAT', h0 + .8, size=28),
                                    b_rows(ctx, [('calendar', 'Dibangun tentara AS, 1959'), ('layers', '3 km terowongan di dalam es'),
                                                 ('flask-conical', 'Disebut stasiun penelitian')],
                                           [R(it, 'dibangun'), R(it, 'kilometer'), R(it, 'disebut')])], 'ice'
    if i == 4:
        return 2, 'yang terbukti', [b_title(ctx, ['REAKTOR', 'YANG DIPINDAH'], ('dipindah',), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                    b_rows(ctx, [('atom', 'Reaktor kecil, bisa dipindah'), ('zap', 'Menyala 1960 sampai 1963'),
                                                 ('truck', 'Diangkut keluar tahun 1964')],
                                           [R(it, 'listriknya'), R(it, 'menyala'), R(it, 'diangkut')], rowh=112)], 'dark'
    if i == 6:
        return 2, 'yang terbukti', [b_title(ctx, ['YANG', 'DISEMBUNYIKAN'], ('disembunyikan',), h0), b_plat(ctx, 'TERBUKTI', R(it, 'rencana')),
                                    b_mono(ctx, 'PROJECT ICEWORM', R(it, 'iceworm')),
                                    b_big(ctx, '600', 'RUDAL NUKLIR DIRENCANAKAN', R(it, 'enam')),
                                    b_big(ctx, '4.000 KM', 'TEROWONGAN DIRENCANAKAN', R(it, 'empat'), vsize=140)], 'dark'
    if i == 8:
        return 2, 'yang terbukti', [b_title(ctx, ['MASALAHNYA'], (), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                    b_rows(ctx, [('map-pin', 'Greenland wilayah Denmark'), ('ban', 'Denmark larang senjata nuklir'),
                                                 ('eye-off', 'Tidak pernah diberitahu')],
                                           [R(it, 'greenland'), R(it, 'melarang'), R(it, 'diberitahukan')], rowh=112)], 'dark'
    if i == 10:
        mk('ice')
        return 2, 'yang terbukti', [b_title(ctx, ['ESNYA', 'HIDUP'], ('hidup',), h0), b_text(ctx, 'Rudalnya sendiri tidak pernah terpasang.', h0 + .5),
                                    b_squeeze(ctx, R(it, 'lapisannya'), Rend(it, 'rusak'))], 'ice'
    if i == 11:
        return 2, 'yang terbukti', [b_title(ctx, ['DITINGGALKAN,', 'LALU DIBUKA'], ('dibuka',), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                    b_rows(ctx, [('calendar', '1965 · kamp dikosongkan'), ('calendar', '1966 · ditinggalkan'),
                                                 ('file-text', '1997 · dokumen dibuka')],
                                           [R(it, 'dikosongkan'), R(it, 'ditinggalkan'), R(it, '1997')], rowh=112)], 'dark'
    if i == 13:
        return 3, 'teori yang beredar', [b_title(ctx, ['TEORINYA', 'JALAN'], ('jalan',), h0), b_plat(ctx, 'DIKLAIM', R(it, 'teorinya')),
                                         b_claim(ctx, 'Rudalnya sudah sempat dipasang', 'TEORI YANG BEREDAR · TANPA DOKUMEN', R(it, 'yakin')),
                                         b_strata(ctx, R(it, 'membeku'))], 'dark'
    if i == 15:
        return 3, 'teori yang beredar', [b_title(ctx, ['ADA JUGA', 'YANG PERCAYA'], ('percaya',), h0), b_plat(ctx, 'DIKLAIM', R(it, 'percaya')),
                                         b_rows(ctx, [('eye-off', 'Kamp tidak benar-benar ditutup'), ('layers', 'Instalasi lain di bawah es')],
                                                [R(it, 'kampnya'), R(it, 'instalasi')], rowh=120)], 'dark'
    if i == 16:
        mk('cyan')
        return 3, 'kenapa orang percaya', [b_title(ctx, ['DAN ALASANNYA', 'MASUK AKAL'], ('akal',), h0),
                                           b_big(ctx, '30 TAHUN', 'PROYEK NUKLIR BISA DISIMPAN', R(it, 'tiga'), vsize=140),
                                           b_text(ctx, 'Bahkan dari negara pemilik tanahnya.', R(it, 'bahkan'), col=TH['cyan']['head'], weight=BOLD)], 'cyan'
    if i == 18:
        return 4, 'fakta atau teori', [b_title(ctx, ['FAKTA ATAU TEORI'], ('teori',), h0), b_plat(ctx, 'BELUM TERBUKTI', R(it, 'belum')),
                                       b_claim(ctx, 'Rudal nuklir pernah sampai di sana', 'TIDAK ADA SATU PUN DOKUMEN', R(it, 'tidak'), strike=R(it, 'menunjukkan'))], 'dark'
    if i == 19:
        mk('ice')
        return 4, 'fakta atau teori', [b_title(ctx, ['DOKUMEN', 'YANG DIBUKA'], ('dibuka',), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                       b_rows(ctx, [('file-text', 'Proyek batal: esnya bergerak'), ('ban', 'Kamp tidak terbukti aktif')],
                                              [R(it, 'proyeknya'), R(it, 'bukti')], rowh=128)], 'ice'
    if i == 20:
        return 4, 'yang betulan tertinggal', [b_title(ctx, ['YANG BETULAN', 'TERTINGGAL'], ('tertinggal',), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                              b_rows(ctx, [('droplets', '±200.000 liter diesel'), ('flask-conical', 'Bahan kimia PCB'),
                                                           ('radiation', 'Limbah radioaktif')],
                                                     [R(it, 'sekitar'), R(it, 'bahan'), R(it, 'limbah')], rowh=112)], 'dark'
    if i == 22:
        mk('ice')
        return 4, 'perkiraan studi 2016', [b_title(ctx, ['KALAU ESNYA', 'MENCAIR'], ('mencair',), h0), b_mono(ctx, 'STUDI TAHUN 2016', R(it, '2016')),
                                           b_bar(ctx, '2016', '2100', R(it, 'memperkirakan'), Rend(it, '2100'), 'PERKIRAAN ES MULAI MENCAIR'),
                                           b_text(ctx, 'Air lelehannya membawa sampah itu keluar.', R(it, 'lelehannya'))], 'ice'
    if i == 23:
        return 4, 'uji alat, 2024', [b_title(ctx, ['RADAR NASA,', '2024'], ('2024',), h0), b_scan(ctx, R(it, 'pesawat'), Rend(it, 'terbaca')),
                                     b_text(ctx, 'Kotanya terbaca di layar.', R(it, 'tanpa'))], 'dark'
    if i == 24:
        mk('ice')
        return 5, 'yang bisa kita yakini', [b_title(ctx, ['YANG BISA', 'KITA YAKINI'], ('yakini',), h0), b_plat(ctx, 'TERBUKTI', h0 + .45),
                                            b_rows(ctx, [('check', 'Kota rahasianya nyata'), ('check', 'Satu negara tidak diberitahu'),
                                                         ('check', 'Limbahnya masih di sana')],
                                                   [R(it, 'rahasianya'), R(it, 'satu'), R(it, 'limbahnya')], rowh=112)], 'ice'
    if i == 25:
        return 5, 'batas jujur', [b_title(ctx, ['YANG TIDAK', 'BISA KITA BILANG'], ('tidak',), h0), b_plat(ctx, 'BELUM TERBUKTI', R(it, 'hulu')),
                                  b_claim(ctx, 'Ada hulu ledak nuklir di bawah es', 'BELUM ADA BUKTINYA', R(it, 'ada'), strike=R(it, 'belum'))], 'dark'
    if i == 27:
        return 5, 'penutup', [b_wordmark(ctx, h0), b_title(ctx, ['APA LAGI YANG', 'MASIH TERSIMPAN', 'DI BAWAH ES?'], ('tersimpan',), h0 + .1),
                              b_cta(ctx, R(it, 'tulis'))], 'dark'
    raise KeyError(i)


CARDS = {}
for it in items:
    if it['kind'] == 'N':
        bab, lab, blocks, thn = card_spec(it)
        CARDS[it['i']] = dict(bab=bab, label=lab, blocks=blocks, th=TH[thn])
        for b in blocks:
            b['gap'] = b['gap']


# ---------- caption ----------
def phrases(words):
    f = font(BOLD, 40); gs = []; cur = []
    for k, w in enumerate(words):
        if cur and tw(' '.join(words[j]['w'] for j in cur + [k]), f) > 540:
            gs.append(cur); cur = []
        cur.append(k)
        txt = ' '.join(words[j]['w'] for j in cur)
        if len(cur) >= 4 or re.search(r'[.?!]$', w['w']) or (re.search(r'[,;:]$', w['w']) and len(cur) >= 2) or tw(txt, f) > 560:
            gs.append(cur); cur = []
    if cur:
        if len(cur) == 1 and gs and len(gs[-1]) <= 3: gs[-1] += cur
        else: gs.append(cur)
    return gs


for it in items:
    it['groups'] = phrases(it['words'])


def cap_at(it, rel):
    g = None
    for gg in it['groups']:
        if it['words'][gg[0]]['t0'] - .03 <= rel: g = gg
    if g is None: g = it['groups'][0]
    kata = [it['words'][j]['w'] for j in g]
    aktif = 0
    for q, j in enumerate(g):
        if it['words'][j]['t0'] <= rel: aktif = q
    return kata, aktif, max(0., it['words'][g[0]]['t0'])


# ---------- frame ----------
def item_at(t):
    for it in items:
        if it['ws'] <= t < it['we']: return it
    return items[-1]


def shot_n(t, e):
    k = [0, 2][int(e / .42) % 2]
    p = min(1, e / 1.2)
    return PG.px(PG.zoomed(PG.shot_n(t, k), 1.0 + p * .03, int(p * -8)), 2)


def shot_j(t, e):
    k = [0, 1][int(e / .42) % 2]
    p = min(1, e / 2.0)
    return PG.px(PG.zoomed(PG.shot_j(t, k), 1.0 + p * .035, int(p * -12)), 2)


def card_frame(it, rel, t):
    c = CARDS[it['i']]
    cap = cap_at(it, rel)
    return render_card(dict(th=c['th']), c['blocks'], rel, c['bab'], c['label'], min(1, t / DUR), cap)


def frame(fi):
    t = fi / FPS; it = item_at(t); rel = t - it['ws']
    if it['kind'] == 'J':
        return shot_j(t, rel)
    for (a, b) in it['faces']:
        if a <= rel < b:
            return shot_n(t, rel - a)
    return card_frame(it, rel, t).out()


def render_range(args):
    a, b, outdir = args
    for fi in range(a, b):
        frame(fi).save('%s/%05d.jpg' % (outdir, fi), 'JPEG', quality=93)
    return b - a


def build_audio(path):
    n = int(DUR * SR); voice = np.zeros(n)
    for it in items: place(voice, it['aud'], it['t0'])
    music = musik_misteri(DUR, seed=365112)
    spans = [(it['t0'], it['t0'] + it['dur']) for it in items]
    music = duck(music, spans, depth=.35)
    stg = np.zeros(n)
    place(stg, stinger('buka'), .2, gain=.8)
    for it in items:
        if it['kind'] != 'N': continue
        for b in CARDS[it['i']]['blocks']:
            if b.get('plat'):
                nama, ti = b['plat']
                jenis = {'TERBUKTI': 'terbukti', 'DIKLAIM': 'diklaim', 'BELUM TERBUKTI': 'belum'}[nama]
                place(stg, stinger(jenis), it['ws'] + ti, gain=.7)
    out = mix(normalize(voice, .92), music, stg)
    save_wav(path, normalize(out, .93))
    return path


def check_cards():
    for it in items:
        if it['kind'] != 'N': continue
        c = CARDS[it['i']]
        ys, tot = layout(c['blocks'])
        fr = render_card(dict(th=c['th']), c['blocks'], 99., c['bab'], c['label'], .5, cap_at(it, it['we'] - it['ws'] - .1))
        try:
            cek_tumpuk(fr, str(it['i'])); cek_gerak(fr, str(it['i'])); st = 'ok'
        except Exception as e:
            st = 'GAGAL: ' + str(e)
        print('kartu %2d  tinggi %4d  atas %4d bawah %4d  %s' % (it['i'], tot, ys[0], ys[-1] + c['blocks'][-1]['h'], st))


if __name__ == '__main__':
    print('durasi %.2f dtk, item %d' % (DUR, len(items)))
    mode = sys.argv[1] if len(sys.argv) > 1 else 'info'
    if mode == 'info':
        for it in items:
            print(it['i'], it['kind'], '%.2f-%.2f' % (it['ws'], it['we']), it['faces'], it['text'][:50])
    elif mode == 'cek':
        make_icons_all = None
        check_cards()

    elif mode == 'tes':
        outd = RV + 'tes'; os.makedirs(outd, exist_ok=True)
        ts = [float(x) for x in sys.argv[2:]]
        paths = []
        for tt in ts:
            fi = int(tt * FPS); p_ = '%s/t_%06.2f.jpg' % (outd, tt); frame(fi).save(p_, 'JPEG', quality=90); paths.append(p_)
        from toolkit.studio import contact_sheet
        print(contact_sheet(outd + '/sheet.jpg', paths, cols=4, w=360))

    elif mode == 'penuh':
        outd = RV + 'tes'; os.makedirs(outd, exist_ok=True); paths = []
        for it in items:
            if it['kind'] == 'N':
                tt = it['we'] - .35; p_ = '%s/p_%02d.jpg' % (outd, it['i']); frame(int(tt * FPS)).save(p_, 'JPEG', quality=90); paths.append(p_)
        from toolkit.studio import contact_sheet
        print(contact_sheet(outd + '/penuh.jpg', paths, cols=6, w=300))

    elif mode == 'render':
        import multiprocessing as mp
        for im_ in PG.JC + PG.NC + [PG.WALL]: im_.load()
        outd = '/tmp/dw_frames'; os.makedirs(outd, exist_ok=True)
        N = int(DUR * FPS); step = 150
        jobs = [(a, min(N, a + step), outd) for a in range(0, N, step)]
        t0 = time.time(); done = 0
        with mp.Pool(2) as pool:
            for n in pool.imap_unordered(render_range, jobs):
                done += n
                print('frame %d/%d  %.0f dtk' % (done, N, time.time() - t0), flush=True)
        build_audio(RV + 'mix.wav')
        print('audio ok')
