"""
LinkedIn Job Scraper - Enhanced with Employee Size from Job Page
OPTIMIZED VERSION: Scrape per company (1 request untuk semua job dari company yang sama)
DILENGKAPI: 
- Cek database dulu sebelum scraping employee size
- Update employee size yang kosong di database
- Cache memory untuk akses cepat
"""

import requests
from bs4 import BeautifulSoup
import time
import random
from datetime import datetime
from urllib.parse import quote_plus
import os
import sys
import re
import json
import logging
from typing import Optional, Tuple, Dict, List
from collections import defaultdict
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_context
from database.models import Job, Keyword
from scraper.company.company_url import extract_linkedin_company_url
from utils.job_title_normalizer import JobTitleNormalizer
from constants import (
    DEFAULT_USER_AGENT,
    SCRAPER_REQUEST_TIMEOUT,
    SCRAPER_RANDOM_DELAY_RANGE,
    DATA_AI_KEYWORDS
)

# 🔥 IMPORT EmployeeSizeScraper (sekarang satu folder)
try:
    from scraper.employee_size_scraper import EmployeeSizeScraper
    EMPLOYEE_SCRAPER_AVAILABLE = True
except ImportError:
    try:
        from .employee_size_scraper import EmployeeSizeScraper  # Import relatif
        EMPLOYEE_SCRAPER_AVAILABLE = True
    except ImportError:
        EMPLOYEE_SCRAPER_AVAILABLE = False
        print("[WARNING] EmployeeSizeScraper tidak ditemukan, fitur employee size dinonaktifkan")

load_dotenv()

# ============================================================
# EMPLOYEE SIZE CONFIG
# ============================================================

LINKEDIN_SIZE_RANGES = [
    (0, 10, "1-10"),
    (11, 50, "11-50"),
    (51, 200, "51-200"),
    (201, 500, "201-500"),
    (501, 1000, "501-1000"),
    (1001, 5000, "1001-5000"),
    (5001, 10000, "5001-10000"),
    (10001, float('inf'), "10001+"),
]

VALID_SIZES = {r[2] for r in LINKEDIN_SIZE_RANGES}


def find_size_range(num: int) -> Optional[str]:
    for low, high, label in LINKEDIN_SIZE_RANGES:
        if low <= num <= high:
            return label
    return None


def extract_company_slug(company_url: str) -> Optional[str]:
    if not company_url:
        return None
    m = re.search(r'/company/([^/?#]+)', str(company_url))
    return m.group(1).rstrip('/') if m else None


def range_to_label(start, end) -> Optional[str]:
    if end is None or end == 0:
        return find_size_range(max(int(start), 10001))
    return find_size_range(int(start) if int(start) > 0 else 1)


class LinkedInScraper:
    """
    LinkedIn job scraper with employee size fetched DIRECTLY from job page.
    OPTIMIZED: Per company scraping (1 request untuk semua job dari company yang sama)
    """

    REQUEST_HEADERS = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
    }

    LINKEDIN_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    def __init__(self, location: str = "Indonesia", li_at_cookie: str = None):
        self.location = location
        self.li_at_cookie = li_at_cookie or os.environ.get('LINKEDIN_LI_AT')
        self.session = requests.Session()
        self.session.headers.update(self.REQUEST_HEADERS)
        self.job_normalizer = JobTitleNormalizer()
        self.existing_urls = set()
        self.seen_urls = set()
        self.db_keywords = []
        
        # 🔥 INIT EmployeeSizeScraper (jika tersedia)
        self._employee_size_scraper = None
        if EMPLOYEE_SCRAPER_AVAILABLE and self.li_at_cookie:
            try:
                self._employee_size_scraper = EmployeeSizeScraper(li_at_cookie=self.li_at_cookie)
                print(f"[INFO] EmployeeSizeScraper initialized successfully")
            except Exception as e:
                print(f"[WARNING] Failed to initialize EmployeeSizeScraper: {e}")
        elif EMPLOYEE_SCRAPER_AVAILABLE and not self.li_at_cookie:
            print(f"[WARNING] li_at cookie not set - employee size scraping disabled")
        
        # ============================================================
        # 🔥 SETUP CACHE DI FOLDER scraper/cache/
        # ============================================================
        cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        
        self._size_cache_file = os.path.join(cache_dir, "employee_size_cache.json")
        self._progress_file = os.path.join(cache_dir, "scrape_progress.json")
        
        # Cache untuk employee size (memory)
        self._size_cache: Dict[str, str] = {}
        self._load_size_cache()
        
        # Progress tracking
        self._progress = {}
        self._load_progress()
        
        self._load_database_state()
        
        # Log cookie status
        if self.li_at_cookie:
            print(f"[INFO] li_at cookie: ✓ (length: {len(self.li_at_cookie)})")
        else:
            print(f"[WARNING] li_at cookie: ✗ (employee size scraping akan gagal)")

    # ============================================================
    # CACHE & PROGRESS
    # ============================================================

    def _load_size_cache(self):
        """Load employee size cache."""
        try:
            if os.path.exists(self._size_cache_file):
                with open(self._size_cache_file, 'r') as f:
                    raw = json.load(f)
                now = datetime.now()
                valid = {}
                for k, v in raw.items():
                    try:
                        ts = datetime.fromisoformat(v.get('timestamp', ''))
                        size = v.get('size')
                        if (now - ts).days < 30 and size in VALID_SIZES:
                            valid[k] = size
                    except Exception:
                        pass
                self._size_cache = valid
                print(f"[INFO] Loaded {len(self._size_cache)} employee size cache entries")
        except Exception:
            self._size_cache = {}

    def _save_size_cache(self):
        """Save employee size cache."""
        try:
            with open(self._size_cache_file, 'w') as f:
                json.dump(self._size_cache, f, indent=2)
        except Exception:
            pass

    def _load_progress(self):
        """Load progress untuk resume."""
        try:
            if os.path.exists(self._progress_file):
                with open(self._progress_file, 'r') as f:
                    self._progress = json.load(f)
        except Exception:
            self._progress = {}

    def _save_progress(self, company: str, idx: int, total: int):
        """Save progress."""
        try:
            self._progress = {
                'last_company': company,
                'done': idx,
                'total': total,
                'updated_at': datetime.now().isoformat()
            }
            with open(self._progress_file, 'w') as f:
                json.dump(self._progress, f, indent=2)
        except Exception:
            pass

    def _clear_progress(self):
        """Clear progress setelah selesai."""
        try:
            if os.path.exists(self._progress_file):
                os.remove(self._progress_file)
        except Exception:
            pass

    # ============================================================
    # INIT
    # ============================================================

    def _load_database_state(self) -> None:
        self._reload_existing_urls()
        self._reload_keywords()

    def _reload_existing_urls(self) -> None:
        try:
            with get_db_context() as db:
                all_jobs = db.query(Job.link).all()
                self.existing_urls = {job.link for job in all_jobs}
                print(f"[INFO] Loaded {len(self.existing_urls)} existing URLs")
        except Exception as e:
            print(f"[WARNING] Failed to load existing URLs: {e}")
            self.existing_urls = set()

    def _reload_keywords(self) -> None:
        try:
            with get_db_context() as db:
                all_keywords = db.query(Keyword).all()
                self.db_keywords = [{'id': kw.id, 'keyword': kw.keyword} for kw in all_keywords]
                print(f"[INFO] Loaded {len(self.db_keywords)} keywords")
        except Exception as e:
            print(f"[WARNING] Failed to load keywords: {e}")
            self.db_keywords = []

    def reload_existing_urls(self) -> None:
        self._reload_existing_urls()

    # ============================================================
    # URL / SEARCH HELPERS
    # ============================================================

    def _build_search_url(self, keyword: str, start: int = 0) -> str:
        params = f"keywords={quote_plus(keyword)}&location={quote_plus(self.location)}&start={start}"
        return f"{self.LINKEDIN_API_URL}?{params}"

    # ============================================================
    # FILTERING HELPERS
    # ============================================================

    def _is_data_ai_role(self, job_title: str) -> bool:
        if not job_title:
            return False
        title_lower = job_title.lower()
        has_data_ai_keyword = any(kw in title_lower for kw in DATA_AI_KEYWORDS)
        if not has_data_ai_keyword:
            return False
        non_tech_positions = [
            'accountant', 'auditor', 'sales', 'business development',
            'marketing manager', 'economist'
        ]
        return not any(pos in title_lower for pos in non_tech_positions)

    def _normalize_location(self, location: str) -> str:
        return location.strip() if location else "Indonesia"

    def is_data_ai_job(self, job_title: str) -> bool:
        return self._is_data_ai_role(job_title)

    # ============================================================
    # 🔥 EMPLOYEE SIZE - CEK DATABASE DULU
    # ============================================================

    def _get_employee_size_from_db(self, company_name: str) -> Optional[str]:
        """Cek employee size dari database terlebih dahulu"""
        try:
            with get_db_context() as db:
                from sqlalchemy import text
                result = db.execute(
                    text("""
                        SELECT employee_size 
                        FROM jobs 
                        WHERE company ILIKE :name 
                        AND employee_size IS NOT NULL 
                        AND employee_size != ''
                        LIMIT 1
                    """),
                    {"name": f"%{company_name}%"}
                ).first()
                
                if result and result[0]:
                    return result[0]
                return None
        except Exception as e:
            print(f"      [WARN] DB check failed: {e}")
            return None

    def _save_employee_size_to_db(self, company_name: str, size: str) -> int:
        """Update employee size untuk semua job dengan company yang sama"""
        try:
            with get_db_context() as db:
                from sqlalchemy import text
                result = db.execute(
                    text("""
                        UPDATE jobs 
                        SET employee_size = :size 
                        WHERE company ILIKE :name
                        AND (employee_size IS NULL OR employee_size = '' OR employee_size = '-')
                    """),
                    {"size": size, "name": f"%{company_name}%"}
                )
                db.commit()
                updated_count = result.rowcount
                if updated_count > 0:
                    print(f"      [DB SAVE] {company_name}: {size} → {updated_count} jobs updated")
                return updated_count
        except Exception as e:
            print(f"      [WARN] Failed to save to DB: {e}")
            return 0

    def _get_employee_size(self, company_name: str, company_linkedin_url: str = None) -> Optional[str]:
        """
        Get employee size - cek database dulu, baru scraping jika tidak ada
        PRIORITAS: Database → Cache → Scrape
        """
        cache_key = (company_linkedin_url or company_name).lower().strip()
        
        # 1️⃣ Cek memory cache dulu (paling cepat)
        if cache_key in self._size_cache:
            size = self._size_cache[cache_key]
            print(f"      [CACHE] {company_name}: {size}")
            return size
        
        # 2️⃣ Cek database
        db_size = self._get_employee_size_from_db(company_name)
        if db_size:
            # Simpan ke cache
            self._size_cache[cache_key] = db_size
            self._save_size_cache()
            print(f"      [DB] {company_name}: {db_size}")
            return db_size
        
        # 3️⃣ Jika tidak ada di database, scrape dari LinkedIn
        print(f"      [SCRAPE] {company_name} - not in DB, scraping...")
        
        if not self.li_at_cookie:
            print(f"      [WARN] No li_at cookie for {company_name}")
            return None
        
        if not company_linkedin_url:
            print(f"      [WARN] No LinkedIn URL for {company_name}")
            return None
        
        if self._employee_size_scraper is not None:
            try:
                size = self._employee_size_scraper.get_employee_size(company_name, company_linkedin_url)
                
                if size:
                    # Simpan ke cache
                    self._size_cache[cache_key] = size
                    self._save_size_cache()
                    
                    # Simpan ke database untuk digunakan nanti
                    self._save_employee_size_to_db(company_name, size)
                    
                    print(f"      ✅ {company_name}: {size}")
                    return size
                else:
                    print(f"      ❌ No size found for {company_name}")
                    return None
                    
            except Exception as e:
                print(f"      [ERROR] Employee size for {company_name}: {e}")
                return None
        else:
            print(f"      [ERROR] EmployeeSizeScraper not initialized")
            return None

    # ============================================================
    # CORE SCRAPING
    # ============================================================

    def fetch_all_jobs(self, keyword: str, keyword_id: int) -> list:
        jobs = []
        start = 0
        page = 1
        empty_pages = 0

        print(f"\n  Searching: '{keyword}'")
        print(f"  Location: {self.location}")

        while True:
            try:
                url = self._build_search_url(keyword, start)
                time.sleep(random.uniform(*SCRAPER_RANDOM_DELAY_RANGE))

                response = self.session.get(url, timeout=SCRAPER_REQUEST_TIMEOUT)
                if response.status_code != 200:
                    print(f"    Status code {response.status_code}")
                    break

                soup = BeautifulSoup(response.text, 'html.parser')
                cards = soup.find_all('li')

                if not cards or len(cards) < 2:
                    empty_pages += 1
                    if empty_pages >= 5:
                        print(f"    Tidak ada hasil lagi")
                        break
                    start += 25
                    page += 1
                    continue

                page_count = 0
                for card in cards:
                    job = self.parse_card(card, keyword, keyword_id)
                    if job:
                        jobs.append(job)
                        page_count += 1

                total = len(jobs)
                print(f"    Halaman {page}: +{page_count} lowongan (Total: {total})")

                if page_count > 0:
                    empty_pages = 0
                else:
                    empty_pages += 1
                    if empty_pages >= 5:
                        break

                start += 25
                page += 1

                if page % 10 == 0:
                    time.sleep(random.uniform(5, 8))

            except Exception as e:
                print(f"    Error: {e}")
                break

        return jobs

    def parse_card(self, card, keyword: str, keyword_id: int) -> dict | None:
        try:
            link = card.find('a', class_='base-card__full-link')
            if not link:
                return None

            url = link.get('href', '')
            if '/jobs/view/' not in url:
                return None

            match = re.search(r'/jobs/view/([^?]+)', url)
            if not match:
                return None

            job_view_part = match.group(1)
            id_match = re.search(r'(\d+)$', job_view_part)
            if not id_match:
                return None

            job_id = id_match.group(1)
            url = f"https://www.linkedin.com/jobs/view/{job_id}/"

            if url in self.existing_urls:
                return None
            if url in self.seen_urls:
                return None

            self.seen_urls.add(url)

            title_elem = card.find('h3', class_='base-search-card__title')
            job_title = title_elem.text.strip() if title_elem else ""

            if not job_title:
                return None

            cleaned_title = self.job_normalizer.clean_title(job_title)

            if not self.is_data_ai_job(cleaned_title):
                return None

            db_keywords = getattr(self, 'db_keywords', None)
            is_matched, kw_id, matched_keyword = self.job_normalizer.match_keyword(cleaned_title, db_keywords)
            keyword_id_to_use = kw_id if is_matched else keyword_id

            company_elem = card.find('h4', class_='base-search-card__subtitle')
            company = company_elem.text.strip() if company_elem else "N/A"

            location_elem = card.find('span', class_='job-search-card__location')
            raw_location = location_elem.text.strip() if location_elem else "Indonesia"
            location = self._normalize_location(raw_location)

            date_elem = card.find('time')
            posted_date = None
            if date_elem:
                date_str = date_elem.get('datetime', '')
                try:
                    posted_date = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                except Exception:
                    posted_date = datetime.now().date()
            else:
                posted_date = datetime.now().date()

            return {
                'keyword_id': keyword_id_to_use,
                'job_title': cleaned_title,
                'company': company,
                'location': location,
                'posted_date': posted_date,
                'source': 'linkedin',
                'link': url,
                'job_description': '',
                'company_linkedin_url': None,
                'employee_size': None,
            }
        except Exception:
            return None

    # ============================================================
    # FETCH JOB DETAILS
    # ============================================================

    def fetch_job_page_details(self, url: str) -> Tuple[str, Optional[str]]:
        """
        Ambil deskripsi job dan company LinkedIn URL.
        (Employee size diambil terpisah oleh _get_employee_size)
        """
        try:
            time.sleep(random.uniform(1, 2))
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                return "", None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ========== 1. COMPANY LINKEDIN URL ==========
            company_linkedin_url = None
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                candidate = extract_linkedin_company_url(href)
                if candidate:
                    company_linkedin_url = candidate
                    break

            # ========== 2. DESKRIPSI JOB ==========
            description_selectors = [
                ('div', 'show-more-less-html__markup'),
                ('div', 'description'),
                ('section', None),
                ('div', 'job-details-jobs-unified-top-card__job-insight'),
            ]

            description = ""
            for tag, cls in description_selectors:
                elem = (
                    soup.find(tag, class_=cls)
                    if cls
                    else soup.find(tag, {'id': 'description'})
                )
                if elem:
                    text = elem.get_text(separator='\n', strip=True)
                    if len(text) > 100:
                        description = text
                        break

            if not description:
                main_content = soup.find('main')
                if main_content:
                    description = main_content.get_text(separator='\n', strip=True)

            return description, company_linkedin_url

        except Exception as e:
            print(f"      Error fetching job details: {e}")
            return "", None

    # ============================================================
    # UPDATE MISSING EMPLOYEE SIZES
    # ============================================================

    def update_missing_employee_sizes(self, limit: int = None):
        """
        Update employee size yang kosong di database.
        Cek database dulu, jika ada langsung pakai, jika tidak scrape.
        """
        print("\n" + "=" * 70)
        print("🏢 UPDATE MISSING EMPLOYEE SIZES")
        print("=" * 70)
        
        with get_db_context() as db:
            from sqlalchemy import text
            
            # Cari company dengan employee_size kosong
            companies = db.execute(text("""
                SELECT DISTINCT 
                    company as name,
                    MIN(company_linkedin_url) as linkedin_url,
                    COUNT(*) as job_count
                FROM jobs 
                WHERE company IS NOT NULL AND company != ''
                AND (employee_size IS NULL OR employee_size = '' OR employee_size = '-')
                GROUP BY company
                ORDER BY job_count DESC
            """)).fetchall()
            
            if not companies:
                print("✅ Semua company sudah memiliki employee size!")
                return
            
            print(f"📊 Menemukan {len(companies)} perusahaan tanpa employee size")
            print("-" * 70)
            
            updated = 0
            failed = 0
            from_db = 0
            
            for idx, company in enumerate(companies, 1):
                name, linkedin_url, job_count = company
                
                print(f"\n[{idx}/{len(companies)}] {name} ({job_count} jobs)")
                
                # Cek database dulu
                db_size = self._get_employee_size_from_db(name)
                if db_size:
                    from_db += 1
                    print(f"  ✅ {db_size} (from DB)")
                    continue
                
                # Jika tidak ada, scrape
                size = self._get_employee_size(name, linkedin_url)
                
                if size:
                    updated += 1
                    print(f"  ✅ {size} (scraped)")
                else:
                    failed += 1
                    print(f"  ❌ Not found")
                
                if idx % 10 == 0:
                    print(f"\n  💾 Committed {idx} companies")
            
            print("\n" + "=" * 70)
            print("✅ UPDATE COMPLETE!")
            print(f"  • From database: {from_db}")
            print(f"  • Scraped: {updated}")
            print(f"  • Failed: {failed}")
            print("=" * 70)

    # ============================================================
    # DATABASE OPERATIONS
    # ============================================================

    def save_to_db(self, job_data: dict) -> bool:
        try:
            with get_db_context() as db:
                existing = db.query(Job).filter(Job.link == job_data['link']).first()
                if existing:
                    return False

                new_job = Job(**job_data)
                db.add(new_job)
                db.commit()

                self.existing_urls.add(job_data['link'])
                return True

        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                self.existing_urls.add(job_data['link'])
                return False
            print(f"    Error DB: {e}")
            return False

    # ============================================================
    # MAIN SCRAPING
    # ============================================================

    def scrape_keyword(self, keyword_text: str) -> list:
        """
        Scrape semua job untuk satu keyword.
        Employee size diambil per company dengan prioritas: Database → Cache → Scrape
        """
        self.reload_existing_urls()
        self.seen_urls.clear()

        with get_db_context() as db:
            keyword = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
            if not keyword:
                print(f"  Keyword '{keyword_text}' tidak ditemukan di database!")
                return []

            keyword_id = keyword.id
            existing_count = db.query(Job).filter(Job.keyword_id == keyword_id).count()

            all_keywords = db.query(Keyword).all()
            self.db_keywords = [{'id': kw.id, 'keyword': kw.keyword} for kw in all_keywords]

        if existing_count > 0:
            print(f"  [INFO] {existing_count} lowongan sudah ada di database untuk keyword ini")

        jobs = self.fetch_all_jobs(keyword_text, keyword_id)

        if not jobs:
            if existing_count > 0:
                print(f"  [OK] Semua {existing_count} lowongan sudah ada, tidak ada yang baru")
            else:
                print(f"  [OK] Tidak ada lowongan ditemukan")
            return []

        print(f"  Mengambil detail dan menyimpan {len(jobs)} lowongan...")
        saved_count = 0
        skipped_count = 0
        
        # Batch tracking per company
        company_jobs = defaultdict(list)
        company_urls = {}

        for job in jobs:
            company = job['company']
            company_jobs[company].append(job)
            
            # Ambil detail job (description dan company_linkedin_url)
            description, company_linkedin_url = self.fetch_job_page_details(job['link'])
            job['job_description'] = description
            job['company_linkedin_url'] = company_linkedin_url
            company_urls[company] = company_linkedin_url

        print(f"  📊 Found {len(company_jobs)} unique companies")
        print(f"  🔍 Fetching employee sizes (1 request per company)...")
        print("-" * 70)

        # PROSES PER COMPANY (1 request per company)
        size_found_count = 0
        size_from_db_count = 0
        company_list = list(company_jobs.items())
        
        # Resume dari progress
        start_idx = 0
        if self._progress.get('done', 0) > 0:
            last_company = self._progress.get('last_company')
            if last_company:
                for i, (comp, _) in enumerate(company_list):
                    if comp == last_company:
                        start_idx = i + 1
                        break
                if start_idx > 0:
                    print(f"  🔄 Resume from company index {start_idx}")

        for idx, (company, jobs_list) in enumerate(company_list[start_idx:], start=start_idx + 1):
            company_url = company_urls.get(company)
            
            # 🔥 Ambil employee size (dengan prioritas: DB → Cache → Scrape)
            employee_size = self._get_employee_size(company, company_url)
            
            if employee_size:
                # Cek apakah dari database atau hasil scrape
                cache_key = (company_url or company).lower().strip()
                if cache_key in self._size_cache:
                    size_found_count += 1
                else:
                    size_from_db_count += 1
            
            # Update semua job dari company ini
            for job in jobs_list:
                job['employee_size'] = employee_size
                if self.save_to_db(job):
                    saved_count += 1
            
            # Progress
            if idx % 10 == 0:
                self._save_progress(company, idx, len(company_list))
                print(f"    Progress: {idx}/{len(company_list)} companies | "
                      f"Saved: {saved_count} jobs | "
                      f"Size found: {size_found_count + size_from_db_count}")

        self._clear_progress()

        print("-" * 70)
        print(
            f"  [OK] Hasil: {len(jobs)} hasil scraping → "
            f"{saved_count} tersimpan, {skipped_count} skip, "
            f"{size_found_count + size_from_db_count} dengan employee_size "
            f"({size_from_db_count} from DB, {size_found_count} scraped)"
        )
        
        return jobs


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Job Scraper with Employee Size')
    parser.add_argument('--keyword', type=str, default='Data Analyst', help='Keyword to search')
    parser.add_argument('--update-missing', action='store_true', help='Update missing employee sizes')
    parser.add_argument('--limit', type=int, help='Limit companies to update')
    
    args = parser.parse_args()
    
    # Load li_at cookie dari .env
    li_at = os.environ.get('LINKEDIN_LI_AT')
    
    scraper = LinkedInScraper(li_at_cookie=li_at)
    
    if args.update_missing:
        print("\n🔄 Updating missing employee sizes...")
        scraper.update_missing_employee_sizes(limit=args.limit)
    else:
        print(f"Mode Test - Scraping '{args.keyword}'")
        print(f"li_at: {'✅' if li_at else '❌'}")
        jobs = scraper.scrape_keyword(args.keyword)
        print(f"\nTest selesai: {len(jobs)} lowongan ditemukan")
        
        # Tampilkan statistik employee size
        sizes = {}
        for job in jobs:
            size = job.get('employee_size')
            if size:
                sizes[size] = sizes.get(size, 0) + 1
        
        if sizes:
            print("\n📊 Employee Size Statistics:")
            for size, count in sorted(sizes.items()):
                print(f"  {size}: {count} jobs")


if __name__ == "__main__":
    main()