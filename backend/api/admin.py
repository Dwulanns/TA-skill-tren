"""
Admin API Endpoints - Scraping, Skill Extraction, Database Management

Endpoints untuk menjalankan proses scraping, ekstraksi skill, dan melihat database
dengan streaming real-time output untuk UI admin.

DATA SOURCES:
    ✅ Semua data diambil dari DATABASE (Keyword, Job, Skill, JobSkill, SkillType)
    ✅ Tidak ada hardcoded atau mock data
    ✅ DEMO_MODE = False → menggunakan real LinkedIn scraper
    ✅ Semua endpoint query database secara langsung

Usage:
    1. Start backend: python -m uvicorn api.main:app --reload --port 8000
    2. Verify data: python validate_all_data_sources.py
    3. Check browser DevTools > Network tab untuk lihat API responses
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
import sys
import os
import json
import asyncio
from typing import List, Optional
from contextlib import redirect_stdout, redirect_stderr
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_context
from database.models import Job, Skill, Keyword, SkillType, JobSkill, CompanyEnrichment
from scraper.main_scraper import LinkedInScraper
from llm.process_jobs import JobProcessor
from llm.process_monitor import ProcessMonitor
from tools.enrich_company_profiles import CompanyEnricher
from sqlalchemy import func

# Import utilities and schemas
from .admin_utils import OutputCapture, AdminState, KeywordValidator
from .schemas_admin import (
    KeywordRequest,
    KeywordResponse,
    KeywordListResponse,
    ScrapeRequest,
    SuccessResponse,
    ErrorResponse,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Global state untuk tracking progress
admin_state = AdminState()


async def stream_skill_extraction(triggered_by: str = "manual"):
    """Shared skill extraction stream for manual and auto-triggered flows."""
    if admin_state["extracting"]:
        raise HTTPException(status_code=409, detail="Ekstraksi skill sudah berjalan")

    if triggered_by != "scrape" and admin_state["scraping"]:
        raise HTTPException(status_code=409, detail="Scraping masih berjalan")

    admin_state["extracting"] = True
    admin_state["current_process"] = "extracting"
    admin_state["last_output"] = []

    monitor = ProcessMonitor()
    admin_state["extract_monitor"] = monitor

    try:
        header = "🔁 EKSTRAKSI SKILL OTOMATIS" if triggered_by == "scrape" else "🤖 MEMULAI EKSTRAKSI SKILL DARI LOWONGAN"
        yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': header})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"

        processor = JobProcessor()
        empty_jobs = processor.find_empty_jobs()
        yield f"data: {json.dumps({'type': 'log', 'message': f'📋 Jobs yang perlu ekstraksi: {len(empty_jobs)}'})}\n\n"

        if not empty_jobs:
            yield f"data: {json.dumps({'type': 'log', 'message': '✓ Semua job sudah memiliki skills'})}\n\n"
            yield f"data: {json.dumps({'type': 'success', 'message': 'Tidak ada pekerjaan baru'})}\n\n"
            return

        with get_db_context() as db:
            total_skills_before = db.query(Skill).count()
            total_job_skills_before = db.query(JobSkill).count()

        jobs_processed = 0
        jobs_with_errors = 0

        yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': 'Memproses job...'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '-' * 100})}\n\n"

        for idx, job_id in enumerate(empty_jobs, 1):
            item_id = f"job_{job_id}"

            with get_db_context() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                job_title = job.job_title if job else f"Job #{job_id}"

            monitor.start_item(item_id, f"Extract: {job_title}", job_title)

            yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': len(empty_jobs)})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': f'[{idx}/{len(empty_jobs)}] Processing: {job_title}'})}\n\n"

            try:
                start_time = time.time()
                success = processor.process_job_stable(job_id)
                duration = time.time() - start_time

                if not success:
                    raise RuntimeError("Ekstraksi gagal atau job masih pending")

                monitor.complete_item(item_id, duplicates=0)
                jobs_processed += 1

                yield f"data: {json.dumps({'type': 'log', 'message': f'  Success ({duration:.1f}s)'})}\n\n"

                if idx < len(empty_jobs):
                    time.sleep(3)

            except Exception as e:
                monitor.error_item(item_id, str(e))
                jobs_with_errors += 1
                yield f"data: {json.dumps({'type': 'error', 'message': f'  Error: {str(e)}'})}\n\n"

        with get_db_context() as db:
            total_skills_after = db.query(Skill).count()
            total_job_skills_after = db.query(JobSkill).count()

        summary = monitor.get_summary()
        new_skills = total_skills_after - total_skills_before
        new_relations = total_job_skills_after - total_job_skills_before
        elapsed_time = summary['timing']['elapsed_formatted']

        yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '✅ EKSTRAKSI SKILL SELESAI!'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'📊 RINGKASAN:'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'  • Jobs diproses: {jobs_processed}'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'  • Errors: {jobs_with_errors}'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'  • Skill baru ditambahkan: {new_skills}'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'  • Relasi job-skill baru: {new_relations}'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'  • Waktu total: {elapsed_time}'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'message': f'  • Total skill dalam database: {total_skills_after}'})}\n\n"
        yield f"data: {json.dumps({'type': 'success', 'message': 'Ekstraksi skill berhasil!'})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'message': f'❌ Error: {str(e)}'})}\n\n"
    finally:
        admin_state["extracting"] = False
        admin_state["current_process"] = None
        admin_state["extract_monitor"] = None


@router.get("/keywords", response_model=KeywordListResponse)
async def get_keywords():
    """
    Get all keywords for scraping
    
    Returns:
        List of all keywords with their IDs
        
    Raises:
        HTTPException: 500 if database error occurs
    """
    try:
        with get_db_context() as db:
            keywords = db.query(Keyword).all()
            return KeywordListResponse(
                keywords=[
                    KeywordResponse(id=kw.id, keyword=kw.keyword)
                    for kw in keywords
                ]
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/keywords", response_model=SuccessResponse)
async def add_keyword(request: KeywordRequest):
    """
    Add new keyword for scraping
    
    Args:
        request: Keyword data
        
    Returns:
        Success response with created keyword
        
    Raises:
        HTTPException: 400 if keyword already exists, 500 for database errors
    """
    try:
        # Validate keyword
        KeywordValidator.validate_keyword(request.keyword)
        normalized_keyword = KeywordValidator.normalize_keyword(request.keyword)
        
        with get_db_context() as db:
            # Check if keyword already exists (case-insensitive)
            existing = db.query(Keyword).filter(
                Keyword.keyword.ilike(normalized_keyword)
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Keyword '{normalized_keyword}' already exists"
                )
            
            # Create new keyword
            new_keyword = Keyword(keyword=normalized_keyword)
            db.add(new_keyword)
            db.commit()
            db.refresh(new_keyword)
            
            return SuccessResponse(
                message="Keyword added successfully",
                data={"id": new_keyword.id, "keyword": new_keyword.keyword}
            )
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.put("/keywords/{keyword_id}", response_model=SuccessResponse)
async def update_keyword(keyword_id: int, request: KeywordRequest):
    """
    Update existing keyword
    
    Args:
        keyword_id: ID of keyword to update
        request: New keyword data
        
    Returns:
        Success response with updated keyword
        
    Raises:
        HTTPException: 400 for validation error, 404 if not found, 500 for database errors
    """
    try:
        # Validate keyword
        KeywordValidator.validate_keyword(request.keyword)
        normalized_keyword = KeywordValidator.normalize_keyword(request.keyword)
        
        with get_db_context() as db:
            # Find keyword
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if not keyword:
                raise HTTPException(status_code=404, detail="Keyword not found")
            
            # Check if new keyword already exists (excluding current)
            existing = db.query(Keyword).filter(
                Keyword.keyword.ilike(normalized_keyword),
                Keyword.id != keyword_id
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Keyword '{normalized_keyword}' already exists"
                )
            
            # Update keyword
            keyword.keyword = normalized_keyword
            db.commit()
            db.refresh(keyword)
            
            return SuccessResponse(
                message="Keyword updated successfully",
                data={"id": keyword.id, "keyword": keyword.keyword}
            )
            
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.delete("/keywords/{keyword_id}", response_model=SuccessResponse)
async def delete_keyword(keyword_id: int):
    """
    Delete keyword
    
    Args:
        keyword_id: ID of keyword to delete
        
    Returns:
        Success response
        
    Raises:
        HTTPException: 404 if not found, 500 for database errors
    """
    try:
        with get_db_context() as db:
            keyword = db.query(Keyword).filter(Keyword.id == keyword_id).first()
            if not keyword:
                raise HTTPException(status_code=404, detail="Keyword not found")
            
            keyword_name = keyword.keyword
            db.delete(keyword)
            db.commit()
            
            return SuccessResponse(
                message=f"Keyword '{keyword_name}' deleted successfully"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/status")
async def get_admin_status():
    """Get current admin process status"""
    with get_db_context() as db:
        job_count = db.query(Job).count()
        skill_count = db.query(Skill).count()
        keyword_count = db.query(Keyword).count()
        job_skill_count = db.query(JobSkill).count()
    
    return {
        "status": "ok",
        "scraping": admin_state["scraping"],
        "extracting": admin_state["extracting"],
        "current_process": admin_state["current_process"],
        "database": {
            "jobs": job_count,
            "skills": skill_count,
            "keywords": keyword_count,
            "job_skills": job_skill_count,
        },
        "last_update": datetime.now().isoformat()
    }


@router.get("/process-progress")
async def get_process_progress():
    """Get detailed progress of current process"""
    current_process = admin_state["current_process"]
    
    if current_process == "scraping" and admin_state["scrape_monitor"]:
        monitor = admin_state["scrape_monitor"]
        return {
            "process_type": "scraping",
            "is_running": admin_state["scraping"],
            "summary": monitor.get_summary(),
            "recent_metrics": monitor.get_all_metrics()[-10:],  # Last 10 items
        }
    elif current_process == "extracting" and admin_state["extract_monitor"]:
        monitor = admin_state["extract_monitor"]
        return {
            "process_type": "extracting",
            "is_running": admin_state["extracting"],
            "summary": monitor.get_summary(),
            "recent_metrics": monitor.get_all_metrics()[-10:],  # Last 10 items
        }
    else:
        return {
            "process_type": None,
            "is_running": False,
            "summary": None,
            "recent_metrics": []
        }



@router.post("/scrape")
async def start_scraping(request: ScrapeRequest = None, background_tasks: BackgroundTasks = None):
    """Start web scraping process dengan process monitoring"""
    if admin_state["scraping"]:
        raise HTTPException(status_code=409, detail="Scraping sudah berjalan")
    
    # Handle both old (no parameter) and new (with ScrapeRequest) calls
    keyword_ids = request.keyword_ids if request else None
    
    async def scraping_generator():
        """Generator untuk streaming scraping output dengan detail monitoring"""
        admin_state["scraping"] = True
        admin_state["current_process"] = "scraping"
        admin_state["last_output"] = []
        
        # Initialize monitor
        monitor = ProcessMonitor()
        admin_state["scrape_monitor"] = monitor
        
        try:
            # First yield - signal start
            yield f"data: {json.dumps({'type': 'log', 'message': '🚀 MEMULAI SCRAPING LOWONGAN KERJA'})}\n\n"
            
            # Get keywords - wrapped in try/catch
            try:
                with get_db_context() as db:
                    if keyword_ids:
                        # Scrape only selected keywords
                        keywords = db.query(Keyword.id, Keyword.keyword).filter(Keyword.id.in_(keyword_ids)).all()
                        print(f"[DEBUG] Found {len(keywords)} selected keywords")
                    else:
                        # Scrape all keywords (backward compatibility)
                        keywords = db.query(Keyword.id, Keyword.keyword).all()
                        print(f"[DEBUG] Found {len(keywords)} keywords (no selection specified)")
            except Exception as e:
                error_msg = f"Error loading keywords: {str(e)}"
                print(f"[ERROR] {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            if not keywords:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Tidak ada keyword dalam database'})}\n\n"
                return
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'🔍 Memproses {len(keywords)} keyword(s)'})}\n\n"
            
            # Initialize scraper - wrapped in try/catch
            try:
                scraper = LinkedInScraper()
                print("[DEBUG] Scraper initialized")
            except Exception as e:
                error_msg = f"Error initializing scraper: {str(e)}"
                print(f"[ERROR] {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
                return
            
            with get_db_context() as db:
                jobs_before = db.query(Job).count()
            
            yield f"data: {json.dumps({'type': 'log', 'message': f'📊 Sebelum scraping: {jobs_before} lowongan'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': ''})}\n\n"  # Blank line for spacing
            
            # Process each keyword
            for idx, (keyword_id, keyword_text) in enumerate(keywords, 1):
                item_id = f"keyword_{keyword_id}"
                monitor.start_item(item_id, f"Scrape: {keyword_text}")
                
                yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': len(keywords)})}\n\n"
                
                try:
                    print(f"[DEBUG] About to scrape keyword: {keyword_text} (id={keyword_id})")
                    start_time = time.time()
                    jobs = scraper.scrape_keyword(keyword_text)
                    duration = time.time() - start_time
                    
                    print(f"[DEBUG] Scraping completed for '{keyword_text}', got {len(jobs) if jobs else 0} jobs")
                    
                    # Count duplicates
                    with get_db_context() as db:
                        existing = db.query(Job).filter(Job.keyword_id == keyword_id).count()
                    
                    print(f"[DEBUG] Existing jobs for keyword {keyword_text}: {existing}")
                    
                    monitor.complete_item(item_id, duplicates=existing)
                    
                    yield f"data: {json.dumps({'type': 'log', 'message': f'[{idx}/{len(keywords)}] ✓ {keyword_text}: {len(jobs)} job(s) | {duration:.1f}s'})}\n\n"
                    
                except Exception as e:
                    error_detail = str(e)[:100]  # Limit error message length
                    monitor.error_item(item_id, error_detail)
                    yield f"data: {json.dumps({'type': 'error', 'message': f'[{idx}/{len(keywords)}] ❌ {keyword_text}: {error_detail}'})}\n\n"
                    continue
                
                # Small delay between keywords
                if idx < len(keywords):
                    await asyncio.sleep(1)
            
            # Summary
            with get_db_context() as db:
                jobs_after = db.query(Job).count()
            
            summary = monitor.get_summary()
            total_completed = summary['progress']['completed']
            total_new = jobs_after - jobs_before
            total_dupes = summary['duplicates']['total']
            total_time = summary['timing']['elapsed_formatted']
            
            # Build comprehensive summary message
            summary_message = f"""📥 Total data diambil (raw): {len(keywords)} keyword(s) diproses
🔎 Cek duplikasi berdasarkan URL...

➕ Data baru (unique): {total_new} lowongan
🔁 Duplikat (tidak disimpan): {total_dupes} lowongan

📊 Sebelum scraping: {jobs_before} lowongan
📊 Setelah scraping: {jobs_after} lowongan

✅ Validasi:
{jobs_before} + {total_new} = {jobs_after} {'✔' if jobs_before + total_new == jobs_after else '❌'} ({'tidak ada duplikasi masuk' if jobs_before + total_new == jobs_after else 'ada masalah!'})

⏱️ Waktu: {total_time}"""
            
            yield f"data: {json.dumps({'type': 'log', 'message': summary_message})}\n\n"
            
            # --- RUN EMPLOYEE SIZE SCRAPING ---
            yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '🏢 MEMULAI PENGAMBILAN UKURAN PERUSAHAAN (EMPLOYEE SIZE) OTOMATIS'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'message': '=' * 100})}\n\n"
            
            try:
                from scraper.employee_size_scraper import EmployeeSizeScraper
                li_at = os.environ.get('LINKEDIN_LI_AT')
                emp_scraper = EmployeeSizeScraper(li_at_cookie=li_at)
                
                log_queue = asyncio.Queue()
                loop = asyncio.get_running_loop()
                
                def log_cb(msg):
                    loop.call_soon_threadsafe(log_queue.put_nowait, msg)
                
                # Jalankan di background executor agar event loop tidak terblokir
                task = loop.run_in_executor(
                    None,
                    lambda: emp_scraper.update_jobs(
                        limit=None,
                        skip_existing=True,
                        resume=True,
                        log_callback=log_cb
                    )
                )
                
                while not task.done() or not log_queue.empty():
                    try:
                        msg = await asyncio.wait_for(log_queue.get(), timeout=0.2)
                        yield f"data: {json.dumps({'type': 'log', 'message': msg})}\n\n"
                        log_queue.task_done()
                    except asyncio.TimeoutError:
                        continue
                        
                # Await task untuk raise exception jika ada error di dalamnya
                await task
                yield f"data: {json.dumps({'type': 'log', 'message': '✓ Selesai memproses employee size.'})}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'Gagal menjalankan employee size scraper: {str(e)}'})}\n\n"

            yield f"data: {json.dumps({'type': 'log', 'message': '🔄 Lanjut otomatis ke ekstraksi skill...'})}\n\n"

            async for chunk in stream_skill_extraction("scrape"):
                yield chunk

            yield f"data: {json.dumps({'type': 'success', 'message': 'Scraping berhasil!'})}\n\n"
            
        except Exception as e:
            error_detail = f"❌ Error: {str(e)}"
            print(f"[ERROR] {error_detail}")
            yield f"data: {json.dumps({'type': 'error', 'message': error_detail})}\n\n"
        finally:
            admin_state["scraping"] = False
            admin_state["current_process"] = None
            admin_state["scrape_monitor"] = None
    
    try:
        gen = scraping_generator()
        return StreamingResponse(gen, media_type="text/event-stream")
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[ERROR] Failed to start scraping generator: {str(e)}\n{tb}")
        raise HTTPException(status_code=500, detail=f"Failed to start scraping: {str(e)}")
@router.post("/extract-skills")
async def start_extraction():
    """Start skill extraction process dengan process monitoring"""
    return StreamingResponse(stream_skill_extraction("manual"), media_type="text/event-stream")


@router.get("/scraping-overview")
async def get_scraping_overview():
    """Get summary ringkas scraping dan ekstraksi per keyword."""
    with get_db_context() as db:
        keywords = db.query(Keyword).order_by(Keyword.keyword.asc()).all()
        rows = []

        for keyword in keywords:
            jobs = (
                db.query(Job)
                .filter(Job.keyword_id == keyword.id)
                .order_by(Job.created_at.desc())
                .all()
            )

            total_jobs = len(jobs)
            completed_jobs = sum(
                1
                for job in jobs
                if job.status_ekstraksi == "completed" or len(job.job_skills) > 0
            )
            pending_jobs = max(total_jobs - completed_jobs, 0)
            last_scraped_at = jobs[0].created_at.isoformat() if jobs and jobs[0].created_at else None
            latest_job_title = jobs[0].job_title if jobs else None
            extraction_rate = round((completed_jobs / total_jobs) * 100, 1) if total_jobs else 0

            rows.append(
                {
                    "keyword_id": keyword.id,
                    "job_title": keyword.keyword,
                    "last_scraped_at": last_scraped_at,
                    "total_jobs": total_jobs,
                    "completed_jobs": completed_jobs,
                    "pending_jobs": pending_jobs,
                    "extraction_rate": extraction_rate,
                    "latest_job_title": latest_job_title,
                }
            )

        return {
            "items": rows,
            "summary": {
                "total_keywords": len(keywords),
                "total_jobs": sum(item["total_jobs"] for item in rows),
                "total_completed": sum(item["completed_jobs"] for item in rows),
                "total_pending": sum(item["pending_jobs"] for item in rows),
            },
        }



@router.get("/database/overview")
async def get_database_overview():
    """Get overview of semua tabel"""
    with get_db_context() as db:
        keywords = db.query(Keyword).all()
        jobs_by_keyword = db.query(
            Keyword.keyword, 
            func.count(Job.id).label('count')
        ).outerjoin(Job).group_by(Keyword.keyword).all()
        
        skills_by_type = db.query(
            SkillType.name,
            func.count(Skill.id).label('count')
        ).outerjoin(Skill).group_by(SkillType.name).all()
        
        total_jobs = db.query(Job).count()
        total_skills = db.query(Skill).count()
        total_job_skills = db.query(JobSkill).count()
        total_keywords = db.query(Keyword).count()
    
    return {
        "summary": {
            "total_jobs": total_jobs,
            "total_skills": total_skills,
            "total_keywords": total_keywords,
            "total_job_skills": total_job_skills,
        },
        "jobs_by_keyword": [
            {"keyword": kw, "count": count} 
            for kw, count in jobs_by_keyword
        ],
        "skills_by_type": [
            {"type": st, "count": count}
            for st, count in skills_by_type
        ]
    }


@router.get("/database/keywords")
async def get_keywords():
    """Get all keywords"""
    with get_db_context() as db:
        keywords = db.query(Keyword).all()
        result = [{"id": k.id, "keyword": k.keyword} for k in keywords]
    return {"keywords": result}


@router.get("/database/jobs")
async def get_jobs(skip: int = 0, limit: int = 20):
    """Get jobs dengan pagination"""
    try:
        print(f"\n📝 Fetching jobs: skip={skip}, limit={limit}")
        
        with get_db_context() as db:
            # Check database state
            total = db.query(Job).count()
            print(f"✅ Total jobs in DB: {total}")
            
            # Query jobs
            jobs_list = db.query(Job).offset(skip).limit(limit).all()
            print(f"✅ Fetched {len(jobs_list)} jobs")
            
            result = []
            for idx, job in enumerate(jobs_list):
                print(f"  Processing job {idx+1}: {job.job_title}")
                try:
                    result.append({
                        "id": job.id,
                        "title": job.job_title,
                        "company": job.company,
                        "location": job.location or "",
                        "keyword": job.keyword.keyword if job.keyword else "N/A",
                        "posted_date": job.posted_date.isoformat() if job.posted_date else None,
                        "link": job.link
                    })
                except Exception as e:
                    print(f"    ❌ Error processing job: {e}")
            
            print(f"✅ Built result with {len(result)} items\n")
        
        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "jobs": result
        }
    except Exception as e:
        print(f"❌ Error fetching jobs: {e}")
        import traceback
        traceback.print_exc()
        return {
            "total": 0,
            "skip": skip,
            "limit": limit,
            "jobs": [],
            "error": str(e)
        }
    finally:
        db.close()


@router.get("/database/skills")
async def get_skills(skip: int = 0, limit: int = 20, skill_type: Optional[str] = None):
    """Get skills dengan pagination dan filter"""
    with get_db_context() as db:
        query = db.query(Skill)
        
        if skill_type:
            query = query.join(SkillType).filter(SkillType.name == skill_type)
        
        total = query.count()
        skills = query.offset(skip).limit(limit).all()
        
        result = []
        for skill in skills:
            job_count = db.query(JobSkill).filter(JobSkill.skill_id == skill.id).count()
            
            result.append({
                "id": skill.id,
                "name": skill.name,
                "normalized_name": skill.normalized_name,
                "type": skill.skill_type.name if skill.skill_type else "N/A",
                "job_count": job_count,
                "created_at": skill.created_at.isoformat()
            })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "skills": result
    }


@router.get("/database/skill-trends")
async def get_skill_trends():
    """Get top skills dan trend"""
    with get_db_context() as db:
        # Top 20 skills
        top_skills = db.query(
            Skill.name,
            SkillType.name.label('type'),
            func.count(JobSkill.skill_id).label('count')
        ).join(SkillType).join(JobSkill).group_by(
            Skill.id, Skill.name, SkillType.name
        ).order_by(func.count(JobSkill.skill_id).desc()).limit(20).all()
        
        # Skills per type
        by_type = db.query(
            SkillType.name,
            func.count(Skill.id)
        ).join(Skill).group_by(SkillType.name).all()
    
    return {
        "top_skills": [
            {"name": s[0], "type": s[1], "count": s[2]}
            for s in top_skills
        ],
        "by_type": [
            {"type": t[0], "count": t[1]}
            for t in by_type
        ]
    }


@router.get("/database/skill-types")
async def get_skill_types():
    """Get all skill types"""
    try:
        with get_db_context() as db:
            skill_types = db.query(SkillType).all()
            result = []
            for st in skill_types:
                skill_count = db.query(Skill).filter(Skill.skill_type_id == st.id).count()
                result.append({
                    "id": st.id,
                    "name": st.name,
                    "skill_count": skill_count
                })
            return {"skill_types": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database/job-analysis")
async def get_job_analysis(skip: int = 0, limit: int = 20):
    """Get job analysis data with pagination"""
    try:
        with get_db_context() as db:
            from database.models import JobAnalysis
            
            total = db.query(JobAnalysis).count()
            analyses = db.query(JobAnalysis).offset(skip).limit(limit).all()
            
            result = []
            for analysis in analyses:
                job = db.query(Job).filter(Job.id == analysis.job_id).first()
                result.append({
                    "id": analysis.id,
                    "job_id": analysis.job_id,
                    "job_title": analysis.job_title or (job.job_title if job else "N/A"),
                    "analysis_date": analysis.extracted_at.isoformat() if analysis.extracted_at else None,
                    "status": "completed"
                })
            
            return {
                "total": total,
                "skip": skip,
                "limit": limit,
                "analyses": result
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich-companies")
async def enrich_companies(limit: Optional[int] = Query(None, ge=1, le=1000), dry_run: bool = False):
    """Enrich distinct companies from existing jobs without rescraping jobs."""
    try:
        enricher = CompanyEnricher()

        # Select companies present in jobs but NOT yet in company_enrichment
        with get_db_context() as db:
            query = (
                db.query(Job.company, func.count(Job.id).label("job_count"))
                .outerjoin(CompanyEnrichment, CompanyEnrichment.company_name == Job.company)
                .filter(CompanyEnrichment.company_name.is_(None))
                .filter(Job.company.isnot(None))
                .filter(Job.company != "")
                .filter(Job.company != "N/A")
                .group_by(Job.company)
                .order_by(func.count(Job.id).desc(), Job.company.asc())
            )

            if limit:
                query = query.limit(limit)

            company_rows = query.all()

        company_names = [row[0] for row in company_rows]

        if not company_names:
            return {
                "processed": 0,
                "saved": 0,
                "dry_run": dry_run,
                "message": "Tidak ada company yang perlu enrichment (semua sudah ada)",
                "records": [],
            }

        records = []
        saved = 0

        for company_name in company_names:
            enriched = enricher.enrich_company(company_name)

            if not dry_run:
                enricher.save_result(enriched)
                saved += 1

            records.append(
                {
                    "company_name": enriched.company_name,
                    "company_url": enriched.company_url,
                    "employee_size": enriched.employee_size,
                    "linkedin_slug": enriched.linkedin_slug,
                }
            )

        return {
            "processed": len(company_names),
            "saved": saved,
            "dry_run": dry_run,
            "message": (
                "Dry-run selesai, tidak ada data yang disimpan"
                if dry_run
                else "Company enrichment selesai"
            ),
            "records": records,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Company enrichment error: {str(e)}")
