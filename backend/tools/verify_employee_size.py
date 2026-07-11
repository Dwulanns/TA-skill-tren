"""
Verify Company Size - Tool untuk memverifikasi dan memperbaiki employee size
===================================
Menemukan, memverifikasi, dan memperbaiki data employee size yang tidak akurat.

Fitur:
- Deteksi data yang mencurigakan (10,001+ untuk perusahaan kecil)
- Validasi dengan multiple sources (verified DB + LinkedIn fetch)
- Penjelasan detail kenapa data tidak bisa diambil
- Dry run mode untuk preview perubahan
- Manual input untuk data yang perlu verifikasi manual

Usage:
    python tools/verify_company_size.py --check              # Cek saja
    python tools/verify_company_size.py --fix                # Perbaiki otomatis
    python tools/verify_company_size.py --fix --limit 50
    python tools/verify_company_size.py --dry-run --fix      # Preview perubahan
    python tools/verify_company_size.py --manual             # Mode manual input
    python tools/verify_company_size.py --company "Shopee" --fix
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from datetime import datetime
from typing import Optional, Tuple, Dict, List

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

try:
    import requests
    from bs4 import BeautifulSoup
    from sqlalchemy import func
    from database.connection import get_db_context
    from database.models import Job
    REQUESTS_AVAILABLE = True
except ImportError as e:
    print(f"Error import: {e}")
    REQUESTS_AVAILABLE = False
    sys.exit(1)


# ──────────────────────────────────────────────────────────────────────────────
# VERIFIED CORRECT SIZES (Hasil verifikasi manual dari LinkedIn)
# ──────────────────────────────────────────────────────────────────────────────

VERIFIED_SIZES = {
    # ============ PERUSAHAAN BESAR (10,001+) ============
    "Zurich Insurance": "10,001+",
    "AIA Indonesia": "10,001+",
    "Prudential Indonesia": "10,001+",
    "Indosat Ooredoo Hutchison": "10,001+",
    "Telkom Indonesia": "10,001+",
    "Bank Mandiri": "10,001+",
    "Bank BCA": "10,001+",
    "Bank BRI": "10,001+",
    "Bank BNI": "10,001+",
    "Pertamina": "10,001+",
    "PLN": "10,001+",
    "Shopee": "5,001-10,000",  # Dari LinkedIn: 5,001-10,000
    "Tokopedia": "10,001+",
    "Gojek": "10,001+",
    "Grab": "10,001+",
    "Lazada": "10,001+",
    "Kraft Heinz": "10,001+",
    "Schneider Electric": "10,001+",
    "UOB": "10,001+",
    "Avanade": "10,001+",
    "PT Lion Super Indo": "10,001+",
    "NTT DATA, Inc.": "10,001+",
    "Accenture Southeast Asia": "10,001+",
    "Deloitte": "10,001+",
    "HSBC": "10,001+",
    "Aspen Medical": "10,001+",
    "TELUS Digital": "10,001+",
    "PT Chandra Asri Pacific Tbk": "10,001+",
    "PT Astra Otoparts Tbk": "10,001+",
    "PT Kalbe Farma Tbk": "10,001+",
    "PT Unilever Indonesia Tbk": "10,001+",
    "Home Credit Indonesia": "10,001+",
    
    # ============ PERUSAHAAN MENENGAH (1,001-5,000) ============
    "Eka Jaya Group": "1,001-5,000",
    "KB Bank": "1,001-5,000",
    "Güntner": "1,001-5,000",
    "Thamrin Group": "1,001-5,000",
    "Meratus Group": "1,001-5,000",
    "PT. Metrodata Electronics Tbk.": "1,001-5,000",
    "PT ABM Investama Tbk.": "1,001-5,000",
    "PT Gree Electric Appliances Indonesia": "1,001-5,000",
    "Anteraja": "1,001-5,000",
    "Akulaku Indonesia": "1,001-5,000",
    "PT Bank Neo Commerce Tbk": "1,001-5,000",
    "Halodoc": "1,001-5,000",
    "Amartha": "1,001-5,000",
    "PT Amman Mineral Nusa Tenggara": "1,001-5,000",
    "PT Link Net Tbk": "1,001-5,000",
    "QuantumBlack, AI by McKinsey": "1,001-5,000",
    
    # ============ PERUSAHAAN KECIL MENENGAH (501-1,000) ============
    "Kredit Pintar": "501-1,000",
    "Somethinc - BeautyHaul": "501-1,000",
    "Bibit.id": "501-1,000",
    "FinAccel": "501-1,000",
    "SKINTIFIC": "501-1,000",
    "Wego.com": "501-1,000",
    
    # ============ PERUSAHAAN KECIL (201-500) ============
    "CBI Credit Bureau Indonesia": "201-500",
    "PT ITSEC Asia Tbk": "201-500",
    "Funding Societies | Modalku Group": "201-500",
    "tiket.com": "201-500",
    "VLink Inc": "201-500",
    "Nityo Infotech Indonesia": "201-500",
    
    # ============ PERUSAHAAN KECIL (51-200) ============
    "mGanik Group - PT Mganik Grup Mitra Indonesia": "51-200",
    "VIDA Digital Identity": "51-200",
    "Krom": "51-200",
    "Solve Education!": "51-200",
    "Synapsis": "51-200",
    "iZeno": "51-200",
    "PT. CYBERTREND INTRABUANA": "51-200",
    "PT. Intikom Berlian Mustika": "51-200",
    "Erdigma Indonesia": "51-200",
    "株式会社SalesNow": "51-200",
    "Group Avows": "51-200",
    "Asiatek Solusi Indonesia": "51-200",
    "PT. Akhdani Reka Solusi": "51-200",
    "EDTS": "51-200",
    "Bumi Amartha Teknologi Mandiri": "51-200",
    "Intrepid Asia": "51-200",
    "WRS Health": "51-200",
    "Naluri - Employee Health & Wellness": "51-200",
    
    # ============ PERUSAHAAN KECIL (11-50) ============
    "ilmuOne Data": "11-50",
    "Alignerr": "11-50",
    "Cetta Online Class": "11-50",
    "Jobs Ai": "11-50",
    "Jalur Consulting": "11-50",
    "PT. Inovasi Anak Indonesia - PARKEE": "11-50",
    
    # ============ PERUSAHAAN SANGAT KECIL (1-10) ============
    "Gently": "1-10",
}


# ──────────────────────────────────────────────────────────────────────────────
# COMPANY SIZE FETCHER
# ──────────────────────────────────────────────────────────────────────────────

class CompanySizeFetcher:
    """Fetch company size dari LinkedIn dengan penjelasan error."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.session = self._create_session()
        self.cache = {}
    
    def _create_session(self):
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
        })
        return session
    
    def fetch_employee_size(self, company_url: str, company_name: str = None) -> Tuple[Optional[str], str]:
        """
        Fetch employee size dari LinkedIn company page.
        Returns: (size, message) - message berisi penjelasan jika gagal
        """
        if not company_url:
            return None, "❌ Tidak ada LinkedIn URL"
        
        # Check cache
        if company_url in self.cache:
            return self.cache[company_url], "✅ Dari cache"
        
        # Clean URL
        if not company_url.startswith("http"):
            company_url = "https://www.linkedin.com/company/" + company_url.lstrip("/")
        
        company_url = company_url.rstrip("/")
        
        try:
            # Coba /about/ page (paling lengkap)
            about_url = f"{company_url}/about/"
            if self.verbose:
                print(f"      🌐 Fetching: {about_url}")
            
            response = self.session.get(about_url, timeout=20)
            
            if response.status_code != 200:
                return None, f"❌ HTTP {response.status_code} - Halaman tidak ditemukan"
            
            # Cek redirect ke login/block
            if "authwall" in response.url:
                return None, "❌ Kena block LinkedIn (authwall) - perlu cookie/login"
            if "login" in response.url:
                return None, "❌ Redirect ke halaman login - perlu autentikasi"
            if "checkpoint" in response.url:
                return None, "❌ Kena checkpoint LinkedIn - perlu verifikasi"
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # ========== STRATEGI 1: Cari dt/dd dengan Ukuran perusahaan ==========
            size_labels = ["ukuran perusahaan", "company size", "规模", "公司规模"]
            
            for dt in soup.find_all("dt"):
                dt_text = dt.get_text(strip=True).lower()
                if any(label in dt_text for label in size_labels):
                    dd = dt.find_next_sibling("dd")
                    if dd:
                        size_text = dd.get_text(strip=True)
                        parsed = self._parse_size(size_text)
                        if parsed:
                            self.cache[company_url] = parsed
                            return parsed, f"✅ Dari halaman about: {size_text}"
            
            # ========== STRATEGI 2: Cari di full text ==========
            full_text = soup.get_text(" ", strip=True)
            
            patterns = [
                r'(\d{1,3}(?:[,.]\d{3})*)\s*[-–]\s*(\d{1,3}(?:[,.]\d{3})*)\s*(?:karyawan|employees?|人)',
                r'(\d+(?:rb)?)\s*[-–]\s*(\d+(?:rb)?)\s*(?:karyawan|employees?)',
                r'规模[：:]\s*(\d{1,3}(?:[,.]\d{3})*\s*[-–]\s*\d{1,3}(?:[,.]\d{3})*)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    size_text = match.group(0)
                    parsed = self._parse_size(size_text)
                    if parsed:
                        self.cache[company_url] = parsed
                        return parsed, f"✅ Dari text: {size_text}"
            
            # Tidak ditemukan
            return None, "❌ Tidak ditemukan informasi ukuran perusahaan di halaman LinkedIn"
            
        except requests.exceptions.Timeout:
            return None, "❌ Timeout - Koneksi lambat atau server tidak merespon"
        except requests.exceptions.ConnectionError:
            return None, "❌ Connection Error - Tidak bisa terhubung ke LinkedIn"
        except Exception as e:
            return None, f"❌ Error: {str(e)[:100]}"
    
    def _parse_size(self, text: str) -> Optional[str]:
        """Parse size text ke LinkedIn range."""
        if not text:
            return None
        
        text = text.lower().strip()
        
        # Handle rb format (Indonesia)
        if 'rb' in text:
            text = re.sub(r'(\d+)rb', lambda m: str(int(m.group(1)) * 1000), text)
        
        # Extract numbers
        numbers = re.findall(r'(\d{1,3}(?:[,.]\d{3})*|\d+)', text)
        if not numbers:
            return None
        
        nums = []
        for n in numbers:
            try:
                nums.append(int(n.replace(',', '').replace('.', '')))
            except:
                pass
        
        if not nums:
            return None
        
        n = max(nums)
        
        if n <= 10: return "1-10"
        if n <= 50: return "11-50"
        if n <= 200: return "51-200"
        if n <= 500: return "201-500"
        if n <= 1000: return "501-1,000"
        if n <= 5000: return "1,001-5,000"
        if n <= 10000: return "5,001-10,000"
        return "10,001+"


# ──────────────────────────────────────────────────────────────────────────────
# DATABASE OPERATIONS
# ──────────────────────────────────────────────────────────────────────────────

def get_suspicious_companies(limit: Optional[int] = None) -> List[Tuple[str, Optional[str], str, int, str]]:
    """
    Dapatkan company dengan data size yang mencurigakan.
    Returns: (company_name, linkedin_url, current_size, job_count, reason)
    """
    with get_db_context() as db:
        rows = (
            db.query(
                Job.company,
                Job.company_linkedin_url,
                Job.employee_size,
                func.count(Job.id).label("cnt")
            )
            .filter(
                Job.company.isnot(None),
                Job.company != "",
                Job.company != "N/A"
            )
            .group_by(Job.company, Job.company_linkedin_url, Job.employee_size)
            .all()
        )
    
    # Group by company
    company_data = {}
    for name, url, size, cnt in rows:
        if name not in company_data:
            company_data[name] = {"url": url, "size": size, "count": cnt}
        else:
            if cnt > company_data[name]["count"]:
                company_data[name]["size"] = size
                company_data[name]["count"] = cnt
            if url and not company_data[name]["url"]:
                company_data[name]["url"] = url
    
    # Filter suspicious companies
    suspicious = []
    for name, data in company_data.items():
        current_size = data["size"]
        url = data["url"]
        cnt = data["count"]
        
        # Skip if current size is None or empty
        if not current_size or current_size in ["N/A", ""]:
            continue
        
        # Check against verified sizes
        verified = VERIFIED_SIZES.get(name)
        if verified and verified != current_size:
            suspicious.append((name, url, current_size, cnt, f"Verified size: {verified}"))
        
        # Check suspicious 10,001+ for small companies
        elif current_size == "10,001+":
            # Check if this company is known to be large
            large_keywords = ["bank", "insurance", "telkom", "pertamina", "pln", 
                             "shopee", "tokopedia", "gojek", "grab", "lazada",
                             "indofood", "astra", "unilever", "kalbe", "schneider"]
            is_large = any(kw in name.lower() for kw in large_keywords)
            if not is_large:
                suspicious.append((name, url, current_size, cnt, "Size 10,001+ untuk perusahaan yang tidak dikenal besar"))
        
        # Check small sizes for companies that might be larger
        elif current_size in ["1-10", "11-50"] and len(name.split()) <= 3:
            suspicious.append((name, url, current_size, cnt, f"Size {current_size} mungkin terlalu kecil"))
    
    # Remove duplicates and sort
    seen = set()
    unique_suspicious = []
    for item in suspicious:
        if item[0] not in seen:
            seen.add(item[0])
            unique_suspicious.append(item)
    
    return unique_suspicious[:limit] if limit else unique_suspicious


def update_company_size(company_name: str, new_size: str, dry_run: bool = False) -> Tuple[int, str]:
    """Update semua jobs untuk company tertentu."""
    if dry_run:
        with get_db_context() as db:
            jobs = db.query(Job).filter(Job.company == company_name).all()
            return len(jobs), "DRY RUN - Tidak ada perubahan"
    
    with get_db_context() as db:
        jobs = db.query(Job).filter(Job.company == company_name).all()
        for job in jobs:
            old_size = job.employee_size
            job.employee_size = new_size
        db.commit()
        return len(jobs), f"✅ Updated {len(jobs)} jobs: {old_size} → {new_size}"


# ──────────────────────────────────────────────────────────────────────────────
# MAIN FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def verify_and_fix(limit: Optional[int] = None, fix: bool = False, dry_run: bool = False, verbose: bool = False):
    """Verifikasi dan perbaiki company size yang salah."""
    print("=" * 80)
    print("🔍 VERIFY COMPANY SIZE - Deteksi dan Perbaiki Data Employee Size")
    print("=" * 80)
    
    suspicious = get_suspicious_companies(limit)
    
    print(f"\n📊 Ditemukan {len(suspicious)} company dengan data mencurigakan")
    
    if fix:
        if dry_run:
            print(f"🔧 Mode: DRY RUN (hanya preview, tidak ada perubahan)")
        else:
            print(f"🔧 Mode: FIX (akan memperbaiki data yang salah)")
    else:
        print(f"🔧 Mode: CHECK ONLY (gunakan --fix untuk memperbaiki)")
    
    print("=" * 80)
    
    if not suspicious:
        print("\n✅ Tidak ada company dengan data mencurigakan!")
        return
    
    fetcher = CompanySizeFetcher(verbose=verbose)
    stats = {
        "fixed_from_verified": 0,
        "fixed_from_linkedin": 0,
        "skipped": 0,
        "failed": 0,
        "manual_needed": 0,
        "details": []
    }
    
    for idx, (name, url, current_size, job_count, reason) in enumerate(suspicious, 1):
        print(f"\n{'─'*80}")
        print(f"[{idx}/{len(suspicious)}] 📌 {name}")
        print(f"  ├─ Current size: {current_size} ({job_count} jobs)")
        print(f"  ├─ Issue: {reason}")
        print(f"  ├─ LinkedIn URL: {url if url else 'TIDAK ADA'}")
        
        # Strategy 1: Use verified size from database
        verified_size = VERIFIED_SIZES.get(name)
        if verified_size and verified_size != current_size:
            print(f"  ├─ ✅ Verified size: {verified_size}")
            
            if fix:
                updated, msg = update_company_size(name, verified_size, dry_run)
                print(f"  └─ 🔧 {msg}")
                stats["fixed_from_verified"] += 1
                stats["details"].append({
                    "name": name,
                    "from": current_size,
                    "to": verified_size,
                    "source": "verified_db"
                })
            else:
                print(f"  └─ 💡 Jalankan dengan --fix untuk memperbaiki")
                stats["skipped"] += 1
            continue
        
        # Strategy 2: Fetch from LinkedIn (only if fix=True)
        if fix and url:
            print(f"  ├─ 🌐 Mencoba fetch dari LinkedIn...")
            linkedin_size, message = fetcher.fetch_employee_size(url, name)
            
            if linkedin_size:
                print(f"  ├─ 📌 LinkedIn result: {linkedin_size}")
                print(f"  ├─ 📝 {message}")
                
                if linkedin_size != current_size:
                    updated, msg = update_company_size(name, linkedin_size, dry_run)
                    print(f"  └─ 🔧 {msg}")
                    stats["fixed_from_linkedin"] += 1
                    stats["details"].append({
                        "name": name,
                        "from": current_size,
                        "to": linkedin_size,
                        "source": "linkedin"
                    })
                else:
                    print(f"  └─ ✅ Size sudah sesuai")
                    stats["skipped"] += 1
            else:
                print(f"  └─ ❌ {message}")
                stats["failed"] += 1
                stats["details"].append({
                    "name": name,
                    "error": message
                })
        else:
            if not fix:
                print(f"  └─ 💡 Gunakan --fix untuk mencoba fetch dari LinkedIn")
            elif not url:
                print(f"  └─ ❌ Tidak ada LinkedIn URL")
            stats["manual_needed"] += 1
        
        # Delay to be polite
        if fix and idx < len(suspicious):
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"  Fixed from verified DB:  {stats['fixed_from_verified']}")
    print(f"  Fixed from LinkedIn:     {stats['fixed_from_linkedin']}")
    print(f"  Skipped (no fix):        {stats['skipped']}")
    print(f"  Failed (fetch error):    {stats['failed']}")
    print(f"  Need manual input:       {stats['manual_needed']}")
    
    if stats['details']:
        print("\n📋 DETAIL PERUBAHAN:")
        for d in stats['details'][:20]:
            if 'error' in d:
                print(f"  ❌ {d['name']}: {d['error']}")
            else:
                print(f"  ✅ {d['name']}: {d['from']} → {d['to']} ({d['source']})")
    
    if stats['manual_needed'] > 0 and fix:
        print("\n💡 Untuk company yang gagal, jalankan manual input:")
        print("   python tools/verify_company_size.py --manual")
    
    return stats


def manual_input_mode():
    """Mode manual input untuk company yang gagal auto-fetch."""
    print("=" * 80)
    print("📝 MANUAL INPUT MODE")
    print("=" * 80)
    print("Masukkan employee size yang benar untuk setiap company.")
    print("Format: 1-10, 11-50, 51-200, 201-500, 501-1,000, 1,001-5,000, 5,001-10,000, 10,001+")
    print("Ketik 'skip' untuk lewati, 'quit' untuk keluar")
    print("=" * 80)
    
    suspicious = get_suspicious_companies()
    
    # Filter yang perlu manual input (tidak ada verified size)
    to_review = [(name, url, size, cnt) for name, url, size, cnt, _ in suspicious 
                 if not VERIFIED_SIZES.get(name)]
    
    print(f"\n📋 Company perlu review manual: {len(to_review)}")
    
    if not to_review:
        print("✅ Semua company sudah memiliki verified size!")
        return
    
    with get_db_context() as db:
        for idx, (name, url, current_size, cnt) in enumerate(to_review, 1):
            print(f"\n{'─'*60}")
            print(f"[{idx}/{len(to_review)}] {name}")
            print(f"  Current size: {current_size} ({cnt} jobs)")
            print(f"  LinkedIn URL: {url if url else 'Tidak ada'}")
            
            # Suggestion based on company name
            suggestion = None
            name_lower = name.lower()
            if any(kw in name_lower for kw in ["bank", "insurance", "telkom"]):
                suggestion = "10,001+"
            elif any(kw in name_lower for kw in ["consulting", "solutions", "digital"]):
                suggestion = "51-200"
            elif any(kw in name_lower for kw in ["startup", "tech", "ai"]):
                suggestion = "11-50"
            
            if suggestion:
                print(f"  💡 Suggestion: {suggestion}")
            
            while True:
                new_size = input("  ✏️ Enter correct size: ").strip()
                
                if new_size.lower() == 'quit':
                    print("\n👋 Exiting...")
                    return
                if new_size.lower() == 'skip':
                    print(f"  ⏭ Skipped")
                    break
                
                valid_sizes = ["1-10", "11-50", "51-200", "201-500", "501-1,000", 
                              "1,001-5,000", "5,001-10,000", "10,001+"]
                
                if new_size in valid_sizes:
                    jobs = db.query(Job).filter(Job.company == name).all()
                    for job in jobs:
                        job.employee_size = new_size
                    db.commit()
                    print(f"  ✅ Updated {len(jobs)} jobs to {new_size}")
                    break
                else:
                    print(f"  ❌ Invalid format. Options: {', '.join(valid_sizes)}")
    
    print("\n✅ Manual update selesai!")


def fix_specific_company(company_name: str, fix: bool = False, dry_run: bool = False, verbose: bool = False):
    """Fix specific company by name."""
    print("=" * 80)
    print(f"🔧 FIX COMPANY: {company_name}")
    print("=" * 80)
    
    with get_db_context() as db:
        jobs = db.query(Job).filter(Job.company == company_name).all()
        if not jobs:
            print(f"❌ Company '{company_name}' tidak ditemukan di database")
            return
        
        current_size = jobs[0].employee_size
        url = jobs[0].company_linkedin_url
        job_count = len(jobs)
        
        print(f"  📝 Current size: {current_size} ({job_count} jobs)")
        print(f"  🔗 LinkedIn URL: {url if url else 'Tidak ada'}")
        
        # Check verified size
        verified_size = VERIFIED_SIZES.get(company_name)
        if verified_size:
            print(f"  ✅ Verified size: {verified_size}")
            if verified_size != current_size:
                print(f"  ⚠️ Mismatch: {current_size} vs {verified_size}")
                if fix:
                    if dry_run:
                        print(f"  🔧 [DRY RUN] Would update to {verified_size}")
                    else:
                        for job in jobs:
                            job.employee_size = verified_size
                        db.commit()
                        print(f"  ✅ Updated {job_count} jobs to {verified_size}")
                else:
                    print(f"  💡 Use --fix to apply")
            else:
                print(f"  ✅ Already correct")
            return
        
        # Fetch from LinkedIn
        if url and fix:
            fetcher = CompanySizeFetcher(verbose=verbose)
            linkedin_size, message = fetcher.fetch_employee_size(url, company_name)
            
            if linkedin_size:
                print(f"  📌 LinkedIn: {linkedin_size}")
                print(f"  📝 {message}")
                if linkedin_size != current_size:
                    if dry_run:
                        print(f"  🔧 [DRY RUN] Would update to {linkedin_size}")
                    else:
                        for job in jobs:
                            job.employee_size = linkedin_size
                        db.commit()
                        print(f"  ✅ Updated {job_count} jobs to {linkedin_size}")
                else:
                    print(f"  ✅ Already correct")
            else:
                print(f"  ❌ {message}")
                print(f"  💡 Use --manual for manual input")
        else:
            if not fix:
                print(f"  💡 Use --fix to fetch from LinkedIn")
            elif not url:
                print(f"  ❌ No LinkedIn URL available")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Verify and fix company employee sizes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/verify_company_size.py --check --limit 20
  python tools/verify_company_size.py --fix --limit 20
  python tools/verify_company_size.py --fix --dry-run --limit 20
  python tools/verify_company_size.py --manual
  python tools/verify_company_size.py --company "Shopee" --fix
        """
    )
    parser.add_argument("--check", action="store_true", help="Check only (default)")
    parser.add_argument("--fix", action="store_true", help="Auto-fix with verified data")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--manual", action="store_true", help="Manual input mode")
    parser.add_argument("--company", type=str, help="Fix specific company only")
    parser.add_argument("--limit", type=int, help="Limit number of companies")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args()
    
    if args.manual:
        manual_input_mode()
    elif args.company:
        fix_specific_company(args.company, fix=args.fix, dry_run=args.dry_run, verbose=args.verbose)
    elif args.fix:
        verify_and_fix(limit=args.limit, fix=True, dry_run=args.dry_run, verbose=args.verbose)
    else:
        verify_and_fix(limit=args.limit, fix=False, verbose=args.verbose)


if __name__ == "__main__":
    main()