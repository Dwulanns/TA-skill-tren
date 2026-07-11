import os
import json
import re
import time
import sys
import threading
from typing import Dict, List
from dotenv import load_dotenv
from groq import Groq

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    GROQ_API_KEY,
    GROQ_MODEL,
    GROQ_MAX_TOKENS,
    GROQ_TEMPERATURE,
    GROQ_TOP_P,
    LLM_MAX_RETRIES,
    LLM_BASE_RETRY_DELAY,
    SKILL_CHAR_LIMIT_PER_JOB,
)
from exceptions import GroqAPIException, RateLimitException
from logger import get_logger

load_dotenv()

logger = get_logger(__name__)


class SkillExtractor:
    """Ekstrak skills dari job description menggunakan Groq Llama"""

    # ------------------------------------------------------------------
    # SAFETY-NET: keyword soft skill untuk post-processing.
    #
    # Kenapa ini perlu walau prompt sudah sangat ketat?
    # Karena LLM (terutama model kecil seperti llama-3.1-8b-instant) tidak
    # 100% patuh terhadap instruksi prompt. Kadang skill seperti
    # "Problem Solving" atau "Analytical Thinking" tetap nyasar masuk ke
    # technical_skill walau prompt sudah melarangnya secara eksplisit.
    #
    # Layer ini bertindak sebagai validator terakhir: setelah JSON di-parse,
    # setiap item di technical_skill dicek ulang. Kalau cocok dengan keyword
    # soft skill di bawah, item tsb otomatis dipindah ke soft_skill.
    #
    # Matching dilakukan dengan substring containment pada string yang sudah
    # dinormalisasi (lowercase, strip, "-" -> spasi), sehingga variasi
    # seperti "Strong Communication Skills" atau "Problem-Solving" tetap
    # tertangkap.
    # ------------------------------------------------------------------
    SOFT_SKILL_KEYWORDS = [
        # English
        "problem solving",
        "analytical thinking",
        "analytical skill",
        "critical thinking",
        "communication",
        "leadership",
        "teamwork",
        "team work",
        "team player",
        "collaboration",
        "time management",
        "adaptability",
        "adaptable",
        "creativity",
        "creative thinking",
        "emotional intelligence",
        "negotiation",
        "presentation skill",
        "writing skill",
        "report writing",
        "attention to detail",
        "organization skill",
        "organizational skill",
        "conflict resolution",
        "decision making",
        "customer service",
        "interpersonal",
        "self motivation",
        "work ethic",
        "stress management",
        "multitasking",
        # Indonesian
        "pemecahan masalah",
        "berpikir analitis",
        "berpikir kritis",
        "komunikasi",
        "kepemimpinan",
        "kerja tim",
        "kerja sama tim",
        "kolaborasi",
        "manajemen waktu",
        "kemampuan beradaptasi",
        "adaptasi",
        "kreativitas",
        "kecerdasan emosional",
        "negosiasi",
        "kemampuan presentasi",
        "ketelitian",
        "manajemen organisasi",
        "resolusi konflik",
        "pengambilan keputusan",
        "layanan pelanggan",
        "keterampilan interpersonal",
        "motivasi diri",
        "etos kerja",
        "manajemen stres",
        "multitugas",
    ]

    # ------------------------------------------------------------------
    # SAFETY-NET #2: grounding/anti-halusinasi.
    #
    # Masalah yang ditambal di sini: LLM kadang menambahkan skill yang
    # "biasanya" relevan untuk suatu posisi (mis. menambahkan "Python"
    # untuk lowongan Data Scientist) padahal kata tsb TIDAK PERNAH muncul
    # di teks deskripsi aslinya. Ini murni halusinasi berbasis pola umum,
    # bukan ekstraksi dari teks.
    #
    # SKILL_ALIASES membantu supaya skill yang memang valid tapi ditulis
    # dalam bentuk singkatan di teks asli (mis. teks bilang "ML" tapi LLM
    # menormalisasi jadi "Machine Learning") tidak ikut terbuang oleh
    # grounding check.
    # ------------------------------------------------------------------
    SKILL_ALIASES = {
        "machine learning": ["ml"],
        "deep learning": ["dl"],
        "natural language processing": ["nlp"],
        "artificial intelligence": ["ai"],
        "javascript": ["js"],
        "typescript": ["ts"],
        "continuous integration": ["ci/cd", "ci cd", "ci"],
        "continuous deployment": ["ci/cd", "ci cd", "cd"],
        "ci/cd": ["ci cd", "continuous integration", "continuous deployment"],
        "user interface": ["ui"],
        "user experience": ["ux"],
        "object oriented programming": ["oop"],
        "structured query language": ["sql"],
        "amazon web services": ["aws"],
        "google cloud platform": ["gcp"],
        "computer vision": ["cv"],
        "extract transform load": ["etl"],
    }

    # 🔁 KEMBALI KE llama-3.1-8b-instant sebagai default model.
    # (Sebelumnya pernah dicoba openai/gpt-oss-120b, tapi gugur karena
    # ketidakstabilan operasional. llama-3.1-8b-instant unggul di semua
    # aspek setelah ditambahkan _reclassify_skills() sebagai safety-net,
    # sehingga jadi solusi paling optimal: akurasi setara model besar,
    # dengan kecepatan, efisiensi biaya, dan kontinuitas operasional yang
    # lebih baik.)
    DEFAULT_MODEL = "llama-3.1-8b-instant"

    def __init__(self, model: str = None):
        """
        Initialize skill extractor dengan Groq
        
        Args:
            model: Groq model name. Default: llama-3.1-8b-instant (cepat, murah,
                   stabil, dan akurat untuk klasifikasi technical vs soft skill
                   setelah dibantu safety-net _reclassify_skills().
                   Bisa di-override manual, misal: SkillExtractor(model="openai/gpt-oss-120b")
        """
        self.model = model or self.DEFAULT_MODEL
        self.api_key = GROQ_API_KEY
        
        if not self.api_key:
            error_msg = "GROQ_API_KEY tidak ditemukan di .env file"
            logger.error(error_msg)
            raise GroqAPIException(error_msg)
        
        # max_retries=0: matikan retry otomatis bawaan SDK Groq.
        # Tanpa ini, SDK akan retry sendiri di balik layar (dengan delay-nya
        # sendiri) SEBELUM exception sampai ke retry logic custom kita di
        # extract_skills/extract_skills_batch - dua lapis retry yang
        # tumpang tindih ini bikin total waktu tunggu saat 429 jadi gak
        # terkontrol/sulit diprediksi. Biar retry SEPENUHNYA dipegang
        # oleh kode kita sendiri (yang sudah punya backoff jelas).
        self.client = Groq(api_key=self.api_key, max_retries=0)
        logger.info(f"[OK] Groq client initialized: {self.model}")

    # ------------------------------------------------------------------
    # Helper untuk safety-net reclassification
    # ------------------------------------------------------------------
    def _normalize_skill(self, skill: str) -> str:
        """Normalisasi string skill untuk keperluan matching/dedup."""
        return " ".join(str(skill).strip().lower().replace("-", " ").split())

    def _is_soft_skill(self, skill: str) -> bool:
        """Cek apakah sebuah skill sebenarnya soft skill berdasarkan keyword list."""
        normalized = self._normalize_skill(skill)
        if not normalized:
            return False
        return any(keyword in normalized for keyword in self.SOFT_SKILL_KEYWORDS)

    def _dedup_preserve_order(self, items: List[str]) -> List[str]:
        """Dedup case-insensitive, tetap pertahankan casing kemunculan pertama."""
        seen = set()
        out = []
        for item in items:
            key = self._normalize_skill(item)
            if key and key not in seen:
                seen.add(key)
                out.append(item)
        return out

    def _reclassify_skills(self, result: Dict) -> Dict:
        """
        Safety-net post-processing.

        Memindahkan skill yang masih salah diklasifikasikan sebagai
        technical_skill (padahal sebenarnya soft_skill) ke soft_skill,
        lalu dedup tiap kategori. Dipanggil setelah JSON hasil LLM
        di-parse, baik untuk single extraction maupun batch extraction.
        """
        technical = result.get("technical_skill", []) or []
        soft = result.get("soft_skill", []) or []
        tech_stack = result.get("tech_stack", []) or []

        still_technical = []
        moved_to_soft = []

        for skill in technical:
            if self._is_soft_skill(skill):
                moved_to_soft.append(skill)
            else:
                still_technical.append(skill)

        return {
            "tech_stack": self._dedup_preserve_order(tech_stack),
            "technical_skill": self._dedup_preserve_order(still_technical),
            "soft_skill": self._dedup_preserve_order(soft + moved_to_soft),
        }

    # ------------------------------------------------------------------
    # Helper untuk grounding check (anti-halusinasi)
    # ------------------------------------------------------------------
    def _contains_token(self, token: str, normalized_text: str) -> bool:
        """
        Cek apakah `token` muncul sebagai unit kata/frasa utuh di dalam
        `normalized_text` (sudah dinormalisasi lowercase). Pakai word-boundary
        manual (bukan str.find biasa) supaya alias pendek seperti "ml", "ai",
        "ui" tidak salah match ke substring kata lain (mis. "ml" jangan
        sampai match ke "html" atau "simply").
        """
        token = token.strip()
        if not token:
            return False
        pattern = r"(?<![a-z0-9])" + re.escape(token) + r"(?![a-z0-9])"
        return re.search(pattern, normalized_text) is not None

    def _is_grounded(self, skill: str, normalized_text: str) -> bool:
        """
        Cek apakah sebuah skill benar-benar disebutkan (atau punya alias yang
        dikenal) di teks deskripsi pekerjaan asli.

        Ini adalah safety-net anti-halusinasi: LLM (apalagi model kecil)
        kadang menambahkan skill "populer/umum" untuk suatu posisi (misal
        menambahkan "Python" ke semua lowongan Data Science) padahal kata
        tsb tidak pernah disebut di teks aslinya. Layer ini membuang skill
        seperti itu setelah parsing JSON.
        """
        normalized_skill = self._normalize_skill(skill)
        if not normalized_skill:
            return False

        # 1) Cek langsung sebagai frasa utuh di teks
        if self._contains_token(normalized_skill, normalized_text):
            return True

        # 2) Cek alias yang dikenal (singkatan umum seperti ML, AI, JS, dll)
        for alias in self.SKILL_ALIASES.get(normalized_skill, []):
            if self._contains_token(alias, normalized_text):
                return True

        # 3) Cek partial match berbasis kata, untuk menangani kasus seperti
        #    LLM menormalisasi "Python Programming" (di teks) -> "Python"
        #    (output), atau urutan kata sedikit berbeda dari teks asli.
        words = [w for w in normalized_skill.split() if len(w) >= 3]
        if words:
            matched = sum(1 for w in words if self._contains_token(w, normalized_text))
            if matched / len(words) >= 0.6:
                return True

        return False

    def _filter_grounded(self, result: Dict, source_text: str) -> Dict:
        """
        Buang skill di tech_stack & technical_skill yang tidak benar-benar
        muncul (langsung maupun lewat alias yang dikenal) di teks deskripsi
        asli. Ini mencegah LLM "berhalusinasi" menambahkan skill populer
        (misal Python) hanya karena terdengar cocok dengan judul/jenis
        pekerjaan, padahal skill tsb tidak pernah disebut di deskripsi.

        soft_skill SENGAJA TIDAK difilter di sini, karena soft skill sering
        diimplikasikan secara tidak literal (mis. "mampu bekerja dalam tim
        dan berkomunikasi dengan baik" -> Teamwork, Communication), sehingga
        grounding check literal akan terlalu agresif untuk kategori ini.
        """
        normalized_text = self._normalize_skill(source_text or "")

        def _filter_list(items):
            kept = []
            for skill in items:
                if self._is_grounded(skill, normalized_text):
                    kept.append(skill)
                else:
                    logger.info(
                        f"[ANTI-HALUSINASI] Skill dibuang (tidak ditemukan di teks): {skill}"
                    )
            return kept

        return {
            "tech_stack": _filter_list(result.get("tech_stack", []) or []),
            "technical_skill": _filter_list(result.get("technical_skill", []) or []),
            "soft_skill": result.get("soft_skill", []) or [],
        }

    def extract_skills(self, job_description: str, timeout_seconds: int = 45) -> Dict:
        """
        Extract skills dari job description dengan timeout protection
        
        Args:
            job_description: Teks deskripsi pekerjaan
            timeout_seconds: Timeout untuk API call (default 45 detik)
            
        Returns:
            Dictionary dengan format:
            {
                "tech_stack": ["Python", "Java", "SQL", "Docker", "Git", "AWS"],
                "technical_skill": ["Machine Learning", "Data Analysis", "Deep Learning"],
                "soft_skill": ["Communication", "Leadership"]
            }
        """
        if not job_description or len(job_description) < 50:
            return {"tech_stack": [], "technical_skill": [], "soft_skill": []}
        
        prompt = self._create_prompt(job_description)
        
        max_retries = 3
        base_delay = 30  # Start dengan 30 seconds untuk rate limit
        
        for attempt in range(max_retries):
            try:
                # Wrap API call dengan timeout
                result = self._call_groq_with_timeout(
                    prompt=prompt,
                    timeout_seconds=timeout_seconds,
                    attempt=attempt,
                    max_retries=max_retries
                )
                
                if result is not None:
                    # Safety-net anti-halusinasi: buang skill yang tidak
                    # benar-benar ada di teks deskripsi aslinya.
                    return self._filter_grounded(result, job_description)
            except TimeoutError:
                print(f"    [TIMEOUT] attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    delay = base_delay * (3 ** attempt)  # 30, 90, 270 seconds
                    print(f"    [WAIT] {delay} seconds before retry...")
                    time.sleep(delay)
                    continue
                else:
                    print(f"    [ERROR] Max timeout retries reached")
                    return {"tech_stack": [], "technical_skill": [], "soft_skill": []}
            except Exception as e:
                error_msg = str(e)
                
                # Check if rate limit error
                if "429" in error_msg or "rate_limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (3 ** attempt)  # 30, 90, 270 seconds (more aggressive)
                        print(f"    [RATE LIMIT] waiting {delay} seconds...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"    [ERROR] Rate limit exceeded after retries")
                        return {"tech_stack": [], "technical_skill": [], "soft_skill": []}
                
                # Other errors - log and return empty
                print(f"    [ERROR] {str(e)[:60]}")
                return {"tech_stack": [], "technical_skill": [], "soft_skill": []}
        
        return {"tech_stack": [], "technical_skill": [], "soft_skill": []}
    
    def _call_groq_with_timeout(self, prompt: str, timeout_seconds: int, attempt: int, max_retries: int) -> Dict:
        """
        Call Groq API dengan timeout protection menggunakan threading
        
        Args:
            prompt: Prompt untuk AI
            timeout_seconds: Timeout dalam detik
            attempt: Attempt number
            max_retries: Total retries
            
        Returns:
            Parsed result dict atau None jika timeout
        """
        result = {"response": None, "error": None}
        
        def api_call():
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Extract skills from job description and return ONLY valid JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1000,
                    top_p=0.9,
                    timeout=timeout_seconds  # Timeout per request
                )
                result["response"] = response
            except Exception as e:
                result["error"] = e
        
        # Run API call dalam thread dengan timeout
        thread = threading.Thread(target=api_call, daemon=True)
        thread.start()
        thread.join(timeout=timeout_seconds + 5)  # Add buffer
        
        if thread.is_alive():
            # Thread still running - timeout
            print(f"    ⏱️  API call timeout (>{timeout_seconds}s)")
            raise TimeoutError(f"Groq API call timeout after {timeout_seconds} seconds")
        
        if result["error"]:
            raise result["error"]
        
        if result["response"] is None:
            return None
        
        response = result["response"]
        result_text = response.choices[0].message.content.strip()
        
        # Handle empty response
        if not result_text:
            return None
        
        # Bersihkan markdown code blocks
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.startswith("```"):
            result_text = result_text[3:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
        
        result_text = result_text.strip()
        
        if not result_text:
            return None
        
        # Try to find JSON in response (in case of extra text)
        json_start = result_text.find('{')
        json_end = result_text.rfind('}')
        
        if json_start != -1 and json_end != -1 and json_end > json_start:
            result_text = result_text[json_start:json_end+1]
        
        # Parse JSON
        try:
            parsed = json.loads(result_text)
            extracted = {
                "tech_stack": parsed.get("tech_stack", []) or [],
                "technical_skill": parsed.get("technical_skill", []) or [],
                "soft_skill": parsed.get("soft_skill", []) or []
            }
            # Safety-net: pindahkan soft skill yang nyasar ke technical_skill
            return self._reclassify_skills(extracted)
        except json.JSONDecodeError:
            return None

    def extract_skills_batch(self, jobs: List[Dict], max_chars_per_job: int = 1200) -> Dict[int, Dict]:
        """Batch extract: 1 request untuk banyak job.

        Args:
            jobs: List dict minimal: {"id": int, "description": str}
            max_chars_per_job: limit panjang per job agar prompt tidak kebesaran

        Returns:
            Mapping job_id -> {"tech_stack":[], "technical_skill":[], "soft_skill":[]}
        """
        if not jobs:
            return {}

        prompt = self._create_batch_prompt(jobs, max_chars_per_job=max_chars_per_job)

        max_retries = 3
        base_delay = 30

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Return ONLY valid JSON. Do not add markdown or extra text.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=2500,
                    top_p=0.9,
                )

                result_text = response.choices[0].message.content.strip()
                if not result_text:
                    print("    Warning: Empty response from AI (batch)")
                    return {int(j["id"]): {"tech_stack": [], "technical_skill": [], "soft_skill": []} for j in jobs}

                if result_text.startswith("```json"):
                    result_text = result_text[7:]
                if result_text.startswith("```"):
                    result_text = result_text[3:]
                if result_text.endswith("```"):
                    result_text = result_text[:-3]
                result_text = result_text.strip()

                if not result_text:
                    print("    Warning: Empty response after cleaning (batch)")
                    return {int(j["id"]): {"tech_stack": [], "technical_skill": [], "soft_skill": []} for j in jobs}
                
                # Try to find JSON in response (in case of extra text)
                json_start = result_text.find('{')
                json_end = result_text.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    result_text = result_text[json_start:json_end+1]

                try:
                    payload = json.loads(result_text)
                except json.JSONDecodeError:
                    print("    Warning: JSON decode failed (batch), skipping")
                    return {int(j["id"]): {"tech_stack": [], "technical_skill": [], "soft_skill": []} for j in jobs}

                out: Dict[int, Dict] = {}
                for j in jobs:
                    jid = int(j["id"])
                    item = payload.get(str(jid)) if isinstance(payload, dict) else None
                    if not isinstance(item, dict):
                        out[jid] = {"tech_stack": [], "technical_skill": [], "soft_skill": []}
                        continue
                    extracted = {
                        "tech_stack": item.get("tech_stack", []) or [],
                        "technical_skill": item.get("technical_skill", []) or [],
                        "soft_skill": item.get("soft_skill", []) or [],
                    }
                    # Safety-net #1: pindahkan soft skill yang nyasar ke soft_skill
                    extracted = self._reclassify_skills(extracted)
                    # Safety-net #2: buang skill yang tidak benar-benar ada
                    # di teks deskripsi job ini (anti-halusinasi)
                    out[jid] = self._filter_grounded(extracted, j.get("description", ""))
                return out

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate_limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        print(
                            f"    Rate limit hit (batch), waiting {delay} seconds before retry {attempt + 1}/{max_retries}..."
                        )
                        time.sleep(delay)
                        continue
                    return {int(j["id"]): {"tech_stack": [], "technical_skill": [], "soft_skill": []} for j in jobs}

                print(f"Error ekstraksi skill batch: {e}")
                return {int(j["id"]): {"tech_stack": [], "technical_skill": [], "soft_skill": []} for j in jobs}

        return {int(j["id"]): {"tech_stack": [], "technical_skill": [], "soft_skill": []} for j in jobs}
    
    def extract_skills_for_all_jobs(
        self,
        jobs: List[Dict],
        batch_size: int = 5,
        delay_between_batches: float = 5.0,
        max_chars_per_job: int = 1200,
        progress_callback=None,
    ) -> Dict[int, Dict]:
        """
        Proses banyak job (ratusan/ribuan) sekaligus dengan auto-chunking +
        jeda antar batch, supaya gak nubruk rate limit Groq (429 Too Many
        Requests).

        PAKAI METHOD INI (bukan loop manual yang manggil extract_skills_batch
        sendiri di luar), supaya:
        1. Cuma 1 instance Groq client yang dipakai untuk SEMUA job - gak ada
           lagi "[OK] Groq client initialized" berulang-ulang tiap job/batch.
        2. Ada jeda terkontrol antar batch request, bukan ditembak beruntun
           (ini yang bikin 429 muncul terus-terusan).

        Args:
            jobs: List job dict [{"id": int, "description": str}, ...]
            batch_size: jumlah job per 1 API call. Default 5 - lebih aman untuk
                Free tier Groq (TPM cuma 6.000/menit, batch besar bisa langsung
                melebihi itu dalam SATU request saja). Kalau sudah pakai
                Developer tier (nambah kartu kredit -> limit naik 10x), boleh
                dinaikkan ke 10-15.
            delay_between_batches: jeda detik antar batch request. Default 5
                detik. Kalau masih sering 429, naikkan ke 8-10 detik atau
                turunkan batch_size.
            max_chars_per_job: diteruskan ke extract_skills_batch (limit
                panjang deskripsi per job supaya prompt gak kebesaran).
            progress_callback: optional, function(batch_idx, total_batches,
                batch_results) yang dipanggil tiap batch selesai - berguna
                buat nyimpen progress incremental ke database/file, jadi
                kalau proses kepotong di tengah jalan gak perlu ulang dari nol.

        Returns:
            Dict job_id -> {"tech_stack": [...], "technical_skill": [...], "soft_skill": [...]}
        """
        all_results: Dict[int, Dict] = {}
        total_jobs = len(jobs)
        if total_jobs == 0:
            return all_results

        total_batches = (total_jobs + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start = batch_idx * batch_size
            end = min(start + batch_size, total_jobs)
            batch_jobs = jobs[start:end]

            print(f"Batch {batch_idx + 1}/{total_batches} ({len(batch_jobs)} jobs)...")

            batch_results = self.extract_skills_batch(batch_jobs, max_chars_per_job=max_chars_per_job)
            all_results.update(batch_results)

            if progress_callback:
                progress_callback(batch_idx + 1, total_batches, batch_results)

            # Jeda antar batch (skip di batch terakhir) supaya gak nubruk rate limit
            if batch_idx < total_batches - 1:
                time.sleep(delay_between_batches)

        print(f"Selesai! {total_jobs} job diproses dalam {total_batches} batch.")
        return all_results

    def _create_prompt(self, job_description: str) -> str:
        return f"""
Anda adalah sistem ekstraksi skill SUPER TELITI dan AKURAT.

TUJUAN:
Ekstrak SEMUA skill yang benar-benar ada di deskripsi.
JANGAN ADA YANG TERLEWAT.
TAPI JUGA JANGAN MENAMBAHKAN YANG TIDAK ADA.

==================================================
ATURAN ANTI-HALUSINASI (SANGAT PENTING, BACA DULU!)
==================================================
- Ekstrak HANYA skill yang BENAR-BENAR DISEBUTKAN (secara eksplisit, atau
  lewat singkatan/sinonim yang jelas, misal "ML" untuk "Machine Learning")
  di dalam teks deskripsi di bawah.
- DILARANG menambahkan skill hanya karena "biasanya" dibutuhkan untuk posisi
  sejenis. Contoh kesalahan fatal: menambahkan "Python" ke semua lowongan
  Data Scientist/Data Analyst padahal kata "Python" (atau variasinya) TIDAK
  ADA di teks.
- DILARANG menebak tech stack berdasarkan judul pekerjaan, nama perusahaan,
  atau asumsi industri. Satu-satunya sumber kebenaran adalah teks deskripsi
  yang diberikan, bukan pengetahuan umum Anda tentang posisi tsb.
- Sebaliknya, JANGAN sampai ada skill yang JELAS disebutkan di teks tapi
  tidak Anda ekstrak. Baca SELURUH teks dengan teliti, termasuk bagian
  "Requirements", "Qualifications", "Kualifikasi", "Persyaratan", "Nice to
  have", dan "Preferred".
- Kalau ragu apakah sesuatu benar-benar disebutkan di teks: JANGAN
  dimasukkan.

==================================================
DEFINISI KATEGORI (WAJIB DIPATUHI)
==================================================

1. tech_stack (ALAT / TOOLS / TEKNOLOGI KONKRIT)
HANYA yang bisa "dipakai" secara langsung.

CONTOH VALID:
Python, Java, JavaScript, SQL  
PostgreSQL, MySQL, MongoDB  
React, Laravel, Django, Spring Boot  
Docker, Kubernetes, AWS, GCP, Azure  
Git, Jenkins, Kafka, Spark  
TensorFlow, PyTorch, Pandas, NumPy  

JANGAN MASUKKAN:
Development, Programming, API, Testing, System, Backend, Frontend

RULE PENTING:
Jika bukan NAMA TOOL → JANGAN masuk tech_stack

--------------------------------------------------

2. technical_skill (KEMAMPUAN / KONSEP / BIDANG KEAHLIAN TEKNIS)

CONTOH VALID:
Machine Learning  
Data Analysis  
Data Visualization  
Web Development  
Backend Development  
System Design  
API Design  
Microservices Architecture  
ETL / Data Pipeline  
Deep Learning  
Natural Language Processing  
Computer Vision  
CI/CD  
Software Testing  
Statistical Analysis  
Feature Engineering  
Model Deployment  

⚠️ PERINGATAN PENTING ⚠️
JANGAN masukkan soft skills ke technical_skill!

❌ SALAH (ini SOFT SKILL, bukan technical):
- Problem Solving → HARUS di soft_skill
- Analytical Thinking → HARUS di soft_skill
- Critical Thinking → HARUS di soft_skill
- Communication → HARUS di soft_skill
- Leadership → HARUS di soft_skill
- Teamwork → HARUS di soft_skill
- Time Management → HARUS di soft_skill
- Adaptability → HARUS di soft_skill

✅ BENAR (ini TECHNICAL SKILL):
- Data Analysis (kemampuan analisis data)
- Machine Learning (bidang keilmuan)
- Data Visualization (teknik visualisasi)

--------------------------------------------------

3. soft_skill (KEMAMPUAN NON-TEKNIS / INTERPERSONAL)

CONTOH VALID:
Communication  
Leadership  
Teamwork / Collaboration  
Problem Solving  
Critical Thinking  
Analytical Thinking  
Time Management  
Adaptability  
Creativity  
Emotional Intelligence  
Negotiation  
Presentation  
Writing  
Attention to Detail  
Organization  
Conflict Resolution  
Decision Making  
Customer Service  
Interpersonal Skills  
Self Motivation  
Work Ethic  
Stress Management  
Multitasking  

--------------------------------------------------
RULES SUPER KETAT UNTUK MEMBEDAKAN TECHNICAL VS SOFT
--------------------------------------------------

❌ JIKA SKILL INI MASUK KE TECHNICAL_SKILL, SALAH!

| SKILL | SEHARUSNYA | KATEGORI |
|-------|------------|----------|
| Problem Solving | Soft Skill | ❌ BUKAN Technical |
| Analytical Thinking | Soft Skill | ❌ BUKAN Technical |
| Critical Thinking | Soft Skill | ❌ BUKAN Technical |
| Communication | Soft Skill | ❌ BUKAN Technical |
| Leadership | Soft Skill | ❌ BUKAN Technical |
| Teamwork | Soft Skill | ❌ BUKAN Technical |

✅ YANG BENAR UNTUK TECHNICAL_SKILL:
| SKILL | KATEGORI | ALASAN |
|-------|----------|--------|
| Data Analysis | Technical | Kemampuan teknis analisis data |
| Data Visualization | Technical | Teknik visualisasi data |
| Machine Learning | Technical | Bidang keilmuan teknis |
| Statistical Analysis | Technical | Metode statistik teknis |

==================================================
FORMAT WAJIB:
==================================================

{{
  "tech_stack": [],
  "technical_skill": [],
  "soft_skill": []
}}

==================================================
DESKRIPSI PEKERJAAN:
==================================================

{job_description[:3000]}
"""

    def _create_batch_prompt(self, jobs: List[Dict], max_chars_per_job: int = 1200) -> str:
        """Prompt untuk batch extraction - multiple jobs dalam satu request."""
        lines = []
        for j in jobs:
            jid = int(j.get("id"))
            desc = (j.get("description") or "")
            desc = desc.strip().replace("\r\n", "\n")
            if len(desc) > max_chars_per_job:
                desc = desc[:max_chars_per_job]
            lines.append(f"--- LOWONGAN {jid} ---\n{desc}")

        jobs_block = "\n\n".join(lines)

        return f"""Ekstrak semua skill dari SETIAP deskripsi pekerjaan di bawah. Proses mereka secara terpisah.

Klasifikasikan skill ke dalam 3 kategori:

1. tech_stack: ALAT & BAHASA PEMROGRAMAN ("Senjata")
   Bahasa pemrograman, database, framework, platform, tools
   Contoh: Python, Java, PostgreSQL, AWS, Docker, Kubernetes, Git, TensorFlow, React, Django, dll

2. technical_skill: KEMAMPUAN TEKNIS & KONSEP
   Keahlian domain, metodologi, teknik khusus, dan kapabilitas teknis
   Contoh: Data Science, Machine Learning, ETL, Data Analysis, Data Visualization, Deep Learning, NLP, dll
   
   ⚠️ PERINGATAN: JANGAN masukkan soft skills ke sini!
   ❌ Problem Solving → soft_skill
   ❌ Analytical Thinking → soft_skill
   ❌ Critical Thinking → soft_skill
   ❌ Communication → soft_skill
   ❌ Leadership → soft_skill
   ❌ Teamwork → soft_skill
   
   ✅ YANG BENAR:
   Data Analysis → technical_skill
   Data Visualization → technical_skill
   Machine Learning → technical_skill
   Statistical Analysis → technical_skill

3. soft_skill: KEAHLIAN INTERPERSONAL & PERILAKU
   Communication, Leadership, Teamwork, Problem Solving, Critical Thinking, 
   Analytical Thinking, Time Management, Adaptability, Creativity, dll

ATURAN ANTI-HALUSINASI (SANGAT PENTING):
- HANYA ekstrak skill yang BENAR-BENAR DISEBUTKAN di teks lowongan
  bersangkutan (secara eksplisit atau lewat singkatan/sinonim yang jelas).
- DILARANG menambahkan skill hanya karena "biasanya" ada di posisi sejenis
  (contoh kesalahan fatal: menambahkan "Python" untuk lowongan Data
  Scientist padahal kata "Python" tidak ada di teks LOWONGAN itu).
- DILARANG menebak skill berdasarkan judul pekerjaan saja.
- Sebaliknya, baca SETIAP lowongan dengan teliti dari awal sampai akhir
  (termasuk bagian "Requirements"/"Kualifikasi"/"Nice to have") supaya
  TIDAK ADA skill yang jelas disebutkan tapi terlewat.
- Kalau ragu: JANGAN dimasukkan.

ATURAN LAIN:
- Proses SETIAP lowongan secara terpisah (jangan campur skill antar lowongan)
- Normalisasi: "Python Programming" → "Python", "ML" → "Machine Learning"
- Indonesia/English equivalents = SAME SKILL (ekstrak hanya sekali dengan canonical name)
- Hapus duplikasi dalam setiap kategori
- Output harus valid JSON, tanpa markdown

Kembalikan JSON object yang memetakan job_id (sebagai string) ke objek skill:
{{
  "1": {{"tech_stack": [...], "technical_skill": [...], "soft_skill": [...]}},
  "2": {{"tech_stack": [...], "technical_skill": [...], "soft_skill": [...]}},
  ...
}}

LOWONGAN UNTUK DIEKSTRAK:
{jobs_block}"""
    
    def batch_extract(self, job_descriptions: List[str], delay=1) -> List[Dict]:
        """
        Extract skills dari multiple job descriptions
        
        Args:
            job_descriptions: List of job descriptions
            delay: Delay antara request (detik)
            
        Returns:
            List hasil ekstraksi
        """
        results = []
        total = len(job_descriptions)
        
        print(f"Memproses {total} lowongan dengan Groq...")
        
        for idx, desc in enumerate(job_descriptions, 1):
            print(f"  Proses {idx}/{total}...")
            
            result = self.extract_skills(desc)
            results.append(result)
            
            # Tampilkan sample
            total_skills = len(result.get("tech_stack", [])) + len(result.get("soft_skill", []))
            if total_skills > 0:
                print(f"    Ditemukan {total_skills} skill")
            
            if idx < total:
                time.sleep(delay)
        
        print(f"Batch processing selesai!")
        return results


if __name__ == "__main__":
    # Test ekstraksi skill
    sample_job = """
    Senior Data Scientist - AI/ML Team
    
    Requirements:
    - 3+ years experience in Data Science and Machine Learning
    - Strong proficiency in Python programming
    - Deep understanding of Machine Learning algorithms and Deep Learning
    - Hands-on experience with TensorFlow, PyTorch, or Keras
    - Expert in data manipulation using Pandas, NumPy
    - Strong SQL skills and experience with PostgreSQL
    - Experience with cloud platforms (AWS or GCP)
    - Familiar with Docker, Kubernetes, and MLOps tools
    - Experience with Computer Vision or NLP is a plus
    - Strong analytical thinking and problem-solving abilities
    
    Soft Skills:
    - Excellent communication and presentation skills
    - Strong problem-solving abilities
    - Team player with leadership qualities
    - Critical thinking and attention to detail
    """
    
    print("Test Skill Extractor")
    print("=" * 60)
    
    extractor = SkillExtractor()
    result = extractor.extract_skills(sample_job)
    
    print("\nHasil ekstraksi:")
    print(f"Tech Stack ({len(result['tech_stack'])}): {result['tech_stack']}")
    print(f"Technical Skills ({len(result['technical_skill'])}): {result['technical_skill']}")
    print(f"Soft Skills ({len(result['soft_skill'])}): {result['soft_skill']}")
    
    # Validasi (sekarang seharusnya SELALU lolos berkat _reclassify_skills,
    # karena reklasifikasi dijalankan otomatis di dalam extract_skills)
    print("\n✅ VALIDASI KATEGORI:")
    soft_skills_in_technical = []
    for skill in result.get('technical_skill', []):
        skill_lower = skill.lower().strip()
        if any(word in skill_lower for word in ['problem solving', 'analytical thinking', 'critical thinking', 'communication', 'leadership', 'teamwork', 'time management']):
            soft_skills_in_technical.append(skill)
    
    if soft_skills_in_technical:
        print(f"⚠️  MASIH ADA SOFT SKILL DI TECHNICAL: {soft_skills_in_technical}")
    else:
        print("✅ SEMUA SOFT SKILL SUDAH BENAR DI KATEGORI SOFT_SKILL!")