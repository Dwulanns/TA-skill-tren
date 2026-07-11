"""
scraper/employee_size_fetcher.py
=================================
Shared module untuk mengambil employee_size dari berbagai sumber web.
Dipakai oleh:
  - LinkedInScraper (inline saat scraping)
  - main_scraper.py (Stage backfill untuk data lama)
  - tools/backfill_employee_size.py (standalone backfill)

Sumber (urutan prioritas):
    1. LinkedIn company page (via li_at cookie)
    2. RocketReach via DuckDuckGo
    3. Tracxn via DuckDuckGo
    4. Glassdoor via DuckDuckGo
    5. ZoomInfo via DuckDuckGo
    6. DuckDuckGo general search
    7. Wikipedia (en + id, dengan validasi ketat)
    8. Crunchbase

Output: selalu LinkedIn standard range
    1-10 | 11-50 | 51-200 | 201-500 | 501-1,000 |
    1,001-5,000 | 5,001-10,000 | 10,001+
"""
from __future__ import annotations

import os
import random
import re
import time
from typing import Optional
from urllib.parse import quote_plus

try:
    import requests
    from bs4 import BeautifulSoup
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

from dotenv import load_dotenv
load_dotenv()


# ──────────────────────────────────────────────────────────────────────────────
# LinkedIn standard ranges
# ──────────────────────────────────────────────────────────────────────────────

LINKEDIN_RANGES = [
    "1-10", "11-50", "51-200", "201-500", "501-1,000",
    "1,001-5,000", "5,001-10,000", "10,001+",
]

_SIZE_MAP = {
    r"^1[-–]10$":                      "1-10",
    r"^11[-–]50$":                     "11-50",
    r"^51[-–]200$":                    "51-200",
    r"^201[-–]500$":                   "201-500",
    r"^501[-–]1[,.]?000$":            "501-1,000",
    r"^1[,.]?001[-–]5[,.]?000$":      "1,001-5,000",
    r"^5[,.]?001[-–]10[,.]?000$":     "5,001-10,000",
    r"^10[,.]?001\+?$":               "10,001+",
    r"^1\s+to\s+10$":                 "1-10",
    r"^11\s+to\s+50$":                "11-50",
    r"^51\s+to\s+200$":               "51-200",
    r"^201\s+to\s+500$":              "201-500",
    r"^501\s+to\s+1[,.]?000$":        "501-1,000",
    r"^1[,.]?001\s+to\s+5[,.]?000$":  "1,001-5,000",
    r"^5[,.]?001\s+to\s+10[,.]?000$": "5,001-10,000",
    r"(?:under|less\s+than)\s*50\b":  "11-50",
    r"(?:under|less\s+than)\s*200\b": "51-200",
    r"^25[-–]100$":                   "11-50",
    r"^100[-–]500$":                  "201-500",
    r"^500[-–]1[,.]?000$":            "501-1,000",
    r"^1[,.]?000[-–]5[,.]?000$":      "1,001-5,000",
}

_N     = r"(?:\d{1,3}(?:[,\.]\d{3})*|\d+)"
_RANGE = rf"{_N}(?:\s*[-–]\s*{_N}|\+)"
_TO    = rf"{_N}\s+to\s+{_N}"

_RANGE_EMPLOYEES_RE = re.compile(
    rf"(?P<size>{_RANGE}|{_TO})\s*(?:employees?|karyawan|staff)\b",
    re.IGNORECASE,
)
_LABELED_SIZE_RE = re.compile(
    rf"(?:company\s*size|ukuran\s*perusahaan|number\s+of\s+employees?|employees?)"
    rf"[:\s]+(?P<size>{_RANGE}|{_TO}|{_N})",
    re.IGNORECASE,
)
_JSON_EMPLOYEES_RE = re.compile(
    rf'"(?:numberOfEmployees|employeeCount)"\s*[:"]+\s*(?P<size>{_RANGE}|{_N})',
    re.IGNORECASE,
)
_HAS_EMPLOYEES_RE = re.compile(
    rf"(?:has|employs|with|approximately|~|about)\s+(?P<size>{_N}[kKmM]?)\s+"
    rf"(?:total\s+)?(?:employees?|staff|karyawan)",
    re.IGNORECASE,
)
_TOTAL_EMPLOYEES_RE = re.compile(
    rf"(?P<size>{_N})\s+total\s+employees?",
    re.IGNORECASE,
)

_UA_POOL = [
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"),
    ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
     "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"),
    ("Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0"),
]

_WIKI_UA = "EmployeeSizeBackfill/2.5 (academic final project; python-requests)"

_LI_BLOCKED      = ["uas/login", "authwall", "signup", "checkpoint"]
_LI_DATA_SIGNALS = [
    "numberOfEmployees", "employeeCount",
    "company size", "employees on linkedin",
    '"@type":"organization"',
]


# ──────────────────────────────────────────────────────────────────────────────
# Normalisasi
# ──────────────────────────────────────────────────────────────────────────────

def normalize_to_linkedin(raw: str) -> Optional[str]:
    s = raw.strip()
    if s in LINKEDIN_RANGES:
        return s
    for pattern, result in _SIZE_MAP.items():
        if re.match(pattern, s, re.IGNORECASE):
            return result
    num_str = re.sub(r"[,\.]", "", re.sub(r"[^\d,\.]", "", s.replace("+", "")))
    if not num_str:
        return None
    try:
        n = int(num_str)
        if n == 0:     return None
        if n <= 10:    return "1-10"
        if n <= 50:    return "11-50"
        if n <= 200:   return "51-200"
        if n <= 500:   return "201-500"
        if n <= 1000:  return "501-1,000"
        if n <= 5000:  return "1,001-5,000"
        if n <= 10000: return "5,001-10,000"
        return "10,001+"
    except ValueError:
        return None


def parse_size_from_text(text: str) -> Optional[str]:
    for pat in [_RANGE_EMPLOYEES_RE, _LABELED_SIZE_RE,
                _TOTAL_EMPLOYEES_RE, _HAS_EMPLOYEES_RE, _JSON_EMPLOYEES_RE]:
        m = pat.search(text)
        if m:
            r = normalize_to_linkedin(m.group("size"))
            if r:
                return r
    return normalize_to_linkedin(text.strip())


def company_name_in_text(company_name: str, text: str, threshold: int = 2) -> bool:
    stopwords = {
        "the", "and", "of", "for", "in", "pt", "tbk", "cv", "ltd", "inc",
        "co", "group", "indonesia", "division", "noodle", "financial",
        "technologies", "technology", "consulting", "digital", "global",
        "solutions", "services", "network", "networks",
    }
    words = [w for w in re.findall(r"[a-zA-Z]{3,}", company_name.lower())
             if w not in stopwords]
    if not words:
        return True
    return sum(1 for w in words if w in text.lower()) >= min(threshold, len(words))


def _title_matches_company(title: str, company_name: str) -> bool:
    stopwords = {
        "the", "and", "of", "for", "in", "pt", "tbk", "cv", "ltd", "inc",
        "co", "group", "indonesia", "division", "noodle", "financial",
        "technologies", "technology", "consulting", "digital", "global",
        "solutions", "services", "network", "networks", "sistem", "teknik",
    }
    key_words = [w for w in re.findall(r"[a-zA-Z]{4,}", company_name.lower())
                 if w not in stopwords]
    if not key_words:
        return False
    return all(w in title.lower() for w in key_words)


# ──────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ──────────────────────────────────────────────────────────────────────────────

def _make_session() -> "requests.Session":
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(_UA_POOL),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
    })
    return s


def _safe_get(
    session: "requests.Session",
    url: str,
    timeout: int = 15,
    min_len: int = 300,
    extra_headers: Optional[dict] = None,
) -> "Optional[requests.Response]":
    try:
        headers = dict(session.headers)
        if extra_headers:
            headers.update(extra_headers)
        r = session.get(url, timeout=timeout, allow_redirects=True, headers=headers)
        if r.status_code == 200 and len(r.text) >= min_len:
            return r
    except Exception:
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Source 1: LinkedIn company page
# ──────────────────────────────────────────────────────────────────────────────

def _linkedin_has_real_data(text: str) -> bool:
    text_lower = text.lower()
    return any(s.lower() in text_lower for s in _LI_DATA_SIGNALS)


def fetch_from_linkedin_page(
    company_linkedin_url: str,
    session: "requests.Session",
) -> Optional[str]:
    """
    Ambil employee_size dari halaman LinkedIn company yang sudah diketahui URL-nya.
    Hanya parse structured/labeled data — TIDAK full-text fallback.
    """
    if not company_linkedin_url:
        return None

    li_at = os.getenv("LINKEDIN_LI_AT", "").strip()
    if not li_at:
        return None

    base = company_linkedin_url.rstrip("/")
    extra_headers = {
        "Cookie": f"li_at={li_at}",
        "User-Agent": random.choice(_UA_POOL),
        "Referer": "https://www.linkedin.com/feed/",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "same-origin",
    }

    for url in [f"{base}/about/", base + "/"]:
        try:
            r = session.get(url, timeout=20, allow_redirects=True,
                            headers={**dict(session.headers), **extra_headers})
            if r.status_code != 200:
                continue
            if any(p in r.url for p in _LI_BLOCKED) or len(r.text) < 2000:
                continue
            if not _linkedin_has_real_data(r.text):
                continue

            soup = BeautifulSoup(r.text, "html.parser")

            # 1) JSON-LD
            for script in soup.find_all("script", type="application/ld+json"):
                raw = script.get_text()
                for field in ["numberOfEmployees", "employeeCount"]:
                    m = re.search(
                        rf'"{field}"\s*:\s*(?:\{{[^}}]*\}}\s*,?\s*)?'
                        rf'"?(?P<val>[^",\}}]+)"?',
                        raw, re.IGNORECASE,
                    )
                    if m:
                        size = normalize_to_linkedin(m.group("val").strip())
                        if size:
                            return size

            # 2) Meta tag eksplisit employees
            for meta in soup.find_all("meta"):
                content = meta.get("content", "")
                if re.search(r"\bemployees?\b", content, re.I):
                    size = parse_size_from_text(content)
                    if size:
                        return size

            # 3) dt/dd "Company size"
            for dt in soup.find_all("dt"):
                if "company size" in dt.get_text(strip=True).lower():
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        size = parse_size_from_text(dd.get_text(" ", strip=True))
                        if size:
                            return size

            # 4) Span/li pendek dengan kata "employee"
            for el in soup.find_all(["span", "li"]):
                text = el.get_text(" ", strip=True)
                if (len(text) <= 50
                        and re.search(r"\bemployees?\b", text, re.I)
                        and re.search(r"\d", text)):
                    size = parse_size_from_text(text)
                    if size:
                        return size

        except Exception:
            continue

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Source 2-6: DDG-based sources
# ──────────────────────────────────────────────────────────────────────────────

def _ddg_search_size(
    company_name: str,
    session: "requests.Session",
    site_filter: str = "",
    extra_queries: Optional[list[str]] = None,
) -> Optional[str]:
    """Generic DDG search untuk employee size dengan optional site filter."""
    queries = extra_queries or []
    if site_filter:
        queries.insert(0, f'"{company_name}" employees site:{site_filter}')
    else:
        queries += [
            f'"{company_name}" "number of employees"',
            f"{company_name} company employees Indonesia",
            f"{company_name} jumlah karyawan",
        ]

    for query in queries:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        r = _safe_get(session, url, min_len=500)
        if not r:
            time.sleep(0.4)
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for result_div in soup.select(".result"):
            result_text = result_div.get_text(" ", strip=True)
            if site_filter and site_filter not in result_text.lower():
                continue
            snippet_el = result_div.select_one(".result__snippet")
            if not snippet_el:
                continue
            text = snippet_el.get_text(" ", strip=True)
            if company_name_in_text(company_name, text):
                size = parse_size_from_text(text)
                if size:
                    return size
        time.sleep(random.uniform(0.4, 0.9))
    return None


def fetch_from_rocketreach(company_name: str, session: "requests.Session") -> Optional[str]:
    return _ddg_search_size(
        company_name, session,
        site_filter="rocketreach.co",
        extra_queries=[f"{company_name} rocketreach employees Indonesia"],
    )


def fetch_from_tracxn(company_name: str, session: "requests.Session") -> Optional[str]:
    return _ddg_search_size(
        company_name, session,
        site_filter="tracxn.com",
    )


def fetch_from_glassdoor(company_name: str, session: "requests.Session") -> Optional[str]:
    return _ddg_search_size(
        company_name, session,
        site_filter="glassdoor.com",
        extra_queries=[f"{company_name} company size glassdoor Indonesia"],
    )


def fetch_from_zoominfo(company_name: str, session: "requests.Session") -> Optional[str]:
    return _ddg_search_size(
        company_name, session,
        site_filter="zoominfo.com",
    )


def fetch_from_ddg_general(company_name: str, session: "requests.Session") -> Optional[str]:
    return _ddg_search_size(company_name, session)


# ──────────────────────────────────────────────────────────────────────────────
# Source 7: Wikipedia
# ──────────────────────────────────────────────────────────────────────────────

def _wiki_get(session: "requests.Session", base_url: str, params: dict) -> Optional[dict]:
    try:
        r = session.get(base_url, params=params, timeout=12,
                        headers={**dict(session.headers), "User-Agent": _WIKI_UA})
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


def fetch_from_wikipedia(company_name: str, session: "requests.Session") -> Optional[str]:
    for lang in ("en", "id"):
        base = f"https://{lang}.wikipedia.org/w/api.php"
        data = _wiki_get(session, base, {
            "action": "query", "list": "search",
            "srsearch": company_name,
            "format": "json", "srlimit": 5, "srprop": "snippet",
        })
        if not data:
            continue
        results = data.get("query", {}).get("search", [])
        best = next(
            (r for r in results if _title_matches_company(r.get("title", ""), company_name)),
            None,
        )
        if not best:
            continue
        snippet = re.sub(r"<[^>]+>", "", best.get("snippet", ""))
        size = parse_size_from_text(snippet)
        if size:
            return size
        data2 = _wiki_get(session, base, {
            "action": "query", "prop": "revisions",
            "rvprop": "content", "titles": best.get("title", ""),
            "format": "json", "rvslots": "main", "rvsection": "0",
        })
        if not data2:
            continue
        for page in data2.get("query", {}).get("pages", {}).values():
            content = (page.get("revisions", [{}])[0]
                       .get("slots", {}).get("main", {}).get("*", ""))
            if not company_name_in_text(company_name, content, threshold=2):
                continue
            m = re.search(
                r"\|\s*(?:num_employees|employees|workforce"
                r"|jumlah_karyawan|number_of_employees)\s*=\s*(.+?)(?:\n|\|)",
                content,
            )
            if m:
                raw = re.sub(r"<[^>]+>|\[\[|\]\]|'''|''|\{\{[^}]+\}\}", "",
                             m.group(1)).strip()
                size = parse_size_from_text(raw) or normalize_to_linkedin(raw)
                if size:
                    return size
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Source 8: Crunchbase
# ──────────────────────────────────────────────────────────────────────────────

def fetch_from_crunchbase(company_name: str, session: "requests.Session") -> Optional[str]:
    slug = re.sub(r"[^a-z0-9]+", "-", company_name.lower()).strip("-")
    r = _safe_get(session, f"https://www.crunchbase.com/organization/{slug}", min_len=1000)
    if not r:
        return None
    soup = BeautifulSoup(r.text, "html.parser")
    for script in soup.find_all("script", type="application/ld+json"):
        size = parse_size_from_text(script.get_text())
        if size:
            return size
    full = soup.get_text(" ", strip=True)
    if company_name_in_text(company_name, full):
        return parse_size_from_text(full)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Main fetcher class — dipakai oleh scraper dan backfill
# ──────────────────────────────────────────────────────────────────────────────

class EmployeeSizeFetcher:
    """
    Fetches employee_size dari berbagai sumber secara berurutan.

    Usage:
        # Shared instance (reuse session antar job)
        fetcher = EmployeeSizeFetcher()

        # Dengan URL LinkedIn yang sudah diketahui (sumber paling akurat)
        size = fetcher.fetch(company_name="Kredivo", company_linkedin_url="https://...")

        # Tanpa URL (fallback ke DDG/Wikipedia/dll)
        size = fetcher.fetch(company_name="Kredivo Group")
    """

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self._session = _make_session() if _AVAILABLE else None

        # Cache: company_name → size (hindari request ulang dalam satu sesi)
        self._cache: dict[str, Optional[str]] = {}

    def _log(self, msg: str) -> None:
        if self.verbose:
            print(f"        [SIZE] {msg}")

    def fetch(
        self,
        company_name: str,
        company_linkedin_url: Optional[str] = None,
    ) -> Optional[str]:
        """
        Ambil employee_size dengan prioritas:
          1. Cache (company_name → size dari sesi ini)
          2. LinkedIn company page (jika URL tersedia)
          3. RocketReach → Tracxn → Glassdoor → ZoomInfo → DDG → Wikipedia → Crunchbase

        Args:
            company_name: Nama company (wajib)
            company_linkedin_url: URL LinkedIn company jika sudah diketahui

        Returns:
            LinkedIn standard range string atau None
        """
        if not _AVAILABLE or not self._session:
            return None

        # 1. Cache hit
        cache_key = company_name.strip().lower()
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            self._log(f"cache: {cached}")
            return cached

        sources: list[tuple[str, any]] = []

        # LinkedIn hanya jika URL tersedia
        if company_linkedin_url:
            sources.append((
                "LinkedIn",
                lambda u=company_linkedin_url: fetch_from_linkedin_page(u, self._session),
            ))

        sources += [
            ("RocketReach", lambda n=company_name: fetch_from_rocketreach(n, self._session)),
            ("Tracxn",      lambda n=company_name: fetch_from_tracxn(n, self._session)),
            ("Glassdoor",   lambda n=company_name: fetch_from_glassdoor(n, self._session)),
            ("ZoomInfo",    lambda n=company_name: fetch_from_zoominfo(n, self._session)),
            ("DDG",         lambda n=company_name: fetch_from_ddg_general(n, self._session)),
            ("Wikipedia",   lambda n=company_name: fetch_from_wikipedia(n, self._session)),
            ("Crunchbase",  lambda n=company_name: fetch_from_crunchbase(n, self._session)),
        ]

        for name, fn in sources:
            try:
                size = fn()
                if size:
                    self._log(f"✓ {name}: {size}")
                    self._cache[cache_key] = size
                    return size
                self._log(f"✗ {name}")
            except Exception as e:
                self._log(f"✗ {name} error: {e}")
            time.sleep(random.uniform(0.2, 0.5))

        self._cache[cache_key] = None
        return None

    def fetch_bulk(
        self,
        companies: list[tuple[str, Optional[str]]],
    ) -> dict[str, Optional[str]]:
        """
        Fetch employee_size untuk banyak company sekaligus.

        Args:
            companies: List of (company_name, company_linkedin_url_or_None)

        Returns:
            Dict {company_name: size_or_None}
        """
        results: dict[str, Optional[str]] = {}
        for company_name, linkedin_url in companies:
            results[company_name] = self.fetch(company_name, linkedin_url)
            time.sleep(random.uniform(0.3, 0.7))
        return results