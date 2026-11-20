"""Mesin episode podcast pixel Studio Nabila (landscape 1920x1080).

Satu perintah dari naskah + rekaman suara sampai mp4 jadi:

    python3 toolkit/podcast/episode.py spek.json            # render penuh
    python3 toolkit/podcast/episode.py spek.json --still 3 12 20   # cek frame (still.jpg)
    python3 toolkit/podcast/episode.py --kontak Rusdi        # lembar kontak semua pose (kontak_Rusdi.jpg)

Bentuk spek.json (jalur relatif terhadap folder spek):
{
  "latar": "olive" | "navy",
  "kiri": "Sonya",                 # tokoh kursi kiri (narasumber)
  "kanan": "Nabila",               # kursi kanan: "Nabila" (pilar 1 & 3) atau narasumber kedua (pilar 2)
  "suara": {"Sonya": "sonya.mp3", "Nabila": "nabila.mp3"},   # satu file per penutur, semua barisnya berurutan
  "baris": [
    {"s": "Nabila", "t": "Kalau hidup terasa berat, kamu pegang apa?"},
    {"s": "Sonya",  "t": "...", "jeda": -0.1, "pose": "20", "tahan": 1.2},
    {"s": "Sonya",  "t": "[tertawa]", "jenis": "tawa", "bareng": true}
  ],
  "keluar": "episode.mp4"
}
- "jeda": detik antara akhir baris sebelumnya dan awal baris ini (negatif = menyela). Bawaan 0.12.
- "bareng": true -> baris ini mulai bersamaan (setelah jeda) tetapi tidak menggeser baris berikutnya (untuk tawa/latar).
- "jenis": "tawa" -> volume 0.55 dan fade.
- "pose"/"tahan": sel pose saat mulai bicara (lihat lembar kontak). Tanpa itu dipilih otomatis dari pose_aman.json.
- "bidik": "W" (lebar) / "H" (kiri) / "N" (kanan) memaksa bidikan; bawaan otomatis.
Nabila yang tidak ada di kursi otomatis jadi suara belakang layar (low-pass 3800 Hz, x0.42).
"""
import sys, os, json, subprocess, tempfile, hashlib
import numpy as np, scipy.io.wavfile as wf
from scipy.signal import butter, lfilter
from PIL import Image, ImageFilter, ImageDraw
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
ASSET = os.path.join(REPO, 'assets', 'podcast')
SR = 44100; FPS = 24
CW, CH = 3840, 2160; OW, OH = 1920, 1080
LATAR = {'olive': 'bg_olive.jpg', 'navy': 'bg_navy_rusdi.jpg'}
NORM = json.load(open(os.path.join(HERE, 'norm.json')))
TOKOH = json.load(open(os.path.join(HERE, 'tokoh.json')))
POSE_AMAN = json.load(open(os.path.join(HERE, 'pose_aman.json')))

# ------------------------------------------------------------------ sel (potongan sheet)
CELLS = os.environ.get('PODCAST_CELLS', os.path.join(tempfile.gettempdir(), 'podcast_cells'))
def siapkan_sel():
    if os.path.exists(os.path.join(CELLS, 'cells.json')):
        return
    os.makedirs(CELLS, exist_ok=True)
    sh = os.path.join(CELLS, 'sh')
    if not os.path.exists(sh):
        os.symlink(os.path.join(ASSET, 'sheets'), sh)
    subprocess.run([sys.executable, os.path.join(HERE, 'cut.py')], cwd=CELLS, check=True, stdout=subprocess.DEVNULL)

def kontak(nama):
    siapkan_sel(); info = json.load(open(os.path.join(CELLS, 'cells.json')))
    ks = sorted(k for k in info if k.rsplit('_', 1)[0] == nama)
    ims = []
    for k in ks:
        im = Image.open(os.path.join(CELLS, 'cells', k + '.png')).convert('RGBA')
        bg = Image.new('RGBA', im.size, (205, 205, 205, 255)); bg.alpha_composite(im)
        d = ImageDraw.Draw(bg); d.rectangle((0, 0, 90, 44), fill=(0, 0, 0)); d.text((8, 6), k.rsplit('_', 1)[1], fill=(255, 255, 0), font_size=34)
        ims.append(bg.convert('RGB').resize((im.width // 2, im.height // 2)))
    cols = 6; w, h = ims[0].size; rows = (len(ims) + cols - 1) // cols
    S = Image.new('RGB', (w * cols, h * rows), (255, 255, 255))
    for i, m in enumerate(ims): S.paste(m, ((i % cols) * w, (i // cols) * h))
    S.save(f'kontak_{nama}.jpg', quality=85); print(f'kontak_{nama}.jpg', len(ims), 'sel')

# ------------------------------------------------------------------ audio
def muat(p):
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 's16le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(out, np.int16).astype(np.float32) / 32768

def db_frames(x, hop=0.01):
    h = int(SR * hop); n = len(x) // h
    return 20 * np.log10(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-9)

def rapikan(x, th=-60, pad=0.03):
    """Buang hening di kepala dan ekor (ambang -60 dB, pad 30 ms) - jangan memotong awal kata."""
    db = db_frames(x); h = int(SR * 0.01); idx = np.where(db > th)[0]
    if not len(idx): return x
    i0 = max(0, idx[0] * h - int(pad * SR)); i1 = min(len(x), (idx[-1] + 1) * h + int(pad * SR))
    return x[i0:i1].copy()

def kata(t):
    import re
    t = re.sub(r'\[[^\]]*\]', ' ', t)          # audio tag tidak diucapkan
    return max(1, len(t.split()))

def pecah(x, teks, nama, manual=None):
    """Pecah rekaman satu penutur jadi satu potongan per baris.
    Titik potong dipilih di jeda hening, dengan dua pertimbangan: jeda yang panjang, dan
    panjang tiap potongan yang sebanding dengan jumlah kata barisnya (jeda di tengah kalimat
    sering lebih panjang dari jeda antarbaris). Bisa ditimpa manual lewat spek "potong"."""
    n = len(teks); h = int(SR * 0.01)
    if manual:
        if len(manual) != n - 1: raise SystemExit(f'GAGAL: potong {nama} butuh {n-1} titik, ada {len(manual)}')
        cuts = [0] + [int(c * SR) for c in manual] + [len(x)]
        return [rapikan(x[cuts[k]:cuts[k + 1]]) for k in range(n)], manual
    if n == 1: return [rapikan(x)], []
    db = db_frames(x); ref = np.percentile(db[db > -90], 95) if (db > -90).any() else -20
    diam = db < max(ref - 38, -55)
    runs = []; i = 0
    while i < len(diam):
        if diam[i]:
            j = i
            while j < len(diam) and diam[j]: j += 1
            if i > 0 and j < len(diam) and j - i >= 4: runs.append((i, j))
            i = j
        else: i += 1
    if len(runs) < n - 1:
        raise SystemExit(f'GAGAL: rekaman {nama} hanya punya {len(runs)+1} bagian, naskah butuh {n}. Periksa jeda antarbaris atau isi "potong".')
    pos = [0] + [(a + b) / 2 for a, b in runs] + [len(diam)]          # kandidat titik (frame)
    glen = [0] + [(b - a) / 100 for a, b in runs] + [0]
    w = np.array([kata(t) for t in teks], float)
    bicara = (~diam).sum() / 100; k = bicara / w.sum()
    M = len(pos); INF = 1e18
    # dp[j][m]: biaya terbaik bila potongan ke-j berakhir di kandidat m
    dp = np.full((n + 1, M), INF); bk = np.zeros((n + 1, M), int); dp[0][0] = 0
    for j in range(1, n + 1):
        for m in range(1, M):
            if (j == n) != (m == M - 1): continue
            best = INF; arg = 0
            for p in range(0, m):
                if dp[j - 1][p] >= INF: continue
                dur = (~diam[int(pos[p]):int(pos[m])]).sum() / 100 + 0.05
                c = dp[j - 1][p] + 2.0 * np.log(dur / (w[j - 1] * k + 0.3)) ** 2 - (glen[m] if m < M - 1 else 0) * 1.5
                if c < best: best, arg = c, p
            dp[j][m] = best; bk[j][m] = arg
    path = [M - 1]
    for j in range(n, 0, -1): path.append(bk[j][path[-1]])
    path = path[::-1]
    cuts = [int(pos[m]) * h for m in path]
    return [rapikan(x[cuts[q]:cuts[q + 1]]) for q in range(n)], [round(c / SR, 2) for c in cuts[1:-1]]

def norm(a, t=-20):
    a = a * (10 ** (t / 20) / (np.sqrt((a ** 2).mean()) + 1e-9)); pk = np.abs(a).max()
    return a * (0.89 / pk) if pk > 0.89 else a

def fade(a, d=0.25):
    a = a.copy(); n = min(len(a), int(d * SR)); a[-n:] *= np.linspace(1, 0, n); return a

def susun_audio(spek, base, nabila_layar):
    baris = spek['baris']; segs = {}
    for nama, f in spek['suara'].items():
        idx = [i for i, b in enumerate(baris) if b['s'] == nama]
        if not idx: continue
        parts, titik = pecah(muat(os.path.join(base, f)), [baris[i]['t'] for i in idx], nama, spek.get('potong', {}).get(nama))
        print(f'  potong {nama}: {titik}  (salin ke "potong" untuk mengunci/membetulkan)')
        for i, p in zip(idx, parts): segs[i] = p
    hilang = [i for i in range(len(baris)) if i not in segs]
    if hilang: raise SystemExit(f'GAGAL: baris {hilang} tidak punya rekaman (cek field "suara").')
    ev = []; tracks = {}; t = 0.4
    for i, b in enumerate(baris):
        a = norm(segs[i])
        tawa = b.get('jenis') == 'tawa'
        if tawa: a = fade(a, 0.3) * b.get('gain', 0.55)
        else: a = a * b.get('gain', 1.0)
        if b['s'] == 'Nabila' and not nabila_layar:
            bb, aa = butter(2, 3800 / (SR / 2)); a = lfilter(bb, aa, a).astype(np.float32) * 0.42
        t0 = max(0.0, t + b.get('jeda', 0.12 if i else 0.0))
        tracks.setdefault(b['s'], []).append((int(t0 * SR), a))
        t1 = t0 + len(a) / SR
        ev.append(dict(i=i, spk=b['s'], t0=t0, t1=t1, tawa=tawa))
        if not b.get('bareng'): t = t1
        print(f"  {i:2d} {b['s']:7s} {t0:6.2f}-{t1:6.2f}  {len(a)/SR:4.1f}s  {len(b['t'].split()):2d} kata  {b['t'][:50]}")
    total = max(e['t1'] for e in ev) + 0.5
    n = int(total * SR); mix = np.zeros(n, np.float32); envs = {}
    h = SR // FPS; nf = int(total * FPS)
    for k, parts in tracks.items():
        tr = np.zeros(n + SR * 8, np.float32)
        for i0, a in parts: tr[i0:i0 + len(a)] += a
        tr = tr[:n]; mix += tr
        envs[k] = np.clip(np.array([np.sqrt((tr[f * h:(f + 1) * h] ** 2).mean()) for f in range(nf)]) / 0.09, 0, 1.5)
    fo = int(0.9 * SR); mix[-fo:] *= np.linspace(1, 0, fo)
    mix *= 0.9 / (np.abs(mix).max() + 1e-9)
    return mix, ev, envs, total

def musik(vo, seed=7):
    """Lo-fi 92 BPM buatan sendiri, ducking saat ada suara."""
    N = len(vo); T = N / SR; rng = np.random.default_rng(seed)
    beat = 60 / 92; bar = beat * 4
    midi = lambda m: 440 * 2 ** ((m - 69) / 12)
    def ep(f, d, vel=1.0):
        n = int(d * SR); t = np.arange(n) / SR
        env = np.exp(-t * 2.2) * (1 - np.exp(-t * 80))
        x = np.sin(2*np.pi*f*t) + 0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t*4) + 0.12*np.sin(2*np.pi*3*f*t)*np.exp(-t*6)
        return x * env * (1 + 0.06 * np.sin(2 * np.pi * 4.5 * t)) * vel
    lp = lambda x, fc: lfilter(*butter(2, fc / (SR / 2)), x)
    out = np.zeros(N + SR * 4, np.float32)
    def put(x, t0):
        i = int(t0 * SR)
        if i >= len(out): return
        j = min(len(out), i + len(x)); out[i:j] += x[:j - i]
    progs = [[[53,57,60,64],[52,55,59,62],[50,53,57,60],[48,52,55,59]], [[50,53,57,60],[55,59,62,65],[48,52,55,59],[57,60,64,67]]]
    CHs = progs[seed % 2]; BASS = [c[0] - 12 for c in CHs]
    t = 0.0; k = 0
    while t < T + bar:
        ch = CHs[k % 4]
        for j, m in enumerate(ch): put(ep(midi(m), bar * 1.1, 0.16), t + j * 0.025)
        put(ep(midi(ch[-1] + 12), beat * 1.5, 0.07), t + beat * 2.5)
        tb = np.arange(int(bar * SR)) / SR
        put(0.22 * np.sin(2 * np.pi * midi(BASS[k % 4]) * tb) * np.exp(-tb * 0.9) * (1 - np.exp(-tb * 40)), t)
        for b in range(4):
            if b in (0, 2):
                tt = np.arange(int(0.25 * SR)) / SR; f = 55 + 70 * np.exp(-tt * 30)
                put(0.28 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 14), t + b * beat)
            if b in (1, 3):
                n = int(0.12 * SR); put(lp(rng.standard_normal(n), 3500) * 0.05 * np.exp(-np.arange(n) / SR * 25), t + b * beat)
            n = int(0.05 * SR); x = rng.standard_normal(n); x = x - lp(x, 6000)
            put(x * 0.025 * np.exp(-np.arange(n) / SR * 60), t + b * beat + 0.5 * beat)
        t += bar; k += 1
    m = lp(out[:N], 5200)
    cr = np.zeros(N, np.float32); idx = rng.integers(0, N, int(T * 9)); cr[idx] = rng.uniform(-0.3, 0.3, len(idx))
    m += lp(cr, 4000) * 0.15 + lp(rng.standard_normal(N), 900) * 0.004
    fi = int(1.5 * SR); fo = int(3.0 * SR); m[:fi] *= np.linspace(0, 1, fi); m[-fo:] *= np.linspace(1, 0, fo)
    m /= np.abs(m).max() + 1e-9
    h = int(0.02 * SR); e = np.array([np.sqrt((vo[i:i + h] ** 2).mean()) for i in range(0, N, h)])
    g = np.repeat(np.where(e > 0.02, 0.35, 1.0), h)[:N]
    g = lfilter([1 - 0.9995], [1, -0.9995], g)
    mix = vo + m * g * 0.13
    return mix / max(1, np.abs(mix).max() / 0.95)

# ------------------------------------------------------------------ gambar
G = {}   # status global untuk proses render
def keyg(a):
    a = a.astype(np.float32); r, g, b = a[..., 0], a[..., 1], a[..., 2]; d = g - np.maximum(r, b)
    al = np.clip((70 - d) / 40, 0, 1); m = np.maximum(r, b); g = np.where(g > m, m + (g - m) * .15, g)
    return Image.fromarray(np.dstack([r, g, b, al * 255]).clip(0, 255).astype(np.uint8))

WARNA = np.array([0.90, 0.86, 0.76])
def siapkan_panggung(spek):
    siapkan_sel(); INFO = json.load(open(os.path.join(CELLS, 'cells.json')))
    e = Image.open(os.path.join(ASSET, LATAR[spek.get('latar', 'olive')])).convert('RGB'); s = CH / e.height
    e = e.resize((round(e.width * s), CH), Image.LANCZOS); ox = (e.width - CW) // 2
    BG = e.crop((ox, 0, ox + CW, CH)).convert('RGBA')
    BASE_S = 936 / 652 * 393
    SEAT = {}
    for k, nama, x in (('H', spek['kiri'], 1300), ('N', spek['kanan'], 2560)):
        tk = TOKOH[nama]
        flip = (k == 'N') == (tk['hadap'] == 'kanan')     # semua tokoh menghadap ke tengah
        SEAT[k] = dict(n=nama, x=x, y=1740, idle=tuple(tk['idle']), mouth=tuple(tk['mulut']), flip=flip,
                       sg=-1 if flip else 1, s=BASE_S / NORM[nama]['chairw'] * tk.get('koreksi', 1.0))
    G.update(INFO=INFO, SEAT=SEAT, cache={})
    M0 = keyg(np.asarray(Image.open(os.path.join(ASSET, 'mic_sheet.jpg')).convert('RGB').crop((0, 0, 500, 768))))
    a = np.asarray(M0).astype(np.float32); a[..., :3] *= WARNA; M0 = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    MICS = {k: mic_for(k, M0) for k in SEAT}
    G['MICS'] = MICS
    base = BG.copy(); base.alpha_composite(bayangan(SEAT, MICS)); G['BASE'] = base

def sprite(k, cell):
    key = (k, cell); cache = G['cache']
    if key not in cache:
        c = G['SEAT'][k]; i = G['INFO'][f"{c['n']}_{cell}"]
        im = Image.open(os.path.join(CELLS, 'cells', f"{c['n']}_{cell}.png")); s = c['s']
        im = im.resize((round(im.width * s), round(im.height * s)), Image.NEAREST)
        a = np.asarray(im).astype(np.float32); a[..., :3] *= WARNA; im = Image.fromarray(a.clip(0, 255).astype(np.uint8))
        ax = i['ax']
        if c['flip']: im = im.transpose(Image.FLIP_LEFT_RIGHT); ax = i['w'] - ax
        cache[key] = (im, round(c['x'] - ax * s), round(c['y'] - i['bot'] * s))
    return cache[key]

def mulut_xy(k):
    c = G['SEAT'][k]; i = G['INFO'][f"{c['n']}_{c['idle'][0]}"]; s = c['s']
    return c['x'] + c['sg'] * (c['mouth'][0] - i['ax']) * s, c['y'] + (c['mouth'][1] - i['bot']) * s

def mic_for(k, M0):
    c = G['SEAT'][k]; mx, my = mulut_xy(k); ms = 0.83; CAP = (40, 293); SPLIT = 480
    up = M0.crop((0, 0, M0.width, SPLIT)); lo = M0.crop((0, SPLIT, M0.width, M0.height))
    up = up.resize((round(up.width * ms), round(up.height * ms)), Image.NEAREST)
    top = my + 41 - CAP[1] * ms; floor = c['y'] + 20
    loh = max(40, int(floor - (top + up.height))); lo = lo.resize((up.width, loh), Image.NEAREST)
    m = Image.new('RGBA', (up.width, up.height + loh), (0, 0, 0, 0)); m.alpha_composite(up, (0, 0)); m.alpha_composite(lo, (0, up.height))
    if k == 'H': px = mx + 43 - CAP[0] * ms
    else: m = m.transpose(Image.FLIP_LEFT_RIGHT); px = mx - 43 - (m.width - CAP[0] * ms)
    return m, (round(px), round(top))

def bayangan(SEAT, MICS):
    amb = Image.new('L', (CW, CH), 0); con = Image.new('L', (CW, CH), 0); da = ImageDraw.Draw(amb)
    for k, c in SEAT.items():
        sp, px, py = sprite(k, c['idle'][0]); al = np.asarray(sp)[..., 3] > 100
        ys, xs = np.where(al); bot = ys.max(); h = bot - ys.min()
        lx = np.where(al[int(bot - h * 0.30):bot + 1].any(0))[0]; x0, x1 = px + lx.min(), px + lx.max(); fy = py + bot
        da.ellipse((x0 - 30, fy - (x1 - x0) * 0.20, x1 + 30, fy + (x1 - x0) * 0.06), fill=150)
        strip = al[int(bot - h * 0.06):bot + 1].astype(np.uint8) * 255
        st = Image.fromarray(strip).resize((strip.shape[1], max(4, strip.shape[0] // 2)))
        con.paste(Image.new('L', st.size, 235), (px, fy - st.height + 6), st)
    for k, (m, (px, py)) in MICS.items():
        al = np.asarray(m)[..., 3] > 100; ys, xs = np.where(al); bot = ys.max()
        row = np.where(al[bot - 25:bot + 1].any(0))[0]; x0, x1 = px + row.min(), px + row.max(); fy = py + bot
        da.ellipse((x0 - 18, fy - 30, x1 + 18, fy + 14), fill=170)
    amb = amb.filter(ImageFilter.GaussianBlur(20)); con = con.filter(ImageFilter.GaussianBlur(6))
    a = np.maximum(np.asarray(amb, np.float32) * 0.95, np.asarray(con, np.float32))
    sh = np.zeros((CH, CW, 4), np.uint8); sh[..., 0] = 18; sh[..., 1] = 14; sh[..., 2] = 8; sh[..., 3] = a.clip(0, 255).astype(np.uint8)
    return Image.fromarray(sh, 'RGBA')

def rencana(spek, ev, total):
    """Bidikan dan pose otomatis dari garis waktu."""
    SEAT = G['SEAT']; kursi = {c['n']: k for k, c in SEAT.items()}
    baris = spek['baris']; shots = [(0.0, 'W')]; pose = []
    rng = np.random.default_rng(int(hashlib.md5(json.dumps(spek['baris']).encode()).hexdigest()[:8], 16))
    terakhir = {}
    for e in ev:
        b = baris[e['i']]; k = kursi.get(e['spk'])
        if b.get('bareng') and not b.get('bidik'): continue
        if b.get('bidik'): sh = b['bidik']
        elif e['tawa'] or k is None: sh = 'W'
        else: sh = k
        if e['i'] == 0 and sh != 'W': shots.append((max(0, e['t0'] + 1.6), sh))
        else: shots.append((max(0.0, e['t0'] - 0.05), sh))
        if k is None: continue
        dur = e['t1'] - e['t0']
        cell = b.get('pose'); tahan = b.get('tahan', 1.1)
        if not cell and not e['tawa'] and dur > 2.2:
            aman = [p for p in POSE_AMAN.get(e['spk'], []) if p != terakhir.get(k)]
            if aman and rng.random() < 0.75: cell = str(rng.choice(aman))
        if e['tawa']:
            tawa = TOKOH[e['spk']].get('tawa')
            if tawa: cell = tawa; tahan = dur + 0.3
        if cell:
            pose.append((k, e['t0'], min(e['t1'], e['t0'] + tahan), cell)); terakhir[k] = cell
    shots.append((ev[-1]['t1'] + 0.15, 'W'))
    # gabungkan bidikan beruntun yang sama, buang bidikan < 0.7 dtk
    rapi = []
    for a, s in sorted(shots):
        if rapi and s == rapi[-1][1]: continue
        if rapi and a - rapi[-1][0] < 0.7 and len(rapi) > 1: rapi[-1] = (rapi[-1][0], s); continue
        rapi.append((a, s))
    G.update(SHOTS=rapi, POSE=pose)

def cell_for(k, t):
    c = G['SEAT'][k]; tq = int(t * 10) / 10.0          # tokoh bergerak 10 fps
    for kk, a, b, cell in G['POSE']:
        if kk == k and a <= t < b: return cell
    env = G['ENVS'].get(c['n'])
    talking = any(e['spk'] == c['n'] and e['t0'] <= t <= e['t1'] for e in G['EV'])
    if talking and env is not None:
        v = env[min(int(tq * FPS), len(env) - 1)]
        return c['idle'][1] if v > 0.35 else c['idle'][0]
    return c['idle'][2] if ((tq + (0.0 if k == 'H' else 1.6)) % 3.7) < 0.14 else c['idle'][0]

def shot_box(sh, lt):
    z = 1 + 0.015 * min(lt, 4) / 4
    if sh == 'W':
        w, h = CW / (1.12 * z), CH / (1.12 * z); cx, cy = 1920, CH / 2 + 80
    else:
        fx, fy = mulut_xy(sh); h = 800 / z; w = h * 16 / 9
        cx = fx + (w * 0.18 if sh == 'H' else -w * 0.18); cy = fy + h * 0.18
    cx = min(max(cx, w / 2), CW - w / 2); cy = min(max(cy, h / 2), CH - h / 2)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)

def render(fr):
    t = fr / FPS; im = G['BASE'].copy()
    for k in ('H', 'N'):
        sp, px, py = sprite(k, cell_for(k, t)); im.alpha_composite(sp, (px, py))
    for k, (m, p) in G['MICS'].items(): im.alpha_composite(m, p)
    sh, st = 'W', 0
    for a, s in G['SHOTS']:
        if t >= a: sh, st = s, a
    b = tuple(int(round(v)) for v in shot_box(sh, t - st))
    return np.asarray(im.convert('RGB').crop(b).resize((OW, OH), Image.LANCZOS))

# ------------------------------------------------------------------ utama
def main():
    a = sys.argv[1:]
    if a and a[0] == '--kontak':
        for n in a[1:]: kontak(n)
        return
    spek_path = a[0]; base = os.path.dirname(os.path.abspath(spek_path)); spek = json.load(open(spek_path))
    for n in (spek['kiri'], spek['kanan']):
        if n not in TOKOH: raise SystemExit(f'GAGAL: tokoh {n} belum ada di tokoh.json')
    for b in spek['baris']:
        if b['s'] not in TOKOH: raise SystemExit(f"GAGAL: penutur {b['s']} belum ada di tokoh.json")
    for n in spek['suara']:
        if n not in TOKOH: raise SystemExit(f'GAGAL: suara {n} tidak dikenal')
    nabila_layar = 'Nabila' in (spek['kiri'], spek['kanan'])
    print('susun audio')
    vo, ev, envs, total = susun_audio(spek, base, nabila_layar)
    mix = musik(vo, seed=spek.get('seed', 7)) if spek.get('musik', True) else vo
    siapkan_panggung(spek)
    G.update(EV=ev, ENVS=envs); rencana(spek, ev, total)
    print('bidikan', [(round(x, 1), s) for x, s in G['SHOTS']])
    if '--still' in a:
        fs = [float(v) for v in a[a.index('--still') + 1:]]
        ims = [Image.fromarray(render(int(f * FPS))).resize((640, 360)) for f in fs]
        S = Image.new('RGB', (1280, 360 * ((len(ims) + 1) // 2)))
        for i, m in enumerate(ims): S.paste(m, ((i % 2) * 640, (i // 2) * 360))
        S.save(os.path.join(base, 'still.jpg')); print('still.jpg'); return
    wav = os.path.join(base, '_mix.wav'); wf.write(wav, SR, (mix * 32767).astype(np.int16))
    out = os.path.join(base, spek.get('keluar', 'episode.mp4'))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}', '-r', str(FPS), '-i', '-',
                          '-i', wav, '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-c:a', 'aac', '-b:a', '160k', '-shortest', out], stdin=subprocess.PIPE)
    with Pool(min(4, os.cpu_count() or 2)) as pool:
        for fr in pool.imap(render, range(int(total * FPS)), chunksize=4): p.stdin.write(fr.tobytes())
    p.stdin.close(); p.wait()
    json.dump(dict(total=total, ev=ev, shots=G['SHOTS'], pose=G['POSE']), open(os.path.join(base, 'garis_waktu.json'), 'w'), indent=1)
    print('ok', out, round(total, 1), 'detik')

if __name__ == '__main__':
    main()
