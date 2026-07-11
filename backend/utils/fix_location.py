"""
fix_location.py — Perbaiki kolom location di job_analysis
dengan mengambil ulang dari jobs.location (data mentah) dan normalisasi ulang.

Script ini TIDAK mengandung logika normalisasi apa pun — semua aturan
normalisasi (termasuk fix bug "Cilandak -> Landak" dan "West Jakarta ->
Jakarta") ada di location_handler.py. Pastikan kamu memakai versi
location_handler.py yang SUDAH DIPERBAIKI sebelum menjalankan script ini,
supaya data lama yang salah ikut tertimpa dengan nilai yang benar.

Cara pakai:
    1. Letakkan fix_location.py dan location_handler.py (versi terbaru!)
       dalam SATU folder
    2. pip install psycopg2-binary --break-system-packages
    3. Isi DB_CONFIG di bawah
    4. python fix_location.py
       (jalankan ulang lagi setiap kali location_handler.py diperbaiki,
        supaya seluruh data ikut ternormalisasi ulang)
"""

import psycopg2
from psycopg2.extras import execute_batch

# ─── KONFIGURASI ────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "skills_trend_db",
    "user":     "postgres",
    "password": "[PASSWORD]",
}
# ────────────────────────────────────────────────────────────────────────────

try:
    from location_handler import LocationNormalizer, KabupatenData
except ImportError:
    print("❌ ERROR: location_handler.py tidak ditemukan di folder yang sama.")
    exit(1)


def _sanity_check_normalizer():
    """
    Cek cepat bahwa location_handler.py yang terimport adalah versi yang
    sudah diperbaiki (punya KABUPATEN_ALIASES untuk West/East/South/North
    Jakarta, dan tidak lagi salah menangkap 'Cilandak' jadi 'Landak').
    Kalau versi lama masih terpakai, fix_location.py akan menormalisasi
    ulang data tapi TETAP MENGHASILKAN nilai yang salah — jadi lebih baik
    berhenti di sini dan kasih tahu penyebabnya, daripada lanjut diam-diam.
    """
    problems = []

    if not hasattr(KabupatenData, "KABUPATEN_ALIASES"):
        problems.append(
            "location_handler.py belum punya KABUPATEN_ALIASES — ini versi LAMA. "
            "'West Jakarta' akan salah dinormalisasi jadi 'Jakarta' (provinsi), "
            "bukan 'Jakarta Barat' (kota)."
        )
    else:
        hasil = LocationNormalizer.normalize("West Jakarta")
        if hasil != "Jakarta Barat":
            problems.append(
                f"'West Jakarta' menghasilkan '{hasil}', seharusnya 'Jakarta Barat'."
            )

    hasil_cilandak = LocationNormalizer.normalize("Cilandak, Jakarta Selatan")
    if hasil_cilandak == "Landak":
        problems.append(
            "Bug 'Cilandak -> Landak' masih terjadi — location_handler.py belum "
            "memakai word-boundary matching."
        )

    if problems:
        print("❌ location_handler.py yang terdeteksi sepertinya BUKAN versi terbaru:\n")
        for p in problems:
            print(f"   • {p}")
        print(
            "\n   Ganti location_handler.py dengan versi yang sudah diperbaiki "
            "(yang punya KABUPATEN_ALIASES dan word-boundary matching di "
            "find_kabupaten/find_province), lalu jalankan ulang script ini.\n"
        )
        return False

    return True


def main():
    if not _sanity_check_normalizer():
        return

    print(f"\n🔌 Menghubungkan ke PostgreSQL ({DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']})...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
    except psycopg2.OperationalError as e:
        print(f"❌ Gagal konek:\n   {e}")
        return

    cur = conn.cursor()

    # ── Ambil data: JOIN job_analysis ke jobs untuk dapat location MENTAH ──
    print("🔍 Mengambil data dari job_analysis JOIN jobs...")
    cur.execute("""
        SELECT
            ja.id                AS ja_id,
            ja.location          AS location_lama,
            j.location           AS location_mentah
        FROM job_analysis ja
        JOIN jobs j ON ja.job_id = j.id
        WHERE j.location IS NOT NULL AND j.location != ''
        ORDER BY ja.id
    """)
    rows = cur.fetchall()
    print(f"   Ditemukan {len(rows):,} baris dengan data lokasi.")

    # ── Normalisasi ulang dari data mentah ──
    changes = []
    for ja_id, location_lama, location_mentah in rows:
        location_baru = LocationNormalizer.normalize(location_mentah)
        # Update jika berbeda dari nilai lama (case-insensitive untuk tangani METRO vs Metro)
        if location_baru.strip().lower() != (location_lama or "").strip().lower():
            changes.append((ja_id, location_lama, location_mentah, location_baru))

    # ── Preview ──
    print("\n" + "=" * 90)
    print("  PREVIEW PERBAIKAN job_analysis.location")
    print("  (Sumber: jobs.location → normalize ulang → update job_analysis.location)")
    print("=" * 90)
    print(f"  Total baris diproses  : {len(rows):,}")
    print(f"  Baris perlu diupdate  : {len(changes):,}")
    print("=" * 90)

    if not changes:
        print("\n  ✅ Semua location sudah benar. Tidak ada yang perlu diubah.")
        cur.close()
        conn.close()
        return

    # Ringkasan unik
    seen = {}
    for _, location_lama, location_mentah, location_baru in changes:
        key = (location_mentah, location_lama or "NULL", location_baru)
        seen[key] = seen.get(key, 0) + 1

    print(f"\n  {'DATA MENTAH (jobs)':<32}  {'LAMA/SALAH':<20}  {'BARU/BENAR':<20}  {'JML':>5}")
    print("  " + "-" * 82)
    for (mentah, lama, baru), cnt in sorted(seen.items(), key=lambda x: -x[1]):
        m = (mentah[:29] + "...") if len(mentah) > 32 else mentah
        l = (lama[:17]   + "...") if len(lama)   > 20 else lama
        b = (baru[:17]   + "...") if len(baru)   > 20 else baru
        print(f"  {m:<32}  {l:<20}  {b:<20}  {cnt:>5,}")
    print()

    # ── Konfirmasi ──
    confirm = input("  ❓ Lanjutkan UPDATE? (ketik 'ya' untuk konfirmasi): ").strip().lower()
    if confirm != "ya":
        print("\n  ⚠️  Dibatalkan. Tidak ada perubahan.")
        cur.close()
        conn.close()
        return

    # ── Eksekusi ──
    print(f"\n  ⏳ Menjalankan UPDATE {len(changes):,} baris...")
    try:
        execute_batch(
            cur,
            "UPDATE job_analysis SET location = %s WHERE id = %s",
            [(location_baru, ja_id) for ja_id, _, _, location_baru in changes],
            page_size=500
        )
        conn.commit()
        print(f"  ✅ Selesai! {len(changes):,} baris berhasil diupdate.")

        # Verifikasi distribusi sesudah update
        cur.execute("""
            SELECT location, COUNT(*) as cnt
            FROM job_analysis
            GROUP BY location
            ORDER BY cnt DESC
            LIMIT 20
        """)
        print("\n  📊 Distribusi location sesudah update:")
        print(f"  {'LOCATION':<35}  {'JUMLAH':>7}")
        print("  " + "-" * 45)
        for loc, cnt in cur.fetchall():
            print(f"  {(loc or 'NULL'):<35}  {cnt:>7,}")

    except Exception as e:
        conn.rollback()
        print(f"  ❌ Error, rollback dilakukan:\n     {e}")

    cur.close()
    conn.close()
    print()


if __name__ == "__main__":
    main()