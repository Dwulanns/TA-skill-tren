"""
LinkedIn Job Scraper - Enhanced with Company Size Fetching
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
from typing import Optional, Tuple
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.connection import get_db_context
from database.models import Job, Keyword
from scraper.company.company_url import extract_linkedin_company_url
from utils.job_title_normalizer import JobTitleNormalizer
from scraper.employee_size_scraper import EmployeeSizeScraper
from constants import (
    DEFAULT_USER_AGENT,
    SCRAPER_REQUEST_TIMEOUT,
    SCRAPER_RANDOM_DELAY_RANGE,
    DATA_AI_KEYWORDS
)

load_dotenv()


class LinkedInScraper:
    """
    LinkedIn job scraper dengan inline employee size fetching.
    Menggunakan session yang sama untuk semua request.
    """

    REQUEST_HEADERS = {
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }

    LINKEDIN_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    def __init__(self, location: str = "Indonesia"):
        self.location = location
        self.session = requests.Session()
        self.session.headers.update(self.REQUEST_HEADERS)
        self.job_normalizer = JobTitleNormalizer()
        self.existing_urls = set()
        self.seen_urls = set()
        self.db_keywords = []
        
        # Inisialisasi company size fetcher menggunakan EmployeeSizeScraper
        li_at = os.environ.get('LINKEDIN_LI_AT')
        self.size_fetcher = EmployeeSizeScraper(li_at_cookie=li_at)
        
        self._load_database_state()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------

    def _load_database_state(self) -> None:
        """Load existing URLs and keywords from database."""
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

    # ------------------------------------------------------------------
    # URL / search helpers
    # ------------------------------------------------------------------

    def _build_search_url(self, keyword: str, start: int = 0) -> str:
        params = f"keywords={quote_plus(keyword)}&location={quote_plus(self.location)}&start={start}"
        return f"{self.LINKEDIN_API_URL}?{params}"

    # ------------------------------------------------------------------
    # Filtering helpers
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Core scraping
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Job page detail fetching
    # ------------------------------------------------------------------

    def fetch_job_page_details(self, url: str) -> Tuple[str, str | None]:
        try:
            time.sleep(random.uniform(1, 2))
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                return "", None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract company LinkedIn URL
            company_linkedin_url: str | None = None
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                candidate = extract_linkedin_company_url(href)
                if candidate:
                    company_linkedin_url = candidate
                    break

            # Extract description
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

        except Exception:
            return "", None

    # ------------------------------------------------------------------
    # Database operations
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Main scraping entry point
    # ------------------------------------------------------------------

    def scrape_keyword(self, keyword_text: str) -> list:
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
            print(f"  [INFO] {existing_count} lowongan sudah ada untuk keyword ini")

        jobs = self.fetch_all_jobs(keyword_text, keyword_id)

        if not jobs:
            if existing_count > 0:
                print(f"  [OK] Semua {existing_count} lowongan sudah ada")
            else:
                print(f"  [OK] Tidak ada lowongan ditemukan")
            return []

        print(f"  Mengambil detail dan menyimpan {len(jobs)} lowongan...")
        saved_count = 0
        skipped_count = 0
        size_found_count = 0

        for i, job in enumerate(jobs, 1):
            # Fetch description and company URL
            description, company_linkedin_url = self.fetch_job_page_details(job['link'])

            job['job_description'] = description
            job['company_linkedin_url'] = company_linkedin_url

            # Fetch employee size INLINE menggunakan EmployeeSizeScraper
            employee_size = None
            if company_linkedin_url:
                employee_size = self.size_fetcher.get_employee_size(
                    job['company'],
                    company_linkedin_url
                )
                if employee_size:
                    size_found_count += 1

            job['employee_size'] = employee_size

            # Save to database
            if self.save_to_db(job):
                saved_count += 1
                print(f"    [OK] [{i}] {job['company']} | size: {employee_size or '-'}")
            else:
                skipped_count += 1

            if i % 10 == 0:
                print(f"    Progress: {i}/{len(jobs)} | Saved: {saved_count} | Size found: {size_found_count}")

        print(
            f"  [OK] Hasil: {len(jobs)} scraping → "
            f"{saved_count} saved, {skipped_count} skip, "
            f"{size_found_count} with employee_size"
        )
        return jobs


def main():
    scraper = LinkedInScraper()
    print("Mode Test - Scraping 'Data Scientist'")
    jobs = scraper.scrape_keyword("Data Scientist")
    print(f"\nTest selesai: {len(jobs)} lowongan ditemukan")


if __name__ == "__main__":
    main()