#!/usr/bin/env python3
"""
Company enrichment utility.

Workflow yang digunakan:
    1. Ambil company_linkedin_url dari tabel jobs (diekstrak saat scraping)
    2. Gunakan URL itu langsung untuk scrape employee size
    3. Fallback ke DuckDuckGo search + slug guessing HANYA jika URL tidak ada di DB

Tidak ada slug guessing dari nama perusahaan sebagai langkah utama.

Usage:
    python tools/enrich_company_profiles.py
    python tools/enrich_company_profiles.py --limit 50 --dry-run
    python tools/enrich_company_profiles.py --export-csv company_enrichment.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.parse import quote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from sqlalchemy import func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_context, init_db  # noqa: E402
from database.models import CompanyEnrichment, Job  # noqa: E402
from scraper.company.company_url import (  # noqa: E402
    build_company_slug_candidates,
    extract_linkedin_company_url,
    looks_like_company_match,
    slug_looks_like_company,
    slugify_company_name,
    split_company_name_variants,
    strip_company_suffixes,
)

load_dotenv()

try:
    from playwright.sync_api import sync_playwright
except Exception:
    sync_playwright = None


@dataclass
class EnrichedCompany:
    company_name: str
    employee_size: Optional[str] = None
    linkedin_slug: Optional[str] = None
    source: str = "linkedin_enrichment"


class CompanyEnricher:
    """
    Resolve LinkedIn company URLs dan employee sizes dari data job yang sudah ada.

    Urutan prioritas resolusi URL:
        1. company_linkedin_url dari tabel jobs  ← paling akurat, dari halaman job langsung
        2. URL dari parameter (jika dipanggil manual)
        3. Fallback: DuckDuckGo search + slug guessing  ← hanya jika 1 dan 2 tidak ada
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    SEARCH_URL = "https://html.duckduckgo.com/html/?q={query}"
    LINKEDIN_COMPANY_FALLBACK = "https://www.linkedin.com/company/{slug}/"
    BLOCKED_STATUS_CODES = {403, 429, 999}

    SIZE_TOKEN = r"(?:\d{1,3}(?:[\.,]\d{3})+|\d+(?:[\.,]\d+)?[kKmM]?)"
    RANGE_TOKEN = rf"{SIZE_TOKEN}(?:\s*[-–]\s*{SIZE_TOKEN})?\+?"

    LIMITED_PAGE_MARKERS = (
        "join linkedin",
        "sign in",
        "security verification",
        "let's do a quick security check",
        "challenge",
        "captcha",
    )

    EMPLOYEE_PATTERNS = [
        re.compile(
            rf"(?:ukuran perusahaan|company size|jumlah karyawan|number of employees|employee count|headcount)\s*[:\-]?\s*(?P<size>{RANGE_TOKEN})\s*(?:karyawan|employees?)?",
            re.I,
        ),
        re.compile(
            rf"(?P<size>{RANGE_TOKEN})\s*(?:karyawan|employees?)\s*(?:\[[^\]]*\]|\([^\)]*\))?",
            re.I,
        ),
        re.compile(rf"(?P<size>{RANGE_TOKEN})\s*(?:karyawan|employees?)", re.I),
        re.compile(r"company\s*size[:\s]+(?P<size>[^\n\r<]{2,100})", re.I),
    ]

    def __init__(
        self,
        pause_range: tuple[float, float] = (1.0, 2.5),
        allow_rendered_search: bool = True,
    ) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.USER_AGENT,
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
            }
        )
        self.pause_range = pause_range
        self.allow_rendered_search = allow_rendered_search

    # ------------------------------------------------------------------
    # Text helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_text(value: str) -> str:
        cleaned = (value or "").replace("\u2013", "-").replace("\u2014", "-").replace("\xa0", " ")
        return re.sub(r"\s+", " ", cleaned).strip()

    @classmethod
    def _is_limited_page_text(cls, text: str) -> bool:
        lowered = cls._normalize_text(text).lower()
        if not lowered:
            return True
        if any(marker in lowered for marker in cls.LIMITED_PAGE_MARKERS):
            return True
        if len(lowered) < 120 and "linkedin" in lowered:
            return True
        return False

    # ------------------------------------------------------------------
    # URL helpers
    # ------------------------------------------------------------------

    def _strip_suffixes(self, company_name: str) -> str:
        return strip_company_suffixes(company_name)

    @staticmethod
    def _slugify(value: str) -> str:
        return slugify_company_name(value)

    @staticmethod
    def _extract_linkedin_company_url(url: str) -> Optional[str]:
        return extract_linkedin_company_url(url)

    # ------------------------------------------------------------------
    # Prioritas 1: Ambil URL dari tabel jobs (paling akurat)
    # ------------------------------------------------------------------

    def resolve_company_url_from_db(
        self, company_name: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Ambil company_linkedin_url yang sudah tersimpan di tabel jobs.

        URL ini diekstrak langsung dari halaman /jobs/view/... saat scraping,
        sehingga dijamin valid dan tidak perlu di-guess.

        Returns:
            (company_linkedin_url, linkedin_slug) atau (None, None) jika tidak ada.
        """
        with get_db_context() as db:
            job = (
                db.query(Job)
                .filter(Job.company == company_name)
                .filter(Job.company_linkedin_url.isnot(None))
                .filter(Job.company_linkedin_url != "")
                .order_by(Job.id.desc())
                .first()
            )

            if job is None or not job.company_linkedin_url:
                return None, None

            url = self._extract_linkedin_company_url(job.company_linkedin_url)
            if not url:
                return None, None

            # Ekstrak slug: "https://www.linkedin.com/company/shopee/" → "shopee"
            slug = url.rstrip("/").split("/company/")[-1]
            return url, slug

    # ------------------------------------------------------------------
    # Prioritas 3: Fallback search (DuckDuckGo + slug guessing)
    # ------------------------------------------------------------------

    def _request_with_retry(
        self, url: str, timeout: int = 20, retries: int = 3
    ) -> Optional[requests.Response]:
        """Retry transient/blocked responses with adaptive backoff."""
        last_response: Optional[requests.Response] = None
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=timeout)
            except Exception:
                response = None

            if response is None:
                time.sleep(random.uniform(1.5, 2.5) * (attempt + 1))
                continue

            last_response = response
            if response.status_code not in self.BLOCKED_STATUS_CODES:
                return response

            if attempt < retries - 1:
                time.sleep(random.uniform(2.0, 4.0) * (attempt + 1))

        return last_response

    def search_company_url(
        self, company_name: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Fallback: cari LinkedIn company URL via DuckDuckGo + slug guessing.
        Hanya dipanggil jika company_linkedin_url tidak ada di tabel jobs.
        """
        candidates: list[tuple[Optional[str], Optional[str]]] = []
        seen_urls: set[str] = set()

        def add_candidate(candidate_url: Optional[str], slug: Optional[str]) -> None:
            canonical_url = self._extract_linkedin_company_url(candidate_url or "")
            if not canonical_url or canonical_url in seen_urls:
                return
            seen_urls.add(canonical_url)
            candidates.append((canonical_url, slug))

        query_variants: list[str] = []
        for variant in split_company_name_variants(company_name):
            cleaned_variant = self._strip_suffixes(variant)
            if cleaned_variant and cleaned_variant not in query_variants:
                query_variants.append(cleaned_variant)

        for cleaned in query_variants[:5]:
            query = quote_plus(f'site:linkedin.com/company "{cleaned}"')
            search_url = self.SEARCH_URL.format(query=query)
            try:
                response = self._request_with_retry(search_url, timeout=20, retries=2)
                if response and response.ok:
                    soup = BeautifulSoup(response.text, "html.parser")
                    for anchor in soup.select("a.result__a"):
                        href = anchor.get("href", "")
                        candidate = self._extract_linkedin_company_url(href)
                        if candidate:
                            slug = candidate.rstrip("/").split("/company/")[-1]
                            add_candidate(candidate, slug)

                    for anchor in soup.find_all("a", href=True):
                        candidate = self._extract_linkedin_company_url(anchor.get("href"))
                        if candidate:
                            slug = candidate.rstrip("/").split("/company/")[-1]
                            add_candidate(candidate, slug)
            except Exception:
                continue

        if self.allow_rendered_search:
            for cleaned in query_variants[:3]:
                rendered_candidates = self._search_linkedin_company_candidates_rendered(cleaned)
                for candidate_url, slug in rendered_candidates:
                    add_candidate(candidate_url, slug)

        slug_candidates = build_company_slug_candidates(company_name)
        for slug in slug_candidates:
            if slug:
                add_candidate(self.LINKEDIN_COMPANY_FALLBACK.format(slug=slug), slug)

        for candidate_url, slug in candidates:
            if candidate_url and self._is_valid_company_url(candidate_url, company_name):
                return candidate_url, slug

        return None, None

    def resolve_company_url(
        self,
        company_name: str,
        company_url: Optional[str] = None,
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Resolve company URL dari parameter eksplisit.
        Backward-compatible — digunakan jika caller punya URL sendiri.
        """
        if company_url:
            canonical_url = self._extract_linkedin_company_url(company_url)
            if canonical_url and self._is_valid_company_url(canonical_url, company_name):
                slug = canonical_url.rstrip("/").split("/company/")[-1]
                return canonical_url, slug

        return self.search_company_url(company_name)

    def _is_valid_company_url(self, company_url: str, company_name: str) -> bool:
        """Cek apakah LinkedIn URL mengarah ke halaman company yang benar."""
        if not company_url:
            return False

        try:
            response = self._request_with_retry(company_url, timeout=20, retries=3)
            if response is None:
                return False

            if response.status_code in self.BLOCKED_STATUS_CODES:
                return slug_looks_like_company(company_url, company_name)
            if response.status_code != 200:
                return False

            page_text = self._normalize_text(
                BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)
            )
            if self._is_limited_page_text(page_text):
                return slug_looks_like_company(company_url, company_name)
            return looks_like_company_match(company_url, company_name, page_text)
        except Exception:
            return False

    def _search_linkedin_company_candidates_rendered(
        self, company_name: str
    ) -> list[tuple[str, str]]:
        """Gunakan LinkedIn rendered search sebagai fallback URL source."""
        if sync_playwright is None:
            return []

        query = quote_plus(company_name)
        search_url = f"https://www.linkedin.com/search/results/companies/?keywords={query}"
        results: list[tuple[str, str]] = []

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=self.USER_AGENT,
                    locale="en-US",
                    viewport={"width": 1440, "height": 1600},
                )
                try:
                    page.goto(search_url, wait_until="networkidle", timeout=25000)
                    anchors = page.locator('a[href*="/company/"]').evaluate_all(
                        """
                        elements => elements.map((element) => ({
                            href: element.href || element.getAttribute('href') || '',
                            text: (element.innerText || element.textContent || '').trim(),
                        }))
                        """
                    )
                    for item in anchors:
                        href = item.get("href") or ""
                        candidate = self._extract_linkedin_company_url(href)
                        if candidate:
                            slug = candidate.rstrip("/").split("/company/")[-1]
                            results.append((candidate, slug))
                finally:
                    browser.close()
        except Exception:
            return []

        return results

    # ------------------------------------------------------------------
    # Employee size fetching
    # ------------------------------------------------------------------

    def fetch_employee_size(self, company_url: str) -> Optional[str]:
        """
        Fetch employee size dari halaman LinkedIn company.
        Mencoba halaman utama dan /about/ secara berurutan.
        """
        if not company_url:
            return None

        candidates = [company_url]
        if not company_url.rstrip("/").endswith("/about"):
            candidates.append(urljoin(company_url.rstrip("/") + "/", "about/"))

        for candidate in candidates:
            try:
                response = self._request_with_retry(candidate, timeout=20, retries=3)
                if not response or not response.ok:
                    continue

                soup = BeautifulSoup(response.text, "html.parser")
                page_text = self._normalize_text(soup.get_text(" ", strip=True))

                if self._is_limited_page_text(page_text):
                    continue

                # Coba JSON-LD structured data dulu
                try:
                    import json
                    for script in soup.find_all("script", type="application/ld+json"):
                        try:
                            data = json.loads(script.string or "{}")
                        except Exception:
                            continue

                        objs = [data] if isinstance(data, dict) else (data if isinstance(data, list) else [])
                        for obj in objs:
                            if not isinstance(obj, dict):
                                continue
                            for key in ("numberOfEmployees", "employees", "member", "memberCount"):
                                if key in obj:
                                    val = obj.get(key)
                                    if isinstance(val, (int, float)):
                                        return str(val)
                                    if isinstance(val, str) and val.strip():
                                        return self._normalize_text(val)
                except Exception:
                    pass

                # Fallback: regex pada teks halaman
                for pattern in self.EMPLOYEE_PATTERNS:
                    match = pattern.search(page_text)
                    if match:
                        size = self._normalize_text(match.group("size"))
                        size = re.sub(r"\s+employees?$", "", size, flags=re.I).strip()
                        return size or None

            except Exception:
                continue

        # Last resort: render dengan Playwright
        if self.allow_rendered_search:
            return self._fetch_employee_size_rendered(company_url)

        return None

    def _fetch_employee_size_rendered(self, company_url: str) -> Optional[str]:
        """Render halaman LinkedIn dengan headless browser saat static HTML kosong."""
        if sync_playwright is None:
            return None

        candidates = [company_url]
        if not company_url.rstrip("/").endswith("/about"):
            candidates.append(urljoin(company_url.rstrip("/") + "/", "about/"))

        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=self.USER_AGENT,
                    locale="en-US",
                    viewport={"width": 1440, "height": 1600},
                )
                try:
                    for candidate in candidates:
                        try:
                            page.goto(candidate, wait_until="networkidle", timeout=25000)
                            rendered_text = self._normalize_text(
                                page.locator("body").inner_text(timeout=10000)
                            )
                            if not rendered_text:
                                rendered_text = self._normalize_text(page.content())

                            if self._is_limited_page_text(rendered_text):
                                continue

                            for pattern in self.EMPLOYEE_PATTERNS:
                                match = pattern.search(rendered_text)
                                if match:
                                    size = self._normalize_text(match.group("size"))
                                    size = re.sub(r"\s+employees?$", "", size, flags=re.I).strip()
                                    if size:
                                        return size
                        except Exception:
                            continue
                finally:
                    browser.close()
        except Exception:
            return None

        return None

    # ------------------------------------------------------------------
    # Main enrichment entry point
    # ------------------------------------------------------------------

    def enrich_company(
        self, company_name: str, company_url: Optional[str] = None
    ) -> EnrichedCompany:
        """
        Enrich satu perusahaan dengan data LinkedIn.

        Urutan prioritas resolusi URL:
            1. company_linkedin_url dari tabel jobs  ← dari halaman job, paling akurat
            2. URL dari parameter company_url         ← jika dipanggil secara manual
            3. Fallback: DuckDuckGo search + slug guessing
        """
        resolved_url: Optional[str] = None
        slug: Optional[str] = None

        # Prioritas 1: URL dari tabel jobs
        resolved_url, slug = self.resolve_company_url_from_db(company_name)
        if resolved_url:
            print(f"    [DB] URL dari database: {resolved_url}")

        # Prioritas 2: URL dari parameter
        if not resolved_url and company_url:
            canonical = self._extract_linkedin_company_url(company_url)
            if canonical:
                resolved_url = canonical
                slug = canonical.rstrip("/").split("/company/")[-1]
                print(f"    [PARAM] URL dari parameter: {resolved_url}")

        # Prioritas 3: Fallback search
        if not resolved_url:
            print(f"    [SEARCH] Tidak ada URL di DB, fallback ke search...")
            resolved_url, slug = self.search_company_url(company_name)

        employee_size = self.fetch_employee_size(resolved_url) if resolved_url else None

        return EnrichedCompany(
            company_name=company_name,
            employee_size=employee_size,
            linkedin_slug=slug,
        )

    # ------------------------------------------------------------------
    # Database helpers
    # ------------------------------------------------------------------

    def get_unique_companies(self, limit: Optional[int] = None) -> list[str]:
        """Ambil daftar nama perusahaan unik dari tabel jobs, urut by job count desc."""
        with get_db_context() as db:
            query = (
                db.query(Job.company, func.count(Job.id).label("job_count"))
                .filter(Job.company.isnot(None))
                .filter(Job.company != "")
                .filter(Job.company != "N/A")
                .group_by(Job.company)
                .order_by(func.count(Job.id).desc(), Job.company.asc())
            )
            if limit:
                query = query.limit(limit)
            return [company for company, _count in query.all()]

    def save_result(self, item: EnrichedCompany) -> dict:
        """Upsert hasil enrichment ke tabel company_enrichment."""
        with get_db_context() as db:
            record = (
                db.query(CompanyEnrichment)
                .filter(CompanyEnrichment.company_name == item.company_name)
                .first()
            )

            if record is None:
                record = CompanyEnrichment(company_name=item.company_name)
                db.add(record)

            if item.employee_size:
                record.employee_size = item.employee_size
            record.linkedin_slug = item.linkedin_slug
            record.source = item.source
            db.commit()
            db.refresh(record)

            # Return dict untuk menghindari DetachedInstanceError di luar session
            return {
                "company_name": record.company_name,
                "company_url": record.company_url,
                "employee_size": record.employee_size,
                "linkedin_slug": record.linkedin_slug,
                "source": record.source,
                "id": record.id,
            }


# ------------------------------------------------------------------
# CSV export
# ------------------------------------------------------------------

def export_results_to_csv(
    records: Iterable[CompanyEnrichment], output_path: str
) -> None:
    fieldnames = ["company_name", "company_url", "employee_size", "linkedin_slug", "source"]
    with open(output_path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            writer.writerow(
                {
                    "company_name": record.company_name,
                    "company_url": record.company_url or "",
                    "employee_size": record.employee_size or "",
                    "linkedin_slug": record.linkedin_slug or "",
                    "source": record.source or "",
                }
            )


# ------------------------------------------------------------------
# CLI
# ------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Enrich company data from existing job records."
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit jumlah perusahaan unik yang diproses"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Jangan tulis ke database, hanya tampilkan hasil"
    )
    parser.add_argument(
        "--export-csv", default=None,
        help="Export tabel company_enrichment ke file CSV"
    )
    parser.add_argument(
        "--pause-min", type=float, default=1.0,
        help="Minimum jeda antar perusahaan (detik)"
    )
    parser.add_argument(
        "--pause-max", type=float, default=2.5,
        help="Maximum jeda antar perusahaan (detik)"
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    init_db()

    enricher = CompanyEnricher(pause_range=(args.pause_min, args.pause_max))
    company_names = enricher.get_unique_companies(limit=args.limit)

    if not company_names:
        print("Tidak ada nama perusahaan di tabel jobs.")
        return 0

    print(f"Ditemukan {len(company_names)} perusahaan unik untuk di-enrich")

    processed = 0
    saved = 0

    for index, company_name in enumerate(company_names, start=1):
        print(f"[{index}/{len(company_names)}] {company_name}")
        enriched = enricher.enrich_company(company_name)
        processed += 1

        if args.dry_run:
            print(
                f"    URL: {enriched.company_url or '-'} | "
                f"Employees: {enriched.employee_size or '-'}"
            )
        else:
            record = enricher.save_result(enriched)
            saved += 1
            print(
                f"    Saved → URL: {record.get('company_url') or '-'} | "
                f"Employees: {record.get('employee_size') or '-'}"
            )

        if index < len(company_names):
            time.sleep(random.uniform(args.pause_min, args.pause_max))

    if args.export_csv:
        with get_db_context() as db:
            records = (
                db.query(CompanyEnrichment)
                .order_by(CompanyEnrichment.company_name.asc())
                .all()
            )
        export_results_to_csv(records, args.export_csv)
        print(f"Exported {len(records)} records ke {args.export_csv}")

    print(
        f"Selesai. Processed={processed}, "
        f"Saved={saved if not args.dry_run else 0}, "
        f"Mode={'dry-run' if args.dry_run else 'write'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())