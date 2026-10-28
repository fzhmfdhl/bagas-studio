#!/usr/bin/env python3
"""Render ikon Lucide (assets/lucide/*.svg) jadi PNG transparan untuk kartu motion.

Pakai:
    python3 toolkit/lucide.py ic/ "message-circle:ink" "sparkles:ink" "trending-down:paper"
    # -> ic/message-circle_ink.png, dst.

Warna yang tersedia: ink (#1B191F), acc (#C0502E), paper (#F4F2ED), mute (#928E8A),
atau hex bebas supaya cocok dengan tema konsep, mis. "mic:#E48C3C".
Di dalam kode render, muat hasilnya dengan nama berkas tanpa ekstensi, mis. 'message-circle_ink'.
"""
import os, sys, json, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SVG = os.path.join(ROOT, 'assets', 'lucide')
COL = {'ink': '#1B191F', 'acc': '#C0502E', 'paper': '#F4F2ED', 'mute': '#928E8A'}
SHARP = '/opt/npm-tools/node_modules/sharp'


def render(outdir, specs, size=320, stroke=1.6):
    """specs: daftar 'nama-ikon:warna'. Mengembalikan daftar path PNG."""
    os.makedirs(outdir, exist_ok=True)
    jobs = []
    for s in specs:
        name, _, col = s.partition(':')
        col = col or 'ink'
        if col.startswith('#'):                      # warna bebas, mis. "mic:#F4F2ED"
            hexv = col
            if len(hexv) != 7:
                raise ValueError('warna hex harus 7 karakter: %s' % col)
            col = 'c' + hexv[1:]
            COL.setdefault(col, hexv)
        if col not in COL:
            raise ValueError('warna tidak dikenal: %s' % col)
        p = os.path.join(SVG, name + '.svg')
        if not os.path.exists(p):
            raise FileNotFoundError('ikon tidak ada: %s (lihat assets/lucide/)' % name)
        jobs.append({'src': p, 'out': os.path.join(outdir, '%s_%s.png' % (name, col)),
                     'color': COL[col]})
    js = """
const sharp=require(%s);const fs=require('fs');
const jobs=JSON.parse(process.env.LUCIDE_JOBS),SZ=%d,SW=%s;
(async()=>{for(const j of jobs){
  let s=fs.readFileSync(j.src,'utf8');
  s=s.replace(/stroke="currentColor"/,'stroke="'+j.color+'"')
     .replace(/stroke-width="2"/,'stroke-width="'+SW+'"')
     .replace('width="24"','width="'+SZ+'"').replace('height="24"','height="'+SZ+'"');
  await sharp(Buffer.from(s),{density:600}).resize(SZ,SZ).png().toFile(j.out);
}})();
""" % (json.dumps(SHARP), size, stroke)
    env = dict(os.environ, LUCIDE_JOBS=json.dumps(jobs))
    subprocess.run(['node', '-e', js], check=True, env=env)
    return [j['out'] for j in jobs]


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    for p in render(sys.argv[1], sys.argv[2:]):
        print(p)
