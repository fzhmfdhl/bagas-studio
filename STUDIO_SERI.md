# Jalur Seri AI (Reels teks + ikon) — sistem visual @jerapahmerah_ sejak 11 Nov 2026

Baca setelah STUDIO.md. Jalur ini berlaku untuk pesanan **brand pribadi Jers** yang punya field `seri` (`"A"` = AI yang benar-benar dipakai,
`"B"` = Salah kaprah). Pesanan lama tanpa `seri` tetap memakai alur konsep bebas di STUDIO.md.
Topik akun sekarang: **AI di industri kreatif**, untuk orang yang ingin belajar AI (bisnis hanya topik sampingan; Desain, Bagas dan Rusdi bukan topik lagi).

Aturan emas 1 di STUDIO.md ("gaya beda dari 6 terakhir") DIGANTI untuk jalur ini: **sistem visual dikunci** supaya akun konsisten,
yang berganti adalah **isi tengah** (pilihan adegan, urutan, transisi, ikon). Aturan 2 juga diperbarui: karakter baru boleh tampil (lihat bawah).

## Sistem visual (dikunci, jangan diubah tanpa perintah Jers)
- **Warna:** maroon `#6B1423` (utama) + putih `#FFFFFF` (sekunder) + pink pucat `#F2C9D0` hanya untuk aksen kecil (kursor, subjudul di atas maroon).
  Latar adegan berselang-seling maroon dan putih. Tanpa gradasi, cahaya, bayangan, neon.
- **Font:** hanya **Space Mono** (`assets/fonts/SpaceMono-*.ttf`). Jangan memakai font lain.
- **Minimalis:** satu ide per layar, sedikit elemen, banyak ruang kosong. Jers tidak suka yang besar dan sesak.
- **Rata tengah:** semua teks, ikon, dan judul rata tengah; isi berada di tengah layar (y 480–1250). Daftar memakai SATU kolom tetap
  (lebar dari kata terpanjang), ikon sejajar tengah tinggi huruf, garis coret di tengah huruf kecil dan hanya sepanjang kata.
- **Zona aman 1080x1920:** konten di y 235–1470, x 100–980; area tombol kanan (x ≥ 940, y ≥ 1150) kosong. Sampul harus terbaca di potongan grid tengah 3:4.
- **Karakter** (Jers versi pixel chibi, hoodie jerapah merah + jeans, `assets/sprites/seri_jers_*.png`): HANYA di sampul (frame 0–4) dan penutup.
  Isi video memakai **ikon Lucide** (`assets/lucide/`, ±1.890 ikon) yang bergerak (pop-in memantul, mengambang, bergetar). Pose: wave, idle, show, talk, idea, laugh, shock.
  Outline sprite putih/maroon (jangan ada lingkaran di belakangnya). Jers adalah satu-satunya orang yang boleh tampil; Rusdi/Bagas hanya sesekali bila naskah meminta.
- **Tetap di setiap video:** (1) sampul = frame 0–4 (jadi thumbnail, jangan minta Jers unggah sampul); (2) intro titik: titik merah menulis tagline
  "KERJA KREATIF, DIBANTU AI." kata demi kata, memudar, titik membesar jadi lingkaran yang membanjiri layar; (3) penutup: handle diketik, ajakan simpan/ikuti, karakter melambai.
- **Tanpa suara/musik** kecuali Jers meminta (Reels teks; musik tren ditambahkan Jers saat unggah). 15–25 detik, 30 fps.

## Perpustakaan adegan (`toolkit/seri.py`)
`kata_besar` (pernyataan besar + kata disorot kotak) · `salah` (kata besar bergetar + ikon silang) · `daftar` (daftar bergulir berikon, opsi coret pertama) ·
`hitung` (angka menghitung, satuan berganti) · `langkah` (langkah 1-2-3/4 berikon). Transisi masuk: `lingkaran`, `dorong_atas`, `dorong_kiri`, `garis` (adegan pertama selalu banjir dari intro).
Adegan baru dengan gaya yang sama boleh ditambahkan ke `toolkit/seri.py` (fungsi `sc_*` + daftar `SCENES`), terutama dari referensi gerak Jers:
sorotan kata dengan kotak, kartu "masalah" bertumpuk, angka dalam lingkaran, ikon + teks diketik bertingkat, bingkai layar berisi prompt (sebelum/sesudah), tombol klik "Selesai".

**Anti-ulang:** pilih 3–5 adegan per video. Kombinasi dan urutan adegan tidak boleh sama dengan **3 video terakhir** (cek `studio_meta.seri_riwayat`),
dan arah transisi/ikon berganti. Simpan ringkasan `["kata_besar","salah","daftar",...]` ke `studio_meta.seri_riwayat` (12 terakhir).

## Alur kerja (spec JSON, bukan kode baru)
1. **KONSEP = 2 opsi motion (A dan B)** dari naskah Rusdi: dua kombinasi adegan yang berbeda (adegan, urutan, ikon, transisi). Visualnya sama (sistem dikunci).
   Tiap opsi: tulis `spec_A.json` / `spec_B.json` (format ada di docstring `toolkit/seri.py`; `python3 toolkit/seri.py contoh` mencetak contoh),
   lalu `python3 toolkit/seri.py cek spec_X.json papan_X.png` → papan cerita 216x384 per cuplikan dengan garis zona aman (biru), sumbu tengah (hijau), area tombol (ungu).
   **Lihat papan itu (Read)**; perbaiki sampai tidak ada teks terpotong, tidak tengah, menempel, atau bertumpuk. Pecah papan jadi 3–4 frame kunci (sampul + 2–3 adegan)
   sebagai JPG 540x960 untuk `konsep.frames` seperti di STUDIO.md. Isi `konsep` dengan `nama` ("Opsi A: daftar bergulir"), `gaya` (daftar adegan), `ringkas`, `palet` (["#6B1423","#FFFFFF"]).
2. **RENDER** (setelah Jers memilih; boleh digabung/diubah "A tapi transisi dari B"): `python3 toolkit/seri.py render spec.json final.mp4` (±1 menit).
   Lalu audit wajib: `python3 toolkit/studio.py audit final.mp4 audit/ 0.33` dan lihat SEMUA lembar. Ekspor, unggah, dan catat seperti di STUDIO.md.
   Jika ada lampiran revisi, tiap kesalahan dari Jers jadi aturan tambahan: tulis ke daftar di bawah.
3. Salah kaprah #N: sampul `baris` + `kata_a` + `sorot` berbentuk pertanyaan/klaim ("Prompt panjang = bagus?"). AI yang benar-benar dipakai #N: sampul berisi hasil/alat konkret.
   Sampul maks 3 baris, baris terpanjang ≤ 12 huruf pada ukuran besar (mesin mengecilkan otomatis, tapi pendek lebih kuat).

## Isi (kerja sama dengan Rusdi)
- Naskah dari Rusdi: `seri`, `nomor`, `sampul`, 3–5 poin pendek, ajakan penutup (default "simpan, coba besok pagi." / "ikuti untuk seri berikutnya."), `caption`.
- Jangan mengarang angka/klaim hasil. Angka di adegan `hitung` harus contoh jujur (mis. "500 kata" vs "3 kalimat" sebagai ilustrasi, bukan klaim statistik) — beri tanda "contoh" bila ragu.
- Satu video = satu pelajaran yang bisa dicoba penonton hari itu.

## Kesalahan yang pernah terjadi (jangan ulangi)
- Elemen tidak berada di tengah / tiap baris ditengahkan sendiri sehingga ikon tidak segaris → pakai satu kolom tetap.
- Teks kecil dan layar kosong → huruf besar, isi di tengah layar, satu ide per layar.
- Ikon tidak sejajar dengan teks di dalam blok judul+keterangan → ikon di tengah vertikal blok.
