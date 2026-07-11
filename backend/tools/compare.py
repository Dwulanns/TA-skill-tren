import pandas as pd
import psycopg2
from rapidfuzz import fuzz, process

# ── 1. Load CSV Kaggle ──────────────────────────────────────────────
try:
    df_kaggle = pd.read_csv("tools/kaggle_skills3.csv", header=None, names=["skill"], quoting=3, on_bad_lines='skip')
    kaggle_skills = df_kaggle["skill"].dropna().str.strip().tolist()
    print(f"✅ CSV loaded: {len(kaggle_skills)} skills")
except Exception as e:
    print(f"❌ Gagal baca CSV: {e}")
    exit()

# ── 2. Koneksi ke PostgreSQL ────────────────────────────────────────
try:
    conn = psycopg2.connect(
        host="localhost",
        database="skills_trend_db",
        user="postgres",       # ← ganti username PostgreSQL kamu
        password="[PASSWORD]"    # ← ganti password PostgreSQL kamu
    )
    print("✅ Koneksi DB berhasil")
except Exception as e:
    print(f"❌ Gagal konek DB: {e}")
    exit()

# Cek dulu skill_type_id yang ada
try:
    df_types = pd.read_sql("SELECT skill_type_id, COUNT(*) as total FROM skills GROUP BY skill_type_id", conn)
    print("\nSkill type di DB:")
    print(df_types)
except Exception as e:
    print(f"❌ Gagal query: {e}")
    conn.close()
    exit()

# Ambil technical skill — sesuaikan skill_type_id setelah lihat output di atas
query = """
    SELECT id, name, normalized_name
    FROM skills
    WHERE skill_type_id = 3
"""
df_skills = pd.read_sql(query, conn)
conn.close()
print(f"\n✅ Skills dari DB: {len(df_skills)} rows")

if len(df_skills) == 0:
    print("❌ Tidak ada data skills, cek skill_type_id-nya!")
    exit()

# ── 3. Matching ─────────────────────────────────────────────────────
THRESHOLD = 80
results = []

print("\n⏳ Proses matching... (mungkin butuh beberapa menit)")
for i, (_, row) in enumerate(df_skills.iterrows()):
    skill_name = row["normalized_name"] or row["name"]
    match = process.extractOne(skill_name, kaggle_skills, scorer=fuzz.token_sort_ratio)

    if match and match[1] >= THRESHOLD:
        results.append({"skill_id": row["id"], "skill_db": skill_name,
                        "match_kaggle": match[0], "score": match[1], "status": "TP"})
    else:
        results.append({"skill_id": row["id"], "skill_db": skill_name,
                        "match_kaggle": None, "score": match[1] if match else 0, "status": "FP"})

    if (i + 1) % 50 == 0:
        print(f"  {i+1}/{len(df_skills)} diproses...")

# ── 4. Hitung metrik ────────────────────────────────────────────────
df_result = pd.DataFrame(results)

TP = len(df_result[df_result["status"] == "TP"])
FP = len(df_result[df_result["status"] == "FP"])
matched_kaggle = set(df_result["match_kaggle"].dropna())
FN = len([s for s in kaggle_skills if s not in matched_kaggle])

precision = TP / (TP + FP) if (TP + FP) > 0 else 0
recall    = TP / (TP + FN) if (TP + FN) > 0 else 0
f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

print(f"\n📊 HASIL EVALUASI")
print(f"TP: {TP} | FP: {FP} | FN: {FN}")
print(f"Precision : {precision:.2%}")
print(f"Recall    : {recall:.2%}")
print(f"F1-Score  : {f1:.2%}")

# ── 5. Simpan ───────────────────────────────────────────────────────
df_result.to_csv("tools/hasil_evaluasi_technical_skill.csv", index=False)
print("\n✅ Hasil disimpan ke tools/hasil_evaluasi_technical_skill.csv")