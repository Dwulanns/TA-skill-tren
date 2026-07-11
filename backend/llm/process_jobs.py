"""
Process Jobs - Ekstraksi skill dari job descriptions menggunakan AI
"""

import sys
import os
import threading
import time
import random
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# ============================================================
# 🔥 FIX: SETUP PATH DENGAN BENAR
# ============================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(backend_dir)

sys.path.insert(0, current_dir)
sys.path.insert(0, backend_dir)
sys.path.insert(0, project_root)

print(f"[DEBUG] Current dir: {current_dir}")
print(f"[DEBUG] Backend dir: {backend_dir}")
print(f"[DEBUG] Project root: {project_root}")

# ============================================================
# 🔥 IMPORT SKILL_EXTRACTOR & SKILL_DEDUP_NORMALIZED
# ============================================================

SkillExtractor = None
SkillNormalizationConfig = None

# Strategy 1: Import from llm folder (absolute)
try:
    from llm.skill_extractor import SkillExtractor as ImportedSkillExtractor
    SkillExtractor = ImportedSkillExtractor
    print("[OK] Imported SkillExtractor from llm")
except ImportError as e:
    print(f"[WARN] Failed from llm: {e}")

# Strategy 2: Import from current folder
if SkillExtractor is None:
    try:
        from .skill_extractor import SkillExtractor as ImportedSkillExtractor
        SkillExtractor = ImportedSkillExtractor
        print("[OK] Imported SkillExtractor from current folder")
    except ImportError as e:
        print(f"[WARN] Failed from .: {e}")

# Strategy 3: Import without prefix
if SkillExtractor is None:
    try:
        from skill_extractor import SkillExtractor as ImportedSkillExtractor
        SkillExtractor = ImportedSkillExtractor
        print("[OK] Imported SkillExtractor without prefix")
    except ImportError as e:
        print(f"[WARN] Failed without prefix: {e}")

# Strategy 4: Direct file loading
if SkillExtractor is None:
    try:
        import importlib.util
        skill_file = os.path.join(current_dir, 'skill_extractor.py')
        if os.path.exists(skill_file):
            spec = importlib.util.spec_from_file_location("skill_extractor", skill_file)
            skill_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(skill_module)
            SkillExtractor = skill_module.SkillExtractor
            print("[OK] Loaded SkillExtractor from file")
    except Exception as e:
        print(f"[ERROR] Failed via file path: {e}")

# ============================================================
# 🔥 IMPORT SKILL_PROCESSOR DARI SKILL_DEDUP_NORMALIZED
# ============================================================

SkillProcessor = None
SkillMatchEngine = None
SkillMatchResult = None
SkillNormalizer = None

# Try multiple import strategies for skill_dedup_normalized
import_strategies = [
    # Strategy 1: From current folder with dot
    lambda: __import__('skill_dedup_normalized', fromlist=['SkillProcessor', 'SkillMatchEngine', 'SkillMatchResult', 'SkillNormalizer']),
    # Strategy 2: From current folder without dot
    lambda: __import__('skill_dedup_normalized', fromlist=['SkillProcessor', 'SkillMatchEngine', 'SkillMatchResult', 'SkillNormalizer']),
    # Strategy 3: Try with llm prefix
    lambda: __import__('llm.skill_dedup_normalized', fromlist=['SkillProcessor', 'SkillMatchEngine', 'SkillMatchResult', 'SkillNormalizer']),
]

for strategy in import_strategies:
    try:
        module = strategy()
        SkillProcessor = getattr(module, 'SkillProcessor', None)
        SkillMatchEngine = getattr(module, 'SkillMatchEngine', None)
        SkillMatchResult = getattr(module, 'SkillMatchResult', None)
        SkillNormalizer = getattr(module, 'SkillNormalizer', None)
        
        if all([SkillProcessor, SkillMatchEngine, SkillMatchResult, SkillNormalizer]):
            print(f"[OK] Imported from skill_dedup_normalized successfully")
            break
    except (ImportError, AttributeError) as e:
        continue

# 🔥 Jika masih None, coba fallback terakhir
if SkillProcessor is None or SkillMatchEngine is None:
    print("[WARN] Cannot import SkillProcessor from skill_dedup_normalized, using direct file loading...")
    try:
        import importlib.util
        skill_dedup_file = os.path.join(current_dir, 'skill_dedup_normalized.py')
        if os.path.exists(skill_dedup_file):
            spec = importlib.util.spec_from_file_location("skill_dedup_normalized", skill_dedup_file)
            skill_dedup_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(skill_dedup_module)
            
            SkillProcessor = skill_dedup_module.SkillProcessor
            SkillMatchEngine = skill_dedup_module.SkillMatchEngine
            SkillMatchResult = skill_dedup_module.SkillMatchResult
            SkillNormalizer = skill_dedup_module.SkillNormalizer
            print("[OK] Loaded SkillProcessor from skill_dedup_normalized.py file")
    except Exception as e:
        print(f"[ERROR] Failed via file path: {e}")

# 🔥 Final check
if SkillExtractor is None:
    print("\n" + "=" * 70)
    print("❌ ERROR: Cannot import SkillExtractor!")
    print("=" * 70)
    print(f"Please ensure file exists:")
    print(f"  - {os.path.join(current_dir, 'skill_extractor.py')}")
    print("\nOr run from backend folder:")
    print("  cd backend")
    print("  python -m llm.process_jobs")
    print("=" * 70)
    sys.exit(1)

if SkillProcessor is None:
    print("\n" + "=" * 70)
    print("❌ ERROR: Cannot import SkillProcessor from skill_dedup_normalized!")
    print("=" * 70)
    print(f"Please ensure file exists:")
    print(f"  - {os.path.join(current_dir, 'skill_dedup_normalized.py')}")
    print("=" * 70)
    sys.exit(1)

print("[OK] All imports successful!")
print(f"  SkillExtractor: {'[OK]' if SkillExtractor else '[FAIL]'}")
print(f"  SkillProcessor: {'[OK]' if SkillProcessor else '[FAIL]'}")
print(f"  SkillMatchResult: {'[OK]' if SkillMatchResult else '[FAIL]'}")
print(f"  SkillNormalizer: {'[OK]' if SkillNormalizer else '[FAIL]'}")

# ============================================================
# REST OF CODE
# ============================================================

from sqlalchemy import func, select
from database.connection import get_db_context
from database.models import Job, JobAnalysis, JobSkill, Keyword, Skill, SkillType
from utils.location_handler import LocationNormalizer


class _RateLimiter:
    """Enhanced rate limiter dengan exponential backoff"""
    
    def __init__(self, min_interval_seconds: float = 3.0):
        self._min_interval = float(min_interval_seconds)
        self._lock = threading.Lock()
        self._next_time = 0.0
        self._consecutive_errors = 0
        self._max_backoff = 60.0

    def wait(self, error: bool = False) -> None:
        """Wait with backoff jika ada error"""
        with self._lock:
            if error:
                self._consecutive_errors += 1
                backoff = min(
                    self._min_interval * (2 ** self._consecutive_errors),
                    self._max_backoff
                )
                wait_time = backoff + random.uniform(0.5, 2.0)
            else:
                self._consecutive_errors = max(0, self._consecutive_errors - 1)
                now = time.monotonic()
                if now < self._next_time:
                    wait_time = self._next_time - now + random.uniform(0.1, 0.5)
                else:
                    wait_time = 0
            
            if wait_time > 0:
                time.sleep(wait_time)
            
            self._next_time = time.monotonic() + self._min_interval


class JobProcessor:
    def __init__(self):
        # 🔥 Inisialisasi SkillExtractor
        try:
            self.extractor = SkillExtractor()
            print("[OK] SkillExtractor initialized successfully")
        except Exception as e:
            print(f"[ERROR] Failed to initialize SkillExtractor: {e}")
            print("  Please check GROQ_API_KEY in .env")
            raise
        
        self.skill_type_cache = {}
        
        # 🔥 Inisialisasi SkillProcessor dari skill_dedup_normalized
        try:
            self.skill_processor = SkillProcessor()
            print("[OK] SkillProcessor initialized from skill_dedup_normalized")
        except Exception as e:
            print(f"[ERROR] Failed to initialize SkillProcessor: {e}")
            raise
        
        self._load_skill_types()
        self._thread_local = threading.local()
        
        # Rate limiter
        min_interval = float(os.getenv("GROQ_MIN_INTERVAL", "3.0"))
        self.global_limiter = _RateLimiter(min_interval)
        print(f"[OK] Rate limiter initialized: min_interval={min_interval}s")
    
    def _load_skill_types(self):
        """Load skill types into cache"""
        with get_db_context() as db:
            skill_types = db.query(SkillType).all()
            for st in skill_types:
                self.skill_type_cache[st.name] = st.id
        print(f"[OK] Loaded {len(self.skill_type_cache)} skill types into cache")
        print(f"  • Tech Stack (tools): ID {self.skill_type_cache.get('tech_stack', 'N/A')}")
        print(f"  • Technical Skill: ID {self.skill_type_cache.get('technical_skill', 'N/A')}")
        print(f"  • Soft Skill: ID {self.skill_type_cache.get('soft_skill', 'N/A')}")
    
    def find_empty_jobs(self) -> List[int]:
        with get_db_context() as db:
            processed_job_ids = select(JobSkill.job_id).distinct()
            empty_jobs = db.query(Job.id).filter(~Job.id.in_(processed_job_ids)).all()
            return [job_id[0] for job_id in empty_jobs]
    
    def find_empty_analysis_jobs(self) -> List[int]:
        with get_db_context() as db:
            empty_jobs = db.query(Job.id).join(
                JobAnalysis, JobAnalysis.job_id == Job.id
            ).filter(
                JobAnalysis.tech_stack.in_(["", None]),
                JobAnalysis.technical_skill.in_(["", None]),
                JobAnalysis.soft_skill.in_(["", None])
            ).all()
            return [job_id[0] for job_id in empty_jobs]
    
    def reprocess_empty_jobs(
        self,
        batch_size: int = 10,
        limit: Optional[int] = None,
        mode: str = "stable",
        max_workers: Optional[int] = None,
        min_request_interval_seconds: Optional[float] = None,
    ):
        print("=" * 70)
        print("REPROCESS EMPTY JOBS - Ulang Ekstraksi Job yang Kosong (0 Skills)")
        print("=" * 70)
        
        empty_job_ids = self.find_empty_jobs()
        
        if not empty_job_ids:
            print("✓ Semua job sudah memiliki skill! Tidak ada yang perlu diulang.")
            return
        
        print(f"\n⚠️  DETEKSI: {len(empty_job_ids)} job dengan 0 skills")
        print(f"Akan mengulang ekstraksi dengan mode: {mode.upper()}\n")
        
        if limit:
            empty_job_ids = empty_job_ids[:limit]
            print(f"Dibatasi processing: {len(empty_job_ids)} job\n")
        
        with get_db_context() as db:
            analysis_count = db.query(JobAnalysis).filter(
                JobAnalysis.job_id.in_(empty_job_ids)
            ).count()
            
            if analysis_count > 0:
                print(f"🗑️  Membersihkan {analysis_count} entries JobAnalysis yang kosong...")
                db.query(JobAnalysis).filter(
                    JobAnalysis.job_id.in_(empty_job_ids)
                ).delete()
                db.commit()
                print(f"✓ Cleared\n")
        
        self.process_all_jobs(
            batch_size=batch_size,
            limit=None,
            mode=mode,
            max_workers=max_workers,
            min_request_interval_seconds=min_request_interval_seconds,
        )
    
    def process_job_stable(self, job_id: int) -> bool:
        try:
            with get_db_context() as db:
                job = db.query(Job).filter(Job.id == job_id).first()
                if not job:
                    print(f"  ❌ Job #{job_id} tidak ditemukan")
                    return False

                job.status_ekstraksi = "in_progress"
                db.commit()
                
                if not job.job_description or len(job.job_description) < 30:
                    print(f"  ⚠️  Deskripsi job terlalu pendek, skip")
                    job.status_ekstraksi = "pending"
                    db.commit()
                    return False
                
                self.global_limiter.wait()
                
                result = self.extractor.extract_skills(job.job_description)
                if not result:
                    print(f"  ❌ Gagal ekstraksi")
                    job.status_ekstraksi = "pending"
                    db.commit()
                    return False
                
                skills_added = self._save_all_skills_with_normalization(db, job, result)
                
                job.status_ekstraksi = "completed"
                db.commit()
                
                print(f"  ✓ Berhasil ekstraksi {skills_added} skill")
                return True
                
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate_limit" in error_str:
                print(f"  ⚠️ Rate limit, waiting longer...")
                self.global_limiter.wait(error=True)
            
            try:
                with get_db_context() as db:
                    job = db.query(Job).filter(Job.id == job_id).first()
                    if job:
                        job.status_ekstraksi = "pending"
            except Exception:
                pass
            print(f"  ❌ Error: {str(e)}")
            return False
    
    def _save_all_skills_with_normalization(self, db, job: Job, result: Dict) -> int:
        """
        Save skills with proper normalization using SkillProcessor from skill_dedup_normalized.
        FIX: Gunakan canonical form yang benar untuk normalisasi.
        FIX: Deduplikasi skill dalam setiap kategori (mencegah AWS muncul berkali-kali).
        """
        total_added = 0
        
        # Debug info
        print(f"\n[DEBUG] Processing job #{job.id} with SkillProcessor: {type(self.skill_processor)}")
        
        skill_type_mapping = {
            "tech_stack": self.skill_type_cache.get("tech_stack", 3),
            "technical_skill": self.skill_type_cache.get("technical_skill", 2),
            "soft_skill": self.skill_type_cache.get("soft_skill", 1),
        }
        
        # 🔥 FIX: Proses setiap kategori dengan deduplikasi
        for skill_type_name, skill_type_id in skill_type_mapping.items():
            skill_names = result.get(skill_type_name, [])
            if not skill_names:
                continue
            
            # 🔥 DEDUPLIKASI: Hapus skill yang sama dalam satu kategori
            seen = set()
            unique_skills = []
            for skill in skill_names:
                if not skill or len(skill) < 2:
                    continue
                # Normalisasi untuk deduplikasi
                normalized = SkillNormalizer.normalize_skill(skill)
                if normalized not in seen:
                    seen.add(normalized)
                    unique_skills.append(skill)
                else:
                    print(f"    ⚠️ Duplicate skipped in {skill_type_name}: '{skill}'")
            
            if len(unique_skills) != len(skill_names):
                print(f"    ✅ Deduplicated {skill_type_name}: {len(skill_names)} → {len(unique_skills)} skills")
            
            print(f"  {skill_type_name}: found {len(unique_skills)} skills (after dedup)")
            
            for skill_name in unique_skills:
                if not skill_name or len(skill_name) < 2:
                    continue
                
                # 🔥 FIX: Dapatkan canonical form TERLEBIH DAHULU
                canonical, found = SkillNormalizer.get_canonical_form(skill_name, skill_type_id)
                
                # 🔥 FIX: Gunakan canonical jika ditemukan
                if found:
                    skill_to_process = canonical
                    print(f"    Normalizing: '{skill_name}' → '{canonical}'")
                else:
                    skill_to_process = skill_name
                    print(f"    Processing: '{skill_name}' (no canonical found)")
                
                # Process skill using canonical form
                match_result = self.skill_processor.process_skill(skill_to_process, skill_type_id)
                
                # Debug info
                print(f"      → matched_id: {match_result.matched_id}")
                print(f"      → action: {match_result.action}")
                print(f"      → skill_type: {match_result.skill_type_name}")
                print(f"      → normalized: {match_result.normalized_skill}")
                
                if match_result.matched_id and match_result.action != "rejected":
                    # Link skill to job using the engine from skill_dedup_normalized
                    if hasattr(self.skill_processor, 'engine') and self.skill_processor.engine:
                        linked = self.skill_processor.engine.link_skill_to_job(
                            job.id, match_result.matched_id
                        )
                        if linked:
                            total_added += 1
                            print(f"      ✅ Added! Total: {total_added}")
                        else:
                            print(f"      ⚠️ Already linked or failed")
                    else:
                        print(f"      ❌ No engine available!")
                else:
                    if match_result.action == "rejected":
                        print(f"      ❌ Rejected (generic or invalid)")
                    else:
                        print(f"      ❌ No matched_id")
        
        print(f"[DEBUG] Total skills added for job #{job.id}: {total_added}")
        
        # 🔥 FIX: Save to JobAnalysis - deduplikasi juga di sini
        tech_stack_set = set()
        for s in result.get("tech_stack", []):
            canonical, _ = SkillNormalizer.get_canonical_form(s, 3)
            tech_stack_set.add(canonical if canonical else s)
        
        technical_set = set()
        for s in result.get("technical_skill", []):
            canonical, _ = SkillNormalizer.get_canonical_form(s, 2)
            technical_set.add(canonical if canonical else s)
        
        soft_set = set()
        for s in result.get("soft_skill", []):
            canonical, _ = SkillNormalizer.get_canonical_form(s, 1)
            soft_set.add(canonical if canonical else s)
        
        self._save_job_analysis_v2(
            db, job, result,
            list(tech_stack_set),
            list(technical_set),
            list(soft_set)
        )
        
        return total_added
    
    def process_all_jobs(
        self,
        batch_size: int = 10,
        limit: Optional[int] = None,
        mode: str = "stable",
        max_workers: Optional[int] = None,
        min_request_interval_seconds: Optional[float] = None,
    ):
        mode = (mode or "stable").lower().strip()

        if min_request_interval_seconds:
            self.global_limiter = _RateLimiter(min_request_interval_seconds)

        if mode == "batch":
            self.global_limiter = _RateLimiter(max(
                min_request_interval_seconds or 3.0,
                5.0
            ))

        banner = {
            "batch": "EKSTRAKSI SKILL - BATCH MODE",
            "stable": "EKSTRAKSI SKILL - STABLE FAST MODE",
            "ultra": "EKSTRAKSI SKILL - ULTRA FAST MODE",
            "normal": "EKSTRAKSI SKILL - NORMAL MODE",
        }.get(mode, f"EKSTRAKSI SKILL - {mode.upper()} MODE")

        print("=" * 70)
        print(banner)
        print("=" * 70)
        
        with get_db_context() as db:
            processed_job_ids = select(JobSkill.job_id).distinct()
            query = db.query(Job).filter(~Job.id.in_(processed_job_ids))
            
            if limit:
                query = query.limit(limit)
            
            jobs = query.all()
            
            if not jobs:
                print("Tidak ada job yang perlu diproses!")
                return
            
            print(f"\nDitemukan {len(jobs)} job yang belum diproses")
            print(f"Memproses dalam batch {batch_size} job...\n")

            if mode == "batch":
                total_skills_added, processed_count = self._process_batch_mode(
                    db, jobs, batch_size=batch_size
                )
            elif mode == "ultra":
                total_skills_added, processed_count = self._process_ultra_mode(
                    db, jobs, batch_size, max_workers=max_workers
                )
            elif mode == "normal":
                total_skills_added, processed_count = self._process_normal_mode(db, jobs, batch_size)
            else:
                total_skills_added, processed_count = self._process_stable_mode(
                    db, jobs, batch_size,
                    max_workers=max_workers,
                    min_request_interval_seconds=min_request_interval_seconds,
                )
            
            print("\n" + "=" * 70)
            print("EKSTRAKSI SELESAI!")
            print("=" * 70)
            print(f"Job diproses: {processed_count}")
            print(f"Total skill disimpan: {total_skills_added}")
    
    def _get_thread_extractor(self) -> SkillExtractor:
        extractor = getattr(self._thread_local, "extractor", None)
        if extractor is None:
            extractor = SkillExtractor(model=self.extractor.model)
            self._thread_local.extractor = extractor
        return extractor

    def _extract_job_skills_text(
        self,
        job_id: int,
        job_description: str,
        limiter: Optional[_RateLimiter],
    ) -> Optional[Dict]:
        if not job_description or len(job_description) < 50:
            return None

        if limiter is not None:
            limiter.wait()

        extractor = self._get_thread_extractor()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return extractor.extract_skills(job_description)
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate_limit" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 10
                        print(f"  ⚠️ Rate limit, retry in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                return None
        
        return None
    
    def _process_ultra_mode(
        self,
        db,
        jobs: List[Job],
        batch_size: int,
        max_workers: Optional[int] = None,
    ) -> Tuple[int, int]:
        total_skills_added = 0
        processed_count = 0
        
        workers = min(max_workers or 3, 3)
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i+batch_size]
            batch_num = i//batch_size + 1
            
            print(f"\n⚡ Batch {batch_num}/{(len(jobs)-1)//batch_size + 1} ({len(batch)} jobs) - ULTRA FAST")
            print("-" * 70)

            batch_payload = [(job.id, (job.job_description or "")) for job in batch]

            extraction_results = []

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_to_job = {
                    executor.submit(self._extract_job_skills_text, job_id, desc, self.global_limiter): job_id
                    for (job_id, desc) in batch_payload
                }
                
                for future in as_completed(future_to_job):
                    job_id = future_to_job[future]
                    try:
                        result = future.result()
                        if result:
                            extraction_results.append((job_id, result))
                            print(f"  ✓ #{job_id}")
                    except Exception as e:
                        print(f"  ✗ #{job_id}: Error - {str(e)[:80]}")
            
            try:
                job_by_id = {job.id: job for job in batch}
                for job_id, result in extraction_results:
                    job = job_by_id.get(job_id)
                    if not job:
                        continue
                    try:
                        skills_added = self._save_all_skills_with_normalization(db, job, result)
                        total_skills_added += skills_added
                        processed_count += 1
                    except Exception as save_err:
                        print(f"  ✗ Failed to save job #{job_id}: {save_err}")
                        try:
                            db.rollback()
                        except:
                            pass
                        continue
                
                db.commit()
                print(f"  💾 Batch {batch_num} saved: {len(extraction_results)} jobs, {total_skills_added} total skills")
                
                time.sleep(random.uniform(2, 4))
                    
            except Exception as e:
                print(f"  ✗ Batch commit error: {e}")
                try:
                    db.rollback()
                except:
                    pass
        
        return total_skills_added, processed_count

    def _process_batch_mode(self, db, jobs: List[Job], batch_size: int) -> Tuple[int, int]:
        total_skills_added = 0
        processed_count = 0

        llm_batch_size = int(os.getenv("LLM_BATCH_SIZE", "5"))
        llm_max_chars = int(os.getenv("LLM_MAX_CHARS_PER_JOB", "800"))
        min_interval = float(os.getenv("GROQ_MIN_INTERVAL", "3.0"))

        print(f"⚙️  Batch settings: llm_batch_size={llm_batch_size}, max_chars/job={llm_max_chars}, min_interval={min_interval}s")

        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_num = i // batch_size + 1
            print(f"\nBatch {batch_num}/{(len(jobs)-1)//batch_size + 1} ({len(batch)} jobs) - BATCH")
            print("-" * 70)

            try:
                for j in range(0, len(batch), llm_batch_size):
                    chunk = batch[j:j + llm_batch_size]
                    payload = [
                        {"id": job.id, "description": (job.job_description or "")}
                        for job in chunk
                        if job.job_description and len(job.job_description) >= 30
                    ]
                    if not payload:
                        continue

                    self.global_limiter.wait()

                    try:
                        results = self.extractor.extract_skills_batch(
                            payload, max_chars_per_job=llm_max_chars
                        )
                    except Exception as e:
                        if "429" in str(e).lower():
                            print(f"  ⚠️ Rate limit, waiting longer...")
                            self.global_limiter.wait(error=True)
                            results = self.extractor.extract_skills_batch(
                                payload, max_chars_per_job=llm_max_chars
                            )
                        else:
                            raise e

                    job_by_id = {job.id: job for job in chunk}
                    for job_id, result in results.items():
                        job = job_by_id.get(job_id)
                        if not job:
                            continue
                        try:
                            skills_added = self._save_all_skills_with_normalization(db, job, result)
                            total_skills_added += skills_added
                            processed_count += 1
                            print(f"  ✓ #{job_id}")
                        except Exception as save_err:
                            print(f"  ✗ Failed to save job #{job_id}: {save_err}")
                            try:
                                db.rollback()
                            except:
                                pass
                            continue

                    time.sleep(random.uniform(2, 4))

                db.commit()
                print(f"  💾 Batch {batch_num} saved")
                
                time.sleep(random.uniform(3, 5))
                
            except Exception as e:
                print(f"  ✗ Batch error: {e}")
                try:
                    db.rollback()
                except:
                    pass

        return total_skills_added, processed_count

    def _process_stable_mode(
        self,
        db,
        jobs: List[Job],
        batch_size: int,
        max_workers: Optional[int] = None,
        min_request_interval_seconds: Optional[float] = None,
    ) -> Tuple[int, int]:
        total_skills_added = 0
        processed_count = 0

        workers = min(max_workers or 2, 2)
        min_interval = (
            float(min_request_interval_seconds)
            if min_request_interval_seconds is not None
            else float(os.getenv("GROQ_MIN_INTERVAL", "3.0"))
        )

        print(f"⚙️  Stable settings: workers={workers}, min_interval={min_interval}s")

        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i + batch_size]
            batch_num = i // batch_size + 1
            print(f"\nBatch {batch_num}/{(len(jobs)-1)//batch_size + 1} ({len(batch)} jobs) - STABLE")
            print("-" * 70)

            batch_payload = [(job.id, (job.job_description or "")) for job in batch]
            extraction_results: List[Tuple[int, Dict]] = []

            with ThreadPoolExecutor(max_workers=min(workers, len(batch_payload))) as executor:
                future_to_job_id = {
                    executor.submit(self._extract_job_skills_text, job_id, desc, self.global_limiter): job_id
                    for (job_id, desc) in batch_payload
                }

                for future in as_completed(future_to_job_id):
                    job_id = future_to_job_id[future]
                    try:
                        result = future.result()
                        if result:
                            extraction_results.append((job_id, result))
                            print(f"  ✓ #{job_id}")
                    except Exception as e:
                        print(f"  ✗ #{job_id}: {str(e)[:80]}")

            try:
                job_by_id = {job.id: job for job in batch}
                for job_id, result in extraction_results:
                    job = job_by_id.get(job_id)
                    if not job:
                        continue
                    try:
                        skills_added = self._save_all_skills_with_normalization(db, job, result)
                        total_skills_added += skills_added
                        processed_count += 1
                    except Exception as save_err:
                        print(f"    ✗ Failed to save job #{job_id}: {save_err}")
                        try:
                            db.rollback()
                        except:
                            pass
                        continue

                db.commit()
                print(f"  💾 Batch {batch_num} saved: {len(extraction_results)} jobs, {total_skills_added} skills")
                
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"  ✗ Batch commit error: {e}")
                try:
                    db.rollback()
                except:
                    pass

        return total_skills_added, processed_count
    
    def _process_normal_mode(self, db, jobs: List[Job], batch_size: int) -> Tuple[int, int]:
        total_skills_added = 0
        processed_count = 0
        
        for i in range(0, len(jobs), batch_size):
            batch = jobs[i:i+batch_size]
            batch_num = i//batch_size + 1
            
            print(f"\nBatch {batch_num} ({len(batch)} job)...")
            print("-" * 70)
            
            for job in batch:
                try:
                    print(f"\n  Job #{job.id}: {job.job_title}")
                    print(f"  Company: {job.company}")
                    
                    if not job.job_description or len(job.job_description) < 30:
                        print(f"    Deskripsi terlalu pendek, skip...")
                        continue
                    
                    self.global_limiter.wait()
                    
                    result = self.extractor.extract_skills(job.job_description)
                    if not result:
                        print(f"    Gagal ekstraksi")
                        continue
                    
                    skills_added = self._save_all_skills_with_normalization(db, job, result)
                    
                    total_skills_added += skills_added
                    processed_count += 1
                    print(f"    Berhasil: {skills_added} skill disimpan")
                    
                    if processed_count % 10 == 0:
                        db.commit()
                        print(f"\n  Data tersimpan: {processed_count} job telah diproses")
                    
                    time.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    db.rollback()
                    error_str = str(e).lower()
                    print(f"    Error: {e}")
                    if "429" in error_str or "rate_limit" in error_str:
                        print(f"    Rate limit hit, waiting 60 seconds...")
                        self.global_limiter.wait(error=True)
                    continue
            
            try:
                db.commit()
                print(f"\n  Batch {batch_num} selesai dan tersimpan!")
            except Exception as e:
                db.rollback()
                print(f"\n  Error saat commit batch: {e}")
            
            if i + batch_size < len(jobs):
                print(f"  Jeda 5 detik sebelum batch berikutnya...")
                time.sleep(5)
        
        return total_skills_added, processed_count
    
    def _save_job_analysis_v2(self, db, job: Job, result: dict,
                              tech_stack_list: list, technical_skill_list: list,
                              soft_skill_list: list):
        try:
            keyword = db.query(Keyword).filter(Keyword.id == job.keyword_id).first()
            keyword_name = keyword.keyword if keyword else "Unknown"
            
            normalized_location = LocationNormalizer.normalize(job.location)
            
            # Normalisasi untuk JobAnalysis - menggunakan canonical form
            tech_stack_normalized = []
            for s in tech_stack_list:
                if s:
                    canonical, _ = SkillNormalizer.get_canonical_form(s, 3)
                    tech_stack_normalized.append(canonical if canonical else s)
            
            technical_normalized = []
            for s in technical_skill_list:
                if s:
                    canonical, _ = SkillNormalizer.get_canonical_form(s, 2)
                    technical_normalized.append(canonical if canonical else s)
            
            soft_normalized = []
            for s in soft_skill_list:
                if s:
                    canonical, _ = SkillNormalizer.get_canonical_form(s, 1)
                    soft_normalized.append(canonical if canonical else s)
            
            existing = db.query(JobAnalysis).filter(JobAnalysis.job_id == job.id).first()
            
            if existing:
                existing.location = normalized_location
                existing.tech_stack = ", ".join(tech_stack_normalized) if tech_stack_normalized else None
                existing.technical_skill = ", ".join(technical_normalized) if technical_normalized else None
                existing.soft_skill = ", ".join(soft_normalized) if soft_normalized else None
                existing.extracted_at = func.now()
                existing.ai_model = self.extractor.model
            else:
                analysis = JobAnalysis(
                    job_id=job.id,
                    job_title=job.job_title,
                    company=job.company,
                    location=normalized_location,
                    posted_date=job.posted_date,
                    link=job.link,
                    job_description=job.job_description,
                    keyword=keyword_name,
                    tech_stack=", ".join(tech_stack_normalized) if tech_stack_normalized else None,
                    technical_skill=", ".join(technical_normalized) if technical_normalized else None,
                    soft_skill=", ".join(soft_normalized) if soft_normalized else None,
                    ai_model=self.extractor.model
                )
                db.add(analysis)
            
        except Exception as e:
            print(f"    Warning: Gagal menyimpan job_analysis: {e}")
    
    def get_statistics(self):
        with get_db_context() as db:
            total_jobs = db.query(Job).count()
            processed_jobs = db.query(Job).join(JobSkill).distinct().count()
            total_skills = db.query(JobSkill).count()
            unique_skills = db.query(Skill).count()
            
            print("\n" + "=" * 70)
            print("STATISTIK EKSTRAKSI SKILL")
            print("=" * 70)
            print(f"Total job: {total_jobs}")
            print(f"Job diproses: {processed_jobs}")
            print(f"Total skill ekstrak: {total_skills}")
            print(f"Unique skill: {unique_skills}")
            
            print("\n📊 Skill per kategori:")
            skill_types = db.query(SkillType).all()
            for st in skill_types:
                count = db.query(Skill).filter(Skill.skill_type_id == st.id).count()
                print(f"  • {st.name}: {count} skill")
            
            top_skills = db.query(
                Skill.name,
                SkillType.name.label('type'),
                func.count(JobSkill.id).label('count')
            ).join(
                JobSkill, JobSkill.skill_id == Skill.id
            ).join(
                SkillType, SkillType.id == Skill.skill_type_id
            ).group_by(
                Skill.name, SkillType.name
            ).order_by(
                func.count(JobSkill.id).desc()
            ).limit(10).all()
            
            print("\n🏆 Top 10 Skills:")
            for idx, (skill_name, skill_type, count) in enumerate(top_skills, 1):
                print(f"  {idx}. {skill_name} ({skill_type}): {count} job")
            
            print("\n🔍 Checking for potential duplicates...")
            all_skills = db.query(Skill).all()
            seen = {}
            duplicates = []
            for skill in all_skills:
                normalized = SkillNormalizer.normalize_skill(skill.name)
                if normalized in seen:
                    duplicates.append((skill.name, seen[normalized]))
                else:
                    seen[normalized] = skill.name
            
            if duplicates:
                print(f"  ⚠️ Found {len(duplicates)} potential duplicates:")
                for dup in duplicates[:10]:
                    print(f"    • '{dup[0]}' ↔ '{dup[1]}'")
                if len(duplicates) > 10:
                    print(f"    ... and {len(duplicates) - 10} more")
                print("  Run 'python normalize_skills.py --all' to fix duplicates")
            else:
                print("  ✅ No duplicates found!")


if __name__ == "__main__":
    processor = JobProcessor()

    mode = os.getenv("PROCESS_MODE", "stable")
    batch_size = int(os.getenv("PROCESS_BATCH_SIZE", "10"))
    max_workers = os.getenv("PROCESS_MAX_WORKERS")
    max_workers = int(max_workers) if max_workers else None
    min_interval = os.getenv("GROQ_MIN_INTERVAL")
    min_interval = float(min_interval) if min_interval else 3.0
    
    if mode == "batch":
        os.environ["LLM_BATCH_SIZE"] = os.getenv("LLM_BATCH_SIZE", "5")
        batch_size = min(batch_size, 10)
    
    reprocess_empty = os.getenv("REPROCESS_EMPTY", "").lower() in ("true", "1", "yes")
    
    print(f"\n⚙️  CONFIGURATION:")
    print(f"  • Mode: {mode}")
    print(f"  • Batch size: {batch_size}")
    print(f"  • Max workers: {max_workers or 'auto'}")
    print(f"  • Min interval: {min_interval}s")
    if mode == "batch":
        print(f"  • LLM Batch size: {os.getenv('LLM_BATCH_SIZE', '5')}")
    print("")
    
    if reprocess_empty:
        print("\n🔄 Mode REPROCESS_EMPTY aktif - akan retry job-job yang kosong\n")
        processor.reprocess_empty_jobs(
            batch_size=batch_size,
            limit=None,
            mode=mode,
            max_workers=max_workers,
            min_request_interval_seconds=min_interval,
        )
    else:
        processor.process_all_jobs(
            batch_size=batch_size,
            limit=None,
            mode=mode,
            max_workers=max_workers,
            min_request_interval_seconds=min_interval,
        )
    
    processor.get_statistics()