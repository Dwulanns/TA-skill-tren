#!/usr/bin/env python3
"""
Extract LinkedIn company URLs from all jobs in database.

This script attempts to extract company URLs from job posting pages,
using the new enhanced LinkedInCompanyURLExtractor.

Useful for:
1. Testing extraction on existing jobs
2. Filling in missing company_linkedin_url values
3. Comparing old vs new extraction methods
4. Gathering statistics on extraction success

Usage:
    python backend/tools/extract_company_urls_bulk.py
    python backend/tools/extract_company_urls_bulk.py --limit 50 --dry-run
    python backend/tools/extract_company_urls_bulk.py --jobs-without-url
    python backend/tools/extract_company_urls_bulk.py --export-results extraction_results.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import random
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_context, init_db
from database.models import Job
from scraper.company.linkedin_url_extractor import LinkedInCompanyURLExtractor
from scraper.company.company_url_validator import validate_company_url

load_dotenv()


@dataclass
class ExtractionResult:
    """Result of URL extraction for a job."""
    job_id: int
    job_url: str
    company_name: str
    extraction_strategy: str
    extraction_confidence: float
    extracted_url: Optional[str] = None
    existing_url: Optional[str] = None
    validation_result: Optional[bool] = None
    improvement: Optional[bool] = None  # True if new URL is better than old
    error: Optional[str] = None


class CompanyURLBulkExtractor:
    """Extract company URLs from job pages in bulk."""
    
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    
    def __init__(self, pause_range: tuple[float, float] = (0.5, 1.5)):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        self.pause_range = pause_range
    
    def get_jobs_to_process(
        self,
        limit: Optional[int] = None,
        only_without_url: bool = False,
    ) -> list[dict]:
        """Get jobs that need URL extraction."""
        with get_db_context() as db:
            query = db.query(Job)
            
            if only_without_url:
                query = query.filter(
                    (Job.company_linkedin_url.is_(None)) |
                    (Job.company_linkedin_url == "")
                )
            
            query = query.limit(limit) if limit else query
            jobs = query.all()
            
            # Convert to dict before session closes (avoid DetachedInstanceError)
            job_dicts = []
            for job in jobs:
                job_dicts.append({
                    'id': job.id,
                    'link': job.link,
                    'company': job.company,
                    'company_linkedin_url': job.company_linkedin_url,
                })
            
            return job_dicts
    
    def fetch_page(self, url: str, timeout: int = 15) -> Optional[str]:
        """Fetch job posting page."""
        try:
            response = self.session.get(url, timeout=timeout)
            if response.status_code != 200:
                return None
            return response.text
        except Exception as e:
            print(f"      Error fetching: {e}")
            return None
    
    def extract_url(self, job: dict) -> ExtractionResult:
        """Extract company URL from a single job."""
        result = ExtractionResult(
            job_id=job['id'],
            job_url=job['link'],
            company_name=job['company'],
            extraction_strategy="none",
            extraction_confidence=0.0,
            existing_url=job['company_linkedin_url'],
        )
        
        # Fetch page
        page_html = self.fetch_page(job['link'])
        if not page_html:
            result.error = "Failed to fetch page"
            return result
        
        try:
            # Use enhanced extractor
            extractor = LinkedInCompanyURLExtractor(page_html)
            extracted = extractor.extract()
            
            result.extraction_strategy = extracted.strategy
            result.extraction_confidence = extracted.confidence
            result.extracted_url = extracted.url
            
            # Validate extracted URL
            if extracted.url:
                validation = validate_company_url(
                    extracted.url,
                    job['company'],
                    fast_only=True,
                )
                result.validation_result = validation.is_valid
                
                # Check if it's an improvement over existing
                if job['company_linkedin_url']:
                    # If existing URL is different and new one validates better
                    if extracted.url != job['company_linkedin_url']:
                        result.improvement = validation.is_valid
                else:
                    # If no existing URL and new one validates, it's an improvement
                    result.improvement = validation.is_valid
            
            return result
            
        except Exception as e:
            result.error = str(e)
            return result
    
    def process_all(
        self,
        limit: Optional[int] = None,
        only_without_url: bool = False,
        dry_run: bool = False,
    ) -> list[ExtractionResult]:
        """Process all jobs and return results."""
        jobs = self.get_jobs_to_process(limit, only_without_url)
        
        if not jobs:
            print("No jobs to process.")
            return []
        
        print(f"Processing {len(jobs)} jobs...\n")
        
        results = []
        stats = {
            'total': len(jobs),
            'extracted': 0,
            'validated': 0,
            'improved': 0,
            'by_strategy': {},
        }
        
        for index, job in enumerate(jobs, start=1):
            print(f"[{index}/{len(jobs)}] {job['company']}")
            
            result = self.extract_url(job)
            results.append(result)
            
            # Update stats
            if result.extracted_url:
                stats['extracted'] += 1
                
                strategy = result.extraction_strategy
                if strategy not in stats['by_strategy']:
                    stats['by_strategy'][strategy] = {'total': 0, 'success': 0}
                stats['by_strategy'][strategy]['total'] += 1
                
                if result.validation_result:
                    stats['validated'] += 1
                    stats['by_strategy'][strategy]['success'] += 1
                    
                    if result.improvement:
                        stats['improved'] += 1
            
            # Print result
            if result.extracted_url:
                print(f"    Strategy: {result.extraction_strategy}")
                print(f"    Confidence: {result.extraction_confidence:.2f}")
                print(f"    URL: {result.extracted_url}")
                if result.validation_result is not None:
                    print(f"    Validation: {'✓' if result.validation_result else '✗'}")
                if result.improvement is not None:
                    if result.improvement:
                        print(f"    → Improvement over existing URL")
                    else:
                        print(f"    → Not better than existing URL")
            else:
                print(f"    No URL extracted" + (f" ({result.error})" if result.error else ""))
            
            # Save to DB if not dry-run and extracted
            if not dry_run and result.extracted_url:
                with get_db_context() as db:
                    job_record = db.query(Job).filter(Job.id == result.job_id).first()
                    if job_record:
                        old_url = job_record.company_linkedin_url
                        job_record.company_linkedin_url = result.extracted_url
                        db.commit()
                        
                        if old_url != result.extracted_url:
                            print(f"    Saved to database")
            
            # Pause between requests
            if index < len(jobs):
                pause = random.uniform(self.pause_range[0], self.pause_range[1])
                time.sleep(pause)
        
        # Print stats
        print("\n" + "="*60)
        print("EXTRACTION STATISTICS")
        print("="*60)
        print(f"Total jobs: {stats['total']}")
        print(f"URLs extracted: {stats['extracted']} ({100*stats['extracted']/stats['total']:.1f}%)")
        print(f"URLs validated: {stats['validated']} ({100*stats['validated']/max(1, stats['extracted']):.1f}%)")
        print(f"URLs improved (new > old): {stats['improved']}")
        
        if stats['by_strategy']:
            print("\nBy strategy:")
            for strategy, counts in sorted(stats['by_strategy'].items()):
                success_rate = 100 * counts['success'] / counts['total']
                print(f"  {strategy:20s}: {counts['success']:3d}/{counts['total']:3d} ({success_rate:5.1f}%)")
        
        return results


# ============================================================================
# CLI
# ============================================================================

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract LinkedIn company URLs from job posting pages."
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit jumlah jobs yang diproses"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Jangan tulis ke database, hanya tampilkan hasil"
    )
    parser.add_argument(
        "--jobs-without-url", action="store_true",
        help="Hanya proses jobs yang belum punya company_linkedin_url"
    )
    parser.add_argument(
        "--export-results", default=None,
        help="Export hasil ekstraksi ke file CSV"
    )
    parser.add_argument(
        "--pause-min", type=float, default=0.5,
        help="Minimum jeda antar request (detik)"
    )
    parser.add_argument(
        "--pause-max", type=float, default=1.5,
        help="Maximum jeda antar request (detik)"
    )
    return parser


def export_results_to_csv(results: list[ExtractionResult], output_path: str) -> None:
    """Export extraction results to CSV."""
    if not results:
        print("No results to export")
        return
    
    fieldnames = [f.name for f in results[0].__dataclass_fields__.values()]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(asdict(result))
    
    print(f"Exported {len(results)} results to {output_path}")


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()
    
    init_db()
    
    extractor = CompanyURLBulkExtractor(
        pause_range=(args.pause_min, args.pause_max)
    )
    
    results = extractor.process_all(
        limit=args.limit,
        only_without_url=args.jobs_without_url,
        dry_run=args.dry_run,
    )
    
    if args.export_results:
        export_results_to_csv(results, args.export_results)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
