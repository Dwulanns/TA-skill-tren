"""
LinkedIn Company Employee Size Scraper - OPTIMIZED VERSION
============================================================
Location: scraper/employee_size_scraper.py
"""

import os
import sys
import json
import re
import random
import time  # ← TAMBAHKAN INI (penting untuk time.sleep())
import logging
from typing import Optional, Dict, List, Tuple, Callable  # ← TAMBAHKAN Callable
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ============================================================
# SETUP PATH
# ============================================================

# Tambahkan root project ke path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

# ============================================================
# IMPORTS
# ============================================================

from database.connection import get_db_context

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# SIZE RANGES
# ============================================================

LINKEDIN_SIZE_RANGES = [
    (0,      10,           "1-10"),
    (11,     50,           "11-50"),
    (51,     200,          "51-200"),
    (201,    500,          "201-500"),
    (501,    1_000,        "501-1000"),
    (1_001,  5_000,        "1001-5000"),
    (5_001,  10_000,       "5001-10000"),
    (10_001, float('inf'), "10001+"),
]

VALID_SIZES = {r[2] for r in LINKEDIN_SIZE_RANGES}


def _find_size_range(num: int) -> Optional[str]:
    for low, high, label in LINKEDIN_SIZE_RANGES:
        if low <= num <= high:
            return label
    return None


def range_to_label(start, end) -> Optional[str]:
    if end is None or end == 0:
        return _find_size_range(max(int(start), 10001))
    return _find_size_range(int(start) if int(start) > 0 else 1)


def extract_company_slug(company_url: str) -> Optional[str]:
    if not company_url:
        return None
    m = re.search(r'/company/([^/?#]+)', str(company_url))
    return m.group(1).rstrip('/') if m else None


# ============================================================
# SCRAPER
# ============================================================

class EmployeeSizeScraper:

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/115.0',
    ]

    def __init__(
        self,
        li_at_cookie: str = None,
        cache_file: str = None,
        cache_days: int = 30,
        min_delay: float = 1.5,
        max_delay: float = 4.0,
        progress_file: str = None,
    ):
        self.li_at_cookie = li_at_cookie
        
        # ============================================================
        # 🔥 SETUP CACHE & PROGRESS DI FOLDER scraper/
        # ============================================================
        self.base_dir = Path(__file__).parent  # scraper/
        self.cache_dir = self.base_dir / 'cache'
        self.cache_dir.mkdir(exist_ok=True)  # Buat folder cache jika belum ada
        
        # Set default cache & progress files di dalam scraper/cache/
        if cache_file is None:
            cache_file = str(self.cache_dir / 'employee_size_cache.json')
        if progress_file is None:
            progress_file = str(self.cache_dir / 'scrape_progress.json')
        
        self.cache_file = cache_file
        self.cache_days = cache_days
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.progress_file = progress_file
        
        self._cache: Dict[str, dict] = {}
        self._column_names: Dict[str, str] = {}
        self._load_cache()
        self._load_progress()

    # ----------------------------------------------------------
    # PROGRESS TRACKING (Resume jika gagal)
    # ----------------------------------------------------------

    def _load_progress(self):
        """Load progress terakhir untuk resume."""
        self._progress = {}
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    self._progress = json.load(f)
                logger.info(f"Progress loaded: last_company={self._progress.get('last_company')}, "
                           f"done={self._progress.get('done', 0)}")
        except Exception:
            self._progress = {}

    def _save_progress(self, company: str, idx: int, total: int):
        """Simpan progress untuk resume."""
        try:
            self._progress = {
                'last_company': company,
                'done': idx,
                'total': total,
                'updated_at': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(self._progress, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save progress: {e}")

    def _clear_progress(self):
        """Hapus progress setelah selesai."""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
        except Exception:
            pass

    # ----------------------------------------------------------
    # CACHE
    # ----------------------------------------------------------

    def _load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    raw = json.load(f)
                now = datetime.now()
                valid = {}
                for k, v in raw.items():
                    try:
                        ts = datetime.fromisoformat(v.get('timestamp', ''))
                        size = v.get('size')
                        if (now - ts).days < self.cache_days and size in VALID_SIZES:
                            valid[k] = v
                    except Exception:
                        pass
                self._cache = valid
                logger.info(f"Cache loaded: {len(self._cache)} valid entries")
        except Exception as e:
            logger.warning(f"Cache load failed: {e}")
            self._cache = {}

    def _save_cache(self):
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self._cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Cache save failed: {e}")

    # ----------------------------------------------------------
    # DETEKSI NAMA KOLOM OTOMATIS
    # ----------------------------------------------------------

    def _get_column_names(self, db) -> dict:
        """Deteksi nama kolom yang tersedia di tabel jobs."""
        if self._column_names:
            return self._column_names

        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.bind)
            columns = inspector.get_columns('jobs')
            
            col_names = [col['name'].lower() for col in columns]
            
            # Mapping nama kolom yang mungkin
            self._column_names = {
                'id': 'id',
                'company': 'company',
                'job_url': None,
                'company_linkedin_url': None,
                'employee_size': 'employee_size',
            }
            
            # Cari kolom untuk URL job
            for possible in ['job_url', 'url', 'link', 'job_link', 'source_url']:
                if possible.lower() in col_names:
                    self._column_names['job_url'] = possible
                    break
            
            # Cari kolom untuk company LinkedIn URL
            for possible in ['company_linkedin_url', 'company_url', 'linkedin_url', 'company_link']:
                if possible.lower() in col_names:
                    self._column_names['company_linkedin_url'] = possible
                    break
            
            # Pastikan employee_size ada
            if 'employee_size' not in col_names:
                logger.warning("Kolom employee_size tidak ditemukan, akan dibuat otomatis")
                db.execute(text("ALTER TABLE jobs ADD COLUMN employee_size VARCHAR(20)"))
                db.commit()
                self._column_names['employee_size'] = 'employee_size'
            
            logger.info(f"✅ Detected columns: job_url={self._column_names['job_url']}, "
                       f"company_url={self._column_names['company_linkedin_url']}")
            
        except Exception as e:
            logger.warning(f"Column detection failed: {e}, using defaults")
            # Fallback: coba query langsung
            try:
                sample = db.execute(text("SELECT * FROM jobs LIMIT 1")).first()
                if sample:
                    keys = sample._mapping.keys()
                    for possible in ['job_url', 'url', 'link']:
                        if possible in keys:
                            self._column_names['job_url'] = possible
                            break
                    for possible in ['company_linkedin_url', 'company_url', 'linkedin_url']:
                        if possible in keys:
                            self._column_names['company_linkedin_url'] = possible
                            break
            except Exception as e2:
                logger.warning(f"Fallback failed: {e2}")
        
        return self._column_names

    # ----------------------------------------------------------
    # HTTP
    # ----------------------------------------------------------

    def _get(self, url: str, timeout: int = 20) -> Optional[requests.Response]:
        headers = {
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }
        if self.li_at_cookie:
            headers['Cookie'] = f'li_at={self.li_at_cookie}; lang=v2'

        try:
            resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            logger.debug(f"GET {url} → {resp.status_code}")
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429:
                logger.warning("Rate limited — tunggu 30 detik")
                time.sleep(30)
                return self._get(url, timeout)
            if resp.status_code == 999:
                logger.warning("Status 999 — LinkedIn blokir tanpa cookie")
            return None
        except Exception as e:
            logger.warning(f"GET error: {e}")
            return None

    def _sleep(self):
        time.sleep(random.uniform(self.min_delay, self.max_delay))

    # ----------------------------------------------------------
    # EKSTRAKSI DARI <code> TAGS
    # ----------------------------------------------------------

    def _extract_from_code_tags(self, html: str, target_slug: str) -> Optional[str]:
        soup = BeautifulSoup(html, 'html.parser')
        code_tags = soup.find_all('code')

        for code in code_tags:
            raw = code.get_text(strip=True)
            if not raw or 'employeeCountRange' not in raw:
                continue
            try:
                data = json.loads(raw)
            except Exception:
                continue

            included = data.get('included', [])
            if not isinstance(included, list):
                continue

            for item in included:
                if not isinstance(item, dict):
                    continue

                universal_name = item.get('universalName', '')
                entity_urn = item.get('entityUrn', '')

                is_target = (
                    universal_name.lower() == target_slug.lower() or
                    f'company/{target_slug.lower()}' in entity_urn.lower()
                )

                if not is_target:
                    continue

                logger.debug(f"  Match entity: {universal_name} / {entity_urn}")

                ecr = item.get('employeeCountRange')
                if isinstance(ecr, dict):
                    start = ecr.get('start')
                    end = ecr.get('end')
                    if start is not None:
                        result = range_to_label(start, end)
                        if result:
                            logger.info(f"  → employeeCountRange({start},{end}) → {result}")
                            return result

                ec = item.get('employeeCount')
                if ec is not None:
                    result = _find_size_range(int(ec))
                    if result:
                        logger.info(f"  → employeeCount={ec} → {result}")
                        return result

        return None

    # ----------------------------------------------------------
    # SCRAPE COMPANY PAGE
    # ----------------------------------------------------------

    def scrape_company_page(self, company_url: str) -> Optional[str]:
        if not company_url:
            return None
        if not self.li_at_cookie:
            logger.warning("  li_at tidak tersedia — company page butuh cookie")
            return None

        slug = extract_company_slug(company_url)
        if not slug:
            logger.warning(f"  Tidak bisa ekstrak slug dari: {company_url}")
            return None

        about_url = f"https://www.linkedin.com/company/{slug}/about/"
        logger.info(f"  Fetching: {about_url}")

        resp = self._get(about_url)
        if not resp:
            return None

        if 'authwall' in resp.url or '/login' in resp.url:
            logger.warning("  → authwall (li_at mungkin expired)")
            return None

        return self._extract_from_code_tags(resp.text, slug)

    # ----------------------------------------------------------
    # PUBLIC
    # ----------------------------------------------------------

    def get_employee_size(
        self,
        company_name: str,
        company_linkedin_url: str = None,
    ) -> Optional[str]:
        cache_key = (company_linkedin_url or company_name).lower().strip()

        if cache_key in self._cache:
            entry = self._cache[cache_key]
            size = entry.get('size')
            if size in VALID_SIZES:
                try:
                    ts = datetime.fromisoformat(entry.get('timestamp', ''))
                    if (datetime.now() - ts).days < self.cache_days:
                        logger.info(f"  Cache hit: {size}")
                        return size
                except Exception:
                    pass

        result = self.scrape_company_page(company_linkedin_url)
        self._sleep()

        if result in VALID_SIZES:
            self._cache[cache_key] = {
                'size': result,
                'company': company_name,
                'timestamp': datetime.now().isoformat(),
            }
            self._save_cache()

        return result

    # ----------------------------------------------------------
    # UPDATE DATABASE - OPTIMIZED (per company, bukan per job)
    # 🔥 MODIFIED: Added log_callback parameter with proper type hint
    # ----------------------------------------------------------

    def update_jobs(
        self, 
        limit: int = None, 
        skip_existing: bool = True, 
        resume: bool = True,
        log_callback: Optional[Callable[[str], None]] = None
    ):
        """
        Update employee_size untuk semua job di database.
        
        Args:
            limit: Batasi jumlah company yang diproses
            skip_existing: Skip company yang sudah punya size
            resume: Resume dari progress sebelumnya
            log_callback: Callback untuk streaming logs (opsional)
        """
        # Helper function untuk log
        def log(msg: str):
            if log_callback:
                log_callback(msg)
            else:
                print(msg)

        try:
            log("=" * 70)
            log("🏢 MENJALANKAN EMPLOYEE SIZE SCRAPER...")
            log("=" * 70)
            
            with get_db_context() as db:
                from sqlalchemy import text

                # Deteksi nama kolom otomatis
                cols = self._get_column_names(db)
                
                job_url_col = cols.get('job_url')
                company_url_col = cols.get('company_linkedin_url')
                
                if not job_url_col:
                    logger.error("❌ Tidak bisa menemukan kolom URL job di database!")
                    log("❌ Error: Kolom 'job_url' / 'url' / 'link' tidak ditemukan di tabel jobs")
                    log("   Pastikan tabel jobs memiliki kolom untuk menyimpan URL lowongan")
                    return

                valid_list = "','".join(VALID_SIZES)

                # 🔥 OPTIMASI: Ambil data UNIK per company (GROUP BY)
                query = f"""
                    SELECT 
                        MIN(id) as job_id,
                        company,
                        {company_url_col} as company_linkedin_url,
                        COUNT(*) as job_count,
                        employee_size
                    FROM jobs
                """

                if skip_existing:
                    query += (
                        f" WHERE employee_size IS NULL OR employee_size = '' "
                        f"OR employee_size NOT IN ('{valid_list}')"
                    )

                query += f"""
                    GROUP BY company, {company_url_col}, employee_size
                    ORDER BY job_count DESC
                """

                if limit:
                    query += f" LIMIT {limit}"

                logger.info(f"Executing query with columns: job_url={job_url_col}, company_url={company_url_col}")
                companies = db.execute(text(query)).fetchall()

                if not companies:
                    log("✅ Semua company sudah memiliki employee_size yang valid.")
                    return

                log(f"\n📊 Menemukan {len(companies)} perusahaan unik untuk diproses")
                log("=" * 70)

                # Resume dari progress terakhir
                start_idx = 0
                if resume and self._progress.get('done', 0) > 0:
                    last_company = self._progress.get('last_company')
                    if last_company:
                        for i, c in enumerate(companies):
                            if c[1] == last_company:  # c[1] adalah company name
                                start_idx = i + 1
                                break
                        if start_idx > 0:
                            log(f"🔄 Resume from index {start_idx}")

                updated_companies = 0
                updated_jobs = 0
                failed = 0
                failed_companies = []

                for idx, company_data in enumerate(companies[start_idx:], start=start_idx + 1):
                    # Extract data
                    try:
                        job_id = company_data[0]
                        company = company_data[1]
                        company_url = company_data[2]
                        job_count = company_data[3] if len(company_data) > 3 else 1
                        current_size = company_data[4] if len(company_data) > 4 else None
                    except Exception:
                        job_id = company_data.job_id
                        company = company_data.company
                        company_url = company_data.company_linkedin_url
                        job_count = company_data.job_count if hasattr(company_data, 'job_count') else 1

                    log(f"\n[{idx}/{len(companies)}] {company} ({job_count} jobs)")
                    log(f"  company_url  : {company_url}")
                    log(f"  current size : {current_size}")

                    try:
                        # 🔥 HANYA 1 REQUEST per COMPANY
                        size = self.get_employee_size(
                            company_name=company,
                            company_linkedin_url=company_url,
                        )

                        if size:
                            # 🔥 UPDATE SEMUA JOB dengan company yang SAMA
                            update_query = f"""
                                UPDATE jobs 
                                SET employee_size = :size 
                                WHERE company = :company 
                                  AND ({company_url_col} = :company_url OR ({company_url_col} IS NULL AND :company_url IS NULL))
                            """
                            result = db.execute(
                                text(update_query),
                                {"size": size, "company": company, "company_url": company_url}
                            )
                            updated_jobs += result.rowcount
                            updated_companies += 1
                            log(f"  ✅ {size} → Updated {result.rowcount} jobs")
                        else:
                            failed += 1
                            failed_companies.append(company)
                            log(f"  ❌ Tidak ditemukan")

                        # Commit setiap 10 company
                        if idx % 10 == 0:
                            db.commit()
                            self._save_progress(company, idx, len(companies))

                    except Exception as e:
                        failed += 1
                        failed_companies.append(company)
                        log(f"  ❌ Error: {e}")
                        logger.exception(f"Error company {company}")

                db.commit()
                self._clear_progress()

                log("\n" + "=" * 70)
                log("✅ EMPLOYEE SIZE SCRAPER SELESAI!")
                log(f"   • Perusahaan berhasil: {updated_companies}/{len(companies)}")
                log(f"   • Total jobs diupdate: {updated_jobs}")
                log(f"   • Gagal: {failed}")
                if failed_companies:
                    log(f"   • Gagal: {', '.join(failed_companies[:10])}")
                    if len(failed_companies) > 10:
                        log(f"     ... dan {len(failed_companies) - 10} lainnya")
                log("=" * 70)

        except Exception as e:
            logger.exception("update_jobs failed")
            log(f"[ERROR] {e}")

    # ----------------------------------------------------------
    # UPDATE SINGLE COMPANY (untuk testing)
    # ----------------------------------------------------------

    def update_single_company(self, company_name: str):
        """Update employee_size untuk satu perusahaan."""
        try:
            with get_db_context() as db:
                from sqlalchemy import text
                
                cols = self._get_column_names(db)
                company_url_col = cols.get('company_linkedin_url')
                
                # Cari perusahaan
                job = db.execute(
                    text(f"SELECT id, company, {company_url_col} as company_url, employee_size FROM jobs "
                         "WHERE company ILIKE :name LIMIT 1"),
                    {"name": f"%{company_name}%"}
                ).first()
                
                if not job:
                    print(f"❌ Tidak ditemukan: {company_name}")
                    return
                
                job_id, company, company_url, current_size = job
                print(f"\n🔍 {company} — {company_url}")
                print(f"   current size : {current_size}")
                
                # Scrape
                size = self.get_employee_size(company, company_url)
                
                if size:
                    # Update SEMUA job dengan company yang sama
                    update_query = f"""
                        UPDATE jobs 
                        SET employee_size = :size 
                        WHERE company = :company 
                          AND ({company_url_col} = :company_url OR ({company_url_col} IS NULL AND :company_url IS NULL))
                    """
                    result = db.execute(
                        text(update_query),
                        {"size": size, "company": company, "company_url": company_url}
                    )
                    db.commit()
                    print(f"✅ {size} → Updated {result.rowcount} jobs")
                else:
                    print(f"❌ Tidak ditemukan")
                    
        except Exception as e:
            print(f"[ERROR] {e}")
            logger.exception(f"Error updating {company_name}")

    # ----------------------------------------------------------
    # CLEANUP
    # ----------------------------------------------------------

    def cleanup_employee_sizes(self):
        try:
            with get_db_context() as db:
                from sqlalchemy import text
                valid_list = "','".join(VALID_SIZES)
                result = db.execute(text(
                    f"UPDATE jobs SET employee_size = NULL "
                    f"WHERE employee_size IS NOT NULL "
                    f"AND employee_size NOT IN ('{valid_list}')"
                ))
                db.commit()
                print(f"✅ Reset {result.rowcount} nilai tidak valid → NULL")
        except Exception as e:
            print(f"[ERROR] {e}")

    # ----------------------------------------------------------
    # STATISTICS
    # ----------------------------------------------------------

    def show_stats(self):
        """Tampilkan statistik employee_size di database."""
        try:
            with get_db_context() as db:
                from sqlalchemy import text
                result = db.execute(text("""
                    SELECT 
                        employee_size,
                        COUNT(*) as count,
                        COUNT(DISTINCT company) as companies
                    FROM jobs 
                    GROUP BY employee_size
                    ORDER BY count DESC
                """)).fetchall()
                
                print("\n📊 STATISTIK EMPLOYEE SIZE")
                print("=" * 60)
                total = sum(r[1] for r in result)
                print(f"  {'Size':15} | {'Jobs':>6} | {'Companies':>8} | {'%':>6}")
                print("-" * 60)
                for size, count, companies in result:
                    pct = (count / total * 100) if total > 0 else 0
                    display = size if size else "NULL"
                    print(f"  {display:15} | {count:>6} | {companies:>8} | {pct:>5.1f}%")
                print("=" * 60)
                print(f"  TOTAL: {total} jobs")
                
        except Exception as e:
            print(f"[ERROR] {e}")

    def close(self):
        pass


# ============================================================
# MAIN
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='LinkedIn Employee Size Scraper - Optimized Version',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  # Update semua company (dengan resume)
  python -m scraper.employee_size_scraper --li-at YOUR_COOKIE

  # Update 10 company saja (testing)
  python -m scraper.employee_size_scraper --li-at YOUR_COOKIE --limit 10

  # Force update (termasuk yang sudah ada)
  python -m scraper.employee_size_scraper --li-at YOUR_COOKIE --force

  # Update satu perusahaan
  python -m scraper.employee_size_scraper --li-at YOUR_COOKIE --single "Gojek"

  # Reset data invalid ke NULL
  python -m scraper.employee_size_scraper --li-at YOUR_COOKIE --cleanup

  # Cek statistik
  python -m scraper.employee_size_scraper --li-at YOUR_COOKIE --stats
        """
    )
    parser.add_argument('--limit',      type=int,  help='Batasi jumlah company yang diproses')
    parser.add_argument('--force',      action='store_true', help='Update semua (termasuk yang sudah punya size)')
    parser.add_argument('--cleanup',    action='store_true', help='Reset nilai tidak valid ke NULL')
    parser.add_argument('--stats',      action='store_true', help='Tampilkan statistik')
    parser.add_argument('--single',     type=str,  help='Update satu perusahaan saja')
    parser.add_argument('--no-resume',  action='store_true', help='Jangan resume dari progress sebelumnya')
    parser.add_argument('--li-at',      type=str,
                        default=os.environ.get('LINKEDIN_LI_AT'),
                        help='Cookie li_at LinkedIn (atau set env LINKEDIN_LI_AT)')
    args = parser.parse_args()

    if not args.li_at and not args.stats:
        print("⚠️  li_at cookie tidak diset!")
        print("   Gunakan: --li-at YOUR_COOKIE")
        print("   atau set env: set LINKEDIN_LI_AT=YOUR_COOKIE")
        print("   atau 'setx LINKEDIN_LI_AT YOUR_COOKIE' untuk permanen")
        return

    scraper = EmployeeSizeScraper(li_at_cookie=args.li_at)

    try:
        if args.cleanup:
            scraper.cleanup_employee_sizes()
        
        elif args.stats:
            scraper.show_stats()
        
        elif args.single:
            scraper.update_single_company(args.single)
        
        else:
            scraper.update_jobs(
                limit=args.limit, 
                skip_existing=not args.force,
                resume=not args.no_resume
            )

    except KeyboardInterrupt:
        print("\n⚠️ Proses dihentikan oleh user. Progress tersimpan.")
    except Exception as e:
        print(f"[ERROR] {e}")
        logger.exception("Main error")
    finally:
        scraper.close()


if __name__ == "__main__":
    main()