"""
Backfill company_linkedin_url
==============================
Mengisi company_linkedin_url NULL di tabel jobs dengan cara:
  1. Generate slug kandidat dari company name
  2. Verify via LinkedIn search (DDG) untuk dapat slug yang tepat
  3. Optionally verify dengan HEAD request ke LinkedIn

Setup:
    pip install requests beautifulsoup4 python-dotenv sqlalchemy

Usage:
    python tools/backfill_linkedin_url.py --dry-run --verbose --limit 20
    python tools/backfill_linkedin_url.py --limit 50
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
import time
from typing import Optional
from urllib.parse import quote_plus

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# ──────────────────────────────────────────────────────────────────────────────
# Slug helpers
# ──────────────────────────────────────────────────────────────────────────────

# Sufiks yang sering muncul di nama company tapi tidak ada di slug LinkedIn
_STRIP_SUFFIXES = re.compile(
    r"\b(?:pt|tbk|cv|ltd|inc|llc|co|corp|group|indonesia|division|"
    r"technologies?|teknologi|solutions?|services?|digital|global|"
    r"financial|network|networks?|consulting|system|systems?|"
    r"internasional|international)\b",
    re.IGNORECASE,
)

_SPECIAL_CHARS = re.compile(r"[^a-z0-9\s-]")
_MULTI_SPACE   = re.compile(r"\s+")
_MULTI_DASH    = re.compile(r"-+")


def name_to_slugs(company_name: str) -> list[str]:
    """
    Generate beberapa kandidat slug LinkedIn dari nama company.
    LinkedIn pakai lowercase + dash, tapi variasinya banyak.

    Contoh:
      "PT Indofood CBP Sukses Makmur Tbk - Noodle Division"
      → ["pt-indofood-cbp-sukses-makmur-tbk-noodle-division",
         "indofood-cbp-sukses-makmur",
         "indofood"]
    """
    name = company_name.lower().strip()

    # Hapus karakter khusus kecuali spasi dan dash
    name_clean = _SPECIAL_CHARS.sub(" ", name)
    name_clean = _MULTI_SPACE.sub(" ", name_clean).strip()

    slugs = []

    # Slug 1: full name → dash
    slug_full = name_clean.replace(" ", "-")
    slug_full = _MULTI_DASH.sub("-", slug_full).strip("-")
    if slug_full:
        slugs.append(slug_full)

    # Slug 2: hapus sufiks umum, baru slug
    name_stripped = _STRIP_SUFFIXES.sub("", name_clean)
    name_stripped = _MULTI_SPACE.sub(" ", name_stripped).strip()
    slug_stripped  = name_stripped.replace(" ", "-")
    slug_stripped  = _MULTI_DASH.sub("-", slug_stripped).strip("-")
    if slug_stripped and slug_stripped not in slugs:
        slugs.append(slug_stripped)

    # Slug 3: hanya kata pertama yang panjang (≥4 char, bukan stopword)
    stopwords = {"the", "and", "for", "dengan", "dari"}
    words = [w for w in name_stripped.split() if len(w) >= 4 and w not in stopwords]
    if words:
        slug_short = words[0]
        if slug_short not in slugs:
            slugs.append(slug_short)

    # Slug 4: dua kata pertama
    if len(words) >= 2:
        slug_two = f"{words[0]}-{words[1]}"
        if slug_two not in slugs:
            slugs.append(slug_two)

    return slugs


# ──────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────────────────────────────────────

_UA_POOL = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
     "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"),
    ("Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"),
]

_LI_BLOCKED = ["uas/login", "authwall", "signup", "checkpoint"]


def make_session() -> "requests.Session":
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(_UA_POOL),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
    })
    return s


def _li_headers(li_at: str) -> dict:
    return {
        "Cookie": f"li_at={li_at}",
        "User-Agent": random.choice(_UA_POOL),
        "Referer": "https://www.linkedin.com/feed/",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
    }


def verify_linkedin_url(
    slug: str,
    session: "requests.Session",
    li_at: str,
) -> bool:
    """
    Verify apakah linkedin.com/company/<slug> valid.
    Pakai HEAD request dulu (hemat bandwidth), lalu cek redirect.
    """
    url = f"https://www.linkedin.com/company/{slug}/"
    try:
        r = session.head(url, timeout=10, allow_redirects=True,
                         headers=_li_headers(li_at))
        final_url = r.url
        # Kalau redirect ke login → slug tidak valid / tidak bisa verifikasi
        if any(b in final_url for b in _LI_BLOCKED):
            # Fallback: GET request — mungkin HEAD di-block tapi GET OK
            r2 = session.get(url, timeout=15, allow_redirects=True,
                             headers=_li_headers(li_at))
            final_url = r2.url
            if any(b in final_url for b in _LI_BLOCKED):
                return False  # cookie expired atau slug tidak ada
            # Cek apakah URL akhir masih mengandung slug kita
            return slug.lower() in r2.url.lower() and r2.status_code == 200
        return r.status_code in (200, 301, 302) and slug.lower() in final_url.lower()
    except Exception:
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 1: Cari via DuckDuckGo → ambil URL LinkedIn dari hasil
# ──────────────────────────────────────────────────────────────────────────────

_LI_URL_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/company/([a-z0-9\-_%]+)/?",
    re.IGNORECASE,
)


def find_linkedin_url_via_ddg(
    company_name: str,
    session: "requests.Session",
) -> Optional[str]:
    """
    Cari URL LinkedIn company via DuckDuckGo.
    Lebih akurat daripada construct slug manual karena DDG sudah index-nya benar.
    """
    queries = [
        f'"{company_name}" site:linkedin.com/company',
        f"{company_name} linkedin company Indonesia",
    ]
    for query in queries:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            r = session.get(url, timeout=12, allow_redirects=True,
                            headers={"User-Agent": random.choice(_UA_POOL)})
            if r.status_code != 200 or len(r.text) < 500:
                time.sleep(0.5)
                continue
        except Exception:
            time.sleep(0.5)
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # Cari di result URLs dan snippets
        for result_div in soup.select(".result"):
            result_text = result_div.get_text(" ", strip=True)

            # Harus ada kata dari nama company di result
            first_word = re.findall(r"[a-zA-Z]{3,}", company_name)
            if first_word and first_word[0].lower() not in result_text.lower():
                continue

            # Cari URL LinkedIn di href atau teks
            for a_tag in result_div.find_all("a", href=True):
                href = a_tag["href"]
                m = _LI_URL_RE.search(href)
                if m:
                    slug = m.group(1).rstrip("/")
                    return f"https://www.linkedin.com/company/{slug}/"

            # Cari di teks result (kadang URL muncul sebagai teks)
            m = _LI_URL_RE.search(result_text)
            if m:
                slug = m.group(1).rstrip("/")
                return f"https://www.linkedin.com/company/{slug}/"

        time.sleep(random.uniform(0.5, 1.0))

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Strategy 2: Construct slug + verify
# ──────────────────────────────────────────────────────────────────────────────

def find_linkedin_url_via_slug(
    company_name: str,
    session: "requests.Session",
    li_at: str,
    verbose: bool = False,
) -> Optional[str]:
    """
    Construct slug kandidat dari nama company, lalu verify ke LinkedIn.
    Dipakai sebagai fallback jika DDG tidak menemukan URL.
    """
    if not li_at:
        return None  # tidak bisa verify tanpa cookie

    slugs = name_to_slugs(company_name)
    for slug in slugs:
        if verbose:
            print(f"        [SLUG] coba: {slug}")
        if verify_linkedin_url(slug, session, li_at):
            url = f"https://www.linkedin.com/company/{slug}/"
            if verbose:
                print(f"        [SLUG] ✓ valid: {url}")
            return url
        time.sleep(random.uniform(0.3, 0.7))

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Orchestrator
# ──────────────────────────────────────────────────────────────────────────────

def find_linkedin_url(
    company_name: str,
    session: "requests.Session",
    li_at: str,
    verbose: bool = False,
) -> Optional[str]:
    """Cari LinkedIn URL company dengan semua strategi."""

    # Strategi 1: DDG search (lebih akurat, tidak butuh cookie)
    url = find_linkedin_url_via_ddg(company_name, session)
    if url:
        if verbose:
            print(f"        ✓ DDG: {url}")
        return url
    if verbose:
        print(f"        ✗ DDG: tidak ketemu")

    time.sleep(random.uniform(0.3, 0.6))

    # Strategi 2: Construct slug + verify (butuh cookie valid)
    url = find_linkedin_url_via_slug(company_name, session, li_at, verbose)
    if url:
        if verbose:
            print(f"        ✓ Slug: {url}")
        return url
    if verbose:
        print(f"        ✗ Slug: tidak ada yang valid")

    return None


# ──────────────────────────────────────────────────────────────────────────────
# DB helpers
# ──────────────────────────────────────────────────────────────────────────────

def get_companies_without_url(
    limit: Optional[int] = None,
) -> list[tuple[str, int]]:
    """Return list (company_name, job_count) yang company_linkedin_url-nya NULL."""
    from sqlalchemy import func
    from database.connection import get_db_context
    from database.models import Job
    with get_db_context() as db:
        rows = (
            db.query(Job.company, func.count(Job.id).label("cnt"))
            .filter(
                Job.company_linkedin_url.is_(None),
                Job.company.isnot(None),
                Job.company != "",
                Job.company != "N/A",
            )
            .group_by(Job.company)
            .order_by(func.count(Job.id).desc())
            .all()
        )
    results = [(name, cnt) for name, cnt in rows]
    return results[:limit] if limit else results


def count_null_urls() -> int:
    from database.connection import get_db_context
    from database.models import Job
    with get_db_context() as db:
        return db.query(Job).filter(Job.company_linkedin_url.is_(None)).count()


def update_linkedin_url(company_name: str, linkedin_url: str) -> int:
    """Update company_linkedin_url untuk semua jobs dengan company_name tsb."""
    from database.connection import get_db_context
    from database.models import Job
    with get_db_context() as db:
        jobs = (
            db.query(Job)
            .filter(
                Job.company == company_name,
                Job.company_linkedin_url.is_(None),
            )
            .all()
        )
        for job in jobs:
            job.company_linkedin_url = linkedin_url
        db.commit()
        return len(jobs)


# ──────────────────────────────────────────────────────────────────────────────
# Main runner
# ──────────────────────────────────────────────────────────────────────────────

def run_backfill(
    limit: Optional[int] = None,
    dry_run: bool = False,
    verbose: bool = False,
    pause_range: tuple[float, float] = (1.0, 2.0),
) -> dict:
    if not REQUESTS_AVAILABLE:
        print("[ERROR] Jalankan: pip install requests beautifulsoup4")
        return {}

    li_at = os.getenv("LINKEDIN_LI_AT", "").strip()
    if not li_at:
        print("[WARN] LINKEDIN_LI_AT tidak ada di .env — slug verification dinonaktifkan")

    total_before = count_null_urls()
    print("=" * 70)
    print("BACKFILL company_linkedin_url")
    print("=" * 70)
    print(f"Jobs dengan linkedin_url NULL  : {total_before}")

    companies = get_companies_without_url(limit=limit)
    if not companies:
        print("[INFO] Tidak ada company yang perlu diproses.")
        return {}

    print(f"Company unik                   : {len(companies)}")
    print(f"Mode                           : {'DRY-RUN' if dry_run else 'WRITE'}")
    print(f"Strategi                       : DDG search → Slug construct + verify")
    print("=" * 70 + "\n")

    session = make_session()
    stats = dict(processed=0, found=0, updated_jobs=0, skipped=0)

    for idx, (name, job_cnt) in enumerate(companies, 1):
        print(f"[{idx}/{len(companies)}] {name}  ({job_cnt} jobs)")

        url = find_linkedin_url(name, session, li_at, verbose=verbose)

        if not url:
            print(f"    [SKIP] Tidak ditemukan")
            stats["skipped"] += 1
        else:
            print(f"    [URL]  {url}")
            if dry_run:
                print(f"    [DRY-RUN] Akan update {job_cnt} jobs")
            else:
                updated = update_linkedin_url(name, url)
                print(f"    [SAVED] {updated} jobs diupdate")
                stats["updated_jobs"] += updated
            stats["found"] += 1

        stats["processed"] += 1
        if idx < len(companies):
            time.sleep(random.uniform(*pause_range))

    total_after = count_null_urls() if not dry_run else total_before
    print("\n" + "=" * 70)
    print("BACKFILL SELESAI")
    print("=" * 70)
    print(f"Company diproses  : {stats['processed']}")
    print(f"URL ditemukan     : {stats['found']}")
    print(f"Jobs diupdate     : {stats['updated_jobs']}")
    print(f"Skip              : {stats['skipped']}")
    print(f"NULL sebelum      : {total_before}")
    print(f"NULL sesudah      : {total_after}")
    print(f"Berhasil diisi    : {total_before - total_after}")
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill company_linkedin_url NULL.")
    parser.add_argument("--limit",     type=int,   default=None)
    parser.add_argument("--dry-run",   action="store_true")
    parser.add_argument("--verbose",   action="store_true")
    parser.add_argument("--pause-min", type=float, default=1.0)
    parser.add_argument("--pause-max", type=float, default=2.0)
    args = parser.parse_args()
    run_backfill(
        limit=args.limit,
        dry_run=args.dry_run,
        verbose=args.verbose,
        pause_range=(args.pause_min, args.pause_max),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())