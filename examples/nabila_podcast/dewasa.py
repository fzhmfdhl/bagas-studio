"""Alat khusus segmen PEMBICARAAN DEWASA (pilar konspirasi JERSTALK).

Isi:
  musik_misteri(dur, seed)   -> latar misterius dan menegangkan (numpy mono, SR dari toolkit.studio)
  stinger(jenis)             -> hentakan saat label klaim muncul: 'terbukti', 'diklaim', 'belum', 'buka'
  LABEL                      -> warna tetap tiga label klaim (dipakai semua konsep)
  dengar(t, mulai, angguk)   -> indeks pose pendengar (diam atau mengangguk) pada waktu t

Musik dibuat sendiri dari Synth (bebas hak cipta). Seed beda tiap episode supaya tidak terdengar sama,
tetapi karakternya tetap: dengung rendah, denyut seperti detak jantung, nada tinggi yang menggantung,
dan sapuan derau pelan. Tidak ada melodi ceria, tidak ada drum ramai.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from toolkit.studio import SR, Synth as S

# Warna tiga label klaim: DIKUNCI untuk semua konsep Pembicaraan Dewasa.
LABEL = {
    'TERBUKTI': dict(bg=(47, 122, 74), fg=(255, 255, 255)),
    'DIKLAIM': dict(bg=(226, 165, 58), fg=(42, 29, 6)),
    'BELUM TERBUKTI': dict(bg=(181, 40, 42), fg=(255, 255, 255)),
}

# Pose karakter (sprite assets/sprites/<nama>_c_<i>.png)
# Jers  : 0 jempol, 1 tangan terbuka (bicara), 2 tenang (mendengar), 3 tenang + kepala menunduk (angguk)
# Nabila: 0 tangan di dagu, 1 tenang (mendengar), 2 tangan terbuka (bicara), 3 tenang + kepala menunduk (angguk)
DIAM = {'J': 2, 'N': 1}
ANGGUK = {'J': 3, 'N': 3}


def dengar(who, t, angguk_pada=()):
    """Pose pendengar pada waktu t. angguk_pada: daftar waktu (detik) saat pendengar mengangguk.
    Satu anggukan = turun 0,18 dtk, naik, turun lagi 0,18 dtk (dua ketukan kecil), total sekitar 0,7 dtk."""
    for a in angguk_pada:
        e = t - a
        if 0 <= e < .18 or .36 <= e < .54:
            return ANGGUK[who]
    return DIAM[who]


def _rv(x, sr=SR):
    """Gema ruang sederhana (beberapa tunda dengan umpan balik)."""
    out = x.copy()
    for d, g in ((.031, .35), (.047, .3), (.083, .25), (.137, .2), (.211, .15)):
        k = int(d * sr); y = np.zeros(len(x) + k * 6)
        y[:len(x)] += x
        for i in range(1, 6):
            y[k * i:k * i + len(x)] += x * (g ** i)
        out += y[:len(x)] * .35
    return out / np.max(np.abs(out) + 1e-9) * np.max(np.abs(x) + 1e-9)


def _lp(x, k):
    return S.lowpass(S.lowpass(x, k), k)


def musik_misteri(dur, seed=0, nada=None, detak=1.15):
    """Latar misterius. dur detik. seed: ganti tiap episode. nada: midi akar (bawaan acak 36-41).
    detak: jeda denyut (detik); denyut makin rapat menjelang akhir supaya tegang."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR); t = np.arange(n) / SR
    m = nada if nada is not None else int(rng.integers(36, 42))
    f = S.midi(m)
    # 1. dengung rendah: dua gelombang yang sedikit sumbang, berdenyut pelan
    lfo = .6 + .4 * np.sin(2 * np.pi * (.07 + rng.random() * .05) * t)
    drone = (np.sin(2 * np.pi * f * t) + .6 * np.sin(2 * np.pi * (f * 1.006) * t) + .25 * np.sin(2 * np.pi * f * .5 * t))
    saw = _lp(2 * ((t * f * 2) % 1) - 1, 40) * .18
    drone = (drone * .22 + saw) * lfo
    # 2. nada tinggi menggantung: interval sumbang (tritonus / sekon kecil) bergantian, naik-turun pelan
    pad = np.zeros(n)
    iv = [6, 1, 13, 18][int(rng.integers(0, 4))]
    for k, mm in enumerate([m + 24, m + 24 + iv]):
        ff = S.midi(mm)
        trem = .5 + .5 * np.sin(2 * np.pi * (3.1 + k * .7) * t)
        sw = np.clip(np.sin(2 * np.pi * (1 / 16) * t + k * 1.7), 0, 1) ** 2
        pad += np.sin(2 * np.pi * ff * t) * trem * sw * .05
    # 3. denyut seperti detak jantung (dua pukulan rendah), makin rapat di 25% terakhir
    pulse = np.zeros(n); tt = 1.0
    while tt < dur - .3:
        g = .55 + .25 * (tt / dur)
        b = S.kick(.22 * g)
        b = _lp(b, 6)
        i = int(tt * SR); j = min(n, i + len(b)); pulse[i:j] += b[:j - i]
        i2 = int((tt + .22) * SR); j2 = min(n, i2 + len(b))
        if i2 < n: pulse[i2:j2] += b[:j2 - i2] * .6
        tt += detak * (1 - .35 * max(0, (tt / dur - .75) / .25))
    # 4. sapuan derau (angin) tiap 8-12 detik
    air = np.zeros(n); tt = 2.0 + rng.random() * 3
    while tt < dur - 3:
        L = int(3.5 * SR); x = _lp(rng.uniform(-1, 1, L), 30)
        env = np.sin(np.linspace(0, np.pi, L)) ** 2
        i = int(tt * SR); j = min(n, i + L); air[i:j] += (x * env)[:j - i] * .05
        tt += 8 + rng.random() * 4
    out = drone + _rv(pad) + pulse + air
    # masuk dan keluar halus
    fi, fo = int(1.2 * SR), int(2.0 * SR)
    out[:fi] *= np.linspace(0, 1, fi); out[-fo:] *= np.linspace(1, 0, fo)
    return out / (np.max(np.abs(out)) + 1e-9) * .5


def stinger(jenis='terbukti'):
    """Hentakan pendek (0,8-1,6 dtk). Taruh tepat saat label klaim mendarat di layar."""
    if jenis == 'buka':      # pembuka: dentum rendah + desis naik
        n = int(1.6 * SR); t = np.arange(n) / SR
        boom = np.sin(2 * np.pi * (55 * np.exp(-t * 2) + 30) * t) * np.exp(-t * 2.2) * .5
        hiss = _lp(np.random.uniform(-1, 1, n), 8) * np.clip(1 - t / .6, 0, 1) * .08
        return boom + hiss
    if jenis == 'terbukti':  # dentum mantap, satu nada
        n = int(1.0 * SR); t = np.arange(n) / SR
        return (np.sin(2 * np.pi * 65 * t) * np.exp(-t * 4) * .45 + np.sin(2 * np.pi * 130 * t) * np.exp(-t * 6) * .12)
    if jenis == 'diklaim':   # dua nada menggantung
        a = S.note('sine', 69, .9, vol=.12, a=.01, r=.6); b = S.note('sine', 75, .9, vol=.1, a=.01, r=.6)
        return _rv(a + b)
    if jenis == 'belum':     # klaster sumbang yang tertahan
        n = int(1.2 * SR); t = np.arange(n) / SR
        x = sum(np.sin(2 * np.pi * S.midi(m) * t) for m in (58, 59, 64)) * np.exp(-t * 2.5) * .1
        return _rv(x + np.sin(2 * np.pi * 49 * t) * np.exp(-t * 3) * .3)
    raise ValueError(jenis)


if __name__ == '__main__':
    # Contoh 30 detik: python3 examples/nabila_podcast/dewasa.py contoh.wav
    from toolkit.studio import save_wav, place, normalize
    out = sys.argv[1] if len(sys.argv) > 1 else 'musik_misteri_contoh.wav'
    m = musik_misteri(30, seed=7)
    place(m, stinger('buka'), .2); place(m, stinger('terbukti'), 9.0); place(m, stinger('diklaim'), 16.0); place(m, stinger('belum'), 22.5)
    save_wav(out, normalize(m, .9)); print('tersimpan', out)
