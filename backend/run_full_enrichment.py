"""
SIMPLE INTEGRATED ENRICHMENT LAUNCHER
Menjalankan: Scrape → Extract URLs → Enrich Employee Size (SEKALI PERINTAH)

Contoh:
    cd backend
    python run_full_enrichment.py --keyword "data scientist" --limit 50
    python run_full_enrichment.py --keyword "backend engineer"
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and report status"""
    print(f"\n{'='*70}")
    print(f"PHASE: {description}")
    print(f"{'='*70}")
    print(f"Command: {cmd}\n")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
        if result.returncode != 0:
            print(f"⚠️  Command completed with exit code {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"❌ Error running command: {e}")
        return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="One-command integrated job enrichment pipeline"
    )
    parser.add_argument("--keyword", required=True, help="Job search keyword (e.g., 'data scientist')")
    parser.add_argument("--limit", type=int, default=50, help="Number of jobs to process")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't save")
    
    args = parser.parse_args()
    
    print(f"""
╔════════════════════════════════════════════════════════════════════╗
║         INTEGRATED JOB ENRICHMENT PIPELINE                         ║
║  Scrape → Extract LinkedIn URLs → Enrich Employee Size            ║
╚════════════════════════════════════════════════════════════════════╝

Keyword: {args.keyword}
Limit:   {args.limit} jobs
Mode:    {'DRY RUN' if args.dry_run else 'LIVE (will save to database)'}
""")
    
    backend_path = Path(__file__).parent
    
    # Build commands
    cmd_scrape = f'python {backend_path}/scraper/main_scraper.py --keyword "{args.keyword}" --limit {args.limit}'
    cmd_extract_urls = f'python {backend_path}/tools/extract_company_urls_bulk.py --jobs-without-url --pause-min 1.0 --pause-max 2.0'
    cmd_enrich_sizes = f'python {backend_path}/tools/enrich_company_profiles.py'
    cmd_check_progress = f'python {backend_path}/check_employee_size_progress.py'
    
    if args.dry_run:
        cmd_extract_urls += " --dry-run"
        cmd_enrich_sizes += " --dry-run"
    
    # Execute phases
    phases = [
        (cmd_scrape, "1️⃣  SCRAPING JOB POSTINGS"),
        (cmd_extract_urls, "2️⃣  EXTRACTING LINKEDIN COMPANY URLs"),
        (cmd_enrich_sizes, "3️⃣  ENRICHING EMPLOYEE SIZE"),
        (cmd_check_progress, "4️⃣  VERIFICATION & SUMMARY"),
    ]
    
    results = []
    for cmd, description in phases:
        success = run_command(cmd, description)
        results.append((description, success))
        
        if not success:
            print(f"\n⚠️  Phase failed. Continuing with next phase...")
        
        time.sleep(2)  # Brief pause between phases
    
    # Final summary
    print(f"\n{'='*70}")
    print("PIPELINE SUMMARY")
    print(f"{'='*70}\n")
    
    for phase, success in results:
        status = "✅ SUCCESS" if success else "⚠️  WARNING"
        print(f"{status}: {phase}")
    
    print(f"\n{'='*70}")
    print("Pipeline execution completed!")
    print(f"Check database: All job data is now in 'jobs' table")
    print(f"  - job_title: Position name")
    print(f"  - company: Company name")
    print(f"  - company_linkedin_url: LinkedIn company URL")
    print(f"  - employee_size: Company employee count")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
