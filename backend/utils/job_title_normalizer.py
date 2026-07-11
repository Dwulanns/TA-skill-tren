"""
Job Title Normalization & Keyword Matching System

Architecture:
- JobStatus: Enumeration for matching results
- JobTitleNormalizer: Main orchestrator for title normalization

Features:
- Clean job title (remove seniority levels and location info)
- Flexible keyword matching with aliases
- Priority filtering to exclude false positives
- Database-driven keyword matching (not hardcoded)
- Return matched keyword_id (not category name)

Example:
    normalizer = JobTitleNormalizer()
    result = normalizer.normalize("Senior Data Scientist - Jakarta")
    # Returns: {
    #   'status': 'accepted',
    #   'job_title_clean': 'Data Scientist',
    #   'keyword_id': 5
    # }
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Any
from enum import Enum


class JobStatus(str, Enum):
    """Enumeration for job matching results"""
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXCLUDED = "excluded"


class JobTitleNormalizer:
    # Seniority levels yang harus dihapus
    SENIORITY_LEVELS = {
        'junior', 'senior', 'lead', 'intern',
        'staff', 'associate', 'manager', 'director',
        'principal', 'head', 'chief', 'expert',
        'specialist', 'officer', 'sr', 'jr'
    }
    
    # Suffix yang harus dihapus (regex patterns)
    SUFFIX_PATTERNS = [
        r'\s*-\s*(remote|contract|full.?time|part.?time|hybrid|onsite|wfo).*$',
        r'\s*\(.*?(remote|contract|full.?time|part.?time|hybrid|onsite)\.*\).*$',
        r'\s*\[.*\].*$',
        r',\s*(remote|relocation).*$'
    ]
    
    # Priority filter - jika ditemukan, REJECT walaupun ada keyword
    PRIORITY_REJECT_KEYWORDS = [
        'software engineer', 'frontend', 'backend', 'fullstack',
        'android', 'ios', 'mobile', 'web developer',
        'devops', 'qa engineer', 'quality assurance',
        'sales', 'marketing', 'business development',
        'hr ', 'human resource', 'accounting',
        'electrical engineer', 'civil engineer', 'mechanical engineer',
        'driver', 'warehouse'
    ]
    
    # Valid keywords para Data & AI - dengan banyak alias
    VALID_KEYWORDS = {
        'data analyst': ['data analyst', 'analyst data', 'data analytics', 'data reporting', 'analytics analyst', 
                         'dashboard analyst', 'data modeling', 
                         'data quality', 'data governance', 'data processing'],
        'business intelligence': ['bi analyst', 'business intelligence', 'bi engineer', 'business inteligence'],
        'data scientist': ['data scientist', 'scientist data', 'machine learning', 'ml engineer', 'ml specialist', 
                          'predictive analytics', 'statistical modeling', 'data science'],
        'data engineer': ['data engineer', 'engineer data', 'data pipeline', 'data warehouse', 'etl', 'etl developer', 
                         'big data engineer', 'data architect'],
        'ai engineer': ['ai engineer', 'artificial intelligence', 'ai specialist', 'ai developer', 'ai scientist', 
                       'ai research', 'ai/ml'],
        'nlp engineer': ['nlp', 'natural language', 'nlp engineer', 'nlp specialist'],
        'computer vision': ['computer vision', 'cv engineer', 'vision engineer'],
        'deep learning': ['deep learning', 'deep learning engineer'],
        'data developer': ['data developer'],
        'prompt engineer': ['prompt engineer', 'prompt specialist']
    }
    
    # Lokasi normalisasi mapping - prioritas: kota > province > Other
    # Mapping untuk cities yang valid
    CITIES = {
        'jakarta', 'bandung', 'surabaya', 'malang', 'medan',
        'makassar', 'palembang', 'semarang', 'yogyakarta', 'solo',
        'bogor', 'depok', 'tangerang', 'bekasi', 'sidoarjo',
        'gresik', 'pasuruan', 'batu', 'kudus', 'pekalongan',
        'tegal', 'kota lama', 'karawang', 'subang', 'cilegon',
        'serang', 'cirebon', 'magelang', 'salatiga', 'klaten',
        'boyolali', 'sukoharjo', 'purworejo', 'wonosobo', 'kebumen',
        'cilacap', 'bumiayu', 'brebes', 'purwokerto', 'banyumas',
        'banjarmasin', 'balikpapan', 'pontianak', 'denpasar', 'ubud'
    }
    
    # Lokasi normalisasi mapping - untuk province dan special cases
    LOCATION_MAPPING = {
        # Cities (prioritas tertinggi)
        'jakarta': 'Jakarta',
        'bandung': 'Bandung',
        'surabaya': 'Surabaya',
        'malang': 'Malang',
        'medan': 'Medan',
        'makassar': 'Makassar',
        'palembang': 'Palembang',
        'semarang': 'Semarang',
        'yogyakarta': 'Yogyakarta',
        'solo': 'Solo',
        'bogor': 'Bogor',
        'depok': 'Depok',
        'tangerang': 'Tangerang',
        'bekasi': 'Bekasi',
        'sidoarjo': 'Sidoarjo',
        'gresik': 'Gresik',
        'pasuruan': 'Pasuruan',
        'denpasar': 'Denpasar',
        'ubud': 'Ubud',
        'banjarmasin': 'Banjarmasin',
        'balikpapan': 'Balikpapan',
        'pontianak': 'Pontianak',
        
        # Provinces (prioritas kedua)
        'jawa barat': 'Jawa Barat',
        'jawa timur': 'Jawa Timur',
        'jawa tengah': 'Jawa Tengah',
        'sumatera utara': 'Sumatera Utara',
        'sumatera selatan': 'Sumatera Selatan',
        'kalimantan': 'Kalimantan',
        'sulawesi': 'Sulawesi',
        'bali': 'Bali',
        'papua': 'Papua',
        
        # Regional references
        'indonesia': 'Indonesia',
        'nationwide': 'Indonesia',
        
        # Remote options
        'remote': 'Remote',
        'work from home': 'Remote',
        'wfh': 'Remote',
    }
    
    def __init__(self):
        """Initialize normalizer - compile regex patterns"""
        self.suffix_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.SUFFIX_PATTERNS]
    
    def clean_title(self, title: str) -> str:
        """
        Clean job title - hapus level, suffix, capitalize
        
        Example:
        "Senior Data Scientist - Remote (Contract)" → "Data Scientist"
        "Junior Machine Learning Engineer (Full Time)" → "Machine Learning Engineer"
        
        Args:
            title: Original job title
            
        Returns:
            Cleaned job title
        """
        if not title:
            return ""
        
        # Convert to lowercase untuk processing
        cleaned = title.strip().lower()
        
        # Hapus suffix patterns
        for pattern in self.suffix_patterns:
            cleaned = pattern.sub('', cleaned)
        
        # Hapus level di awal atau diantara words
        words = cleaned.split()
        cleaned_words = []
        
        for word in words:
            # Hapus level keywords
            word_clean = word.replace(',', '').replace('(', '').replace(')', '')
            if word_clean not in self.SENIORITY_LEVELS:
                cleaned_words.append(word)
        
        cleaned = ' '.join(cleaned_words).strip()
        
        # Cleanup extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Title case with special handling
        return self._title_case(cleaned)
    
    def _title_case(self, text: str) -> str:
        """Custom title case untuk handle special cases"""
        words = text.split()
        result = []
        
        for word in words:
            # Special case seperti "ML", "AI", "NLP"
            if word.upper() in ['ML', 'AI', 'NLP', 'ETL', 'BI', 'CV']:
                result.append(word.upper())
            else:
                result.append(word.capitalize())
        
        return ' '.join(result)
    
    def is_excluded(self, title: str) -> bool:
        """
        Check apakah job title harus di-EXCLUDE
        Menggunakan PRIORITY REJECT KEYWORDS
        
        Example:
        "Backend Engineer" → True (excluded)
        "Data Backend" → False (not excluded)
        
        Args:
            title: Job title to check
            
        Returns:
            True if should be excluded, False otherwise
        """
        title_lower = title.lower()
        
        for reject_keyword in self.PRIORITY_REJECT_KEYWORDS:
            # Exact match atau awal string (untuk "hr ", "software engineer")
            if title_lower.startswith(reject_keyword):
                return True
            # Atau exact word match
            if f' {reject_keyword}' in f' {title_lower}':
                return True
        
        return False
    
    def match_keyword(self, title: str, db_keywords: Optional[List[Dict[str, Any]]] = None) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Match job title dengan keywords dari database
        
        FLEXIBLE MATCHING:
        - "Senior Data Engineer" matches "Data Engineer" ✔
        - "Data Engineer PT ABC" matches "Data Engineer" ✔
        - All words dalam keyword HARUS ada di title
        - Case insensitive matching
        - Ordered by keyword length (longest first) untuk specificity
        
        Args:
            title: Job title untuk di-match
            db_keywords: List of dicts dengan {'id', 'keyword'} dari database
            
        Returns:
            Tuple (matched: bool, keyword_id: int or None, matched_keyword: str or None)
        """
        if not db_keywords:
            return (False, None, None)
        
        title_lower = title.lower()
        
        # Sort by keyword length (longest first)
        sorted_kw = sorted(db_keywords, key=lambda x: len(x['keyword']), reverse=True)
        
        for kw in sorted_kw:
            keyword_lower = kw['keyword'].lower()
            keyword_words = keyword_lower.split()
            all_words_match = all(word in title_lower for word in keyword_words)
            
            if all_words_match:
                return (True, kw['id'], kw['keyword'])
        
        return (False, None, None)
    
    def normalize(self, 
                  job_title: str,
                  db_keywords: Optional[List[Dict[str, Any]]] = None) -> Dict:
        """
        Normalize & validate job title lengkap
        
        Args:
            job_title: Original job title
            db_keywords: List of {'id', 'keyword'} dari database
        
        Returns:
            Dict dengan fields:
            - job_title_original: Original title
            - job_title_clean: Cleaned title 
            - keyword_id: ID dari keyword yang match (None jika tidak accepted)
            - matched_keyword: Keyword text yang match (None jika tidak accepted)
            - status: 'accepted' | 'rejected' | 'excluded'
            - reason: Reason jika status != accepted
        """
        clean = self.clean_title(job_title)
        
        # Check jika excluded first
        if self.is_excluded(clean):
            return {
                'job_title_original': job_title,
                'job_title_clean': clean,
                'keyword_id': None,
                'matched_keyword': None,
                'status': JobStatus.EXCLUDED,
                'reason': 'Termasuk priority reject keywords'
            }
        
        # Try match dengan keywords
        is_matched, kw_id, matched_keyword = self.match_keyword(clean, db_keywords)
        
        if is_matched:
            return {
                'job_title_original': job_title,
                'job_title_clean': clean,
                'keyword_id': kw_id,
                'matched_keyword': matched_keyword,
                'status': JobStatus.ACCEPTED,
                'reason': None
            }
        else:
            return {
                'job_title_original': job_title,
                'job_title_clean': clean,
                'keyword_id': None,
                'matched_keyword': None,
                'status': JobStatus.REJECTED,
                'reason': 'Tidak cocok dengan keywords di database'
            }
    
    def normalize_location(self, location: str) -> str:
        """
        Normalisasi lokasi dengan prioritas: Kota > Province > Other
        
        Example:
        "Surabaya, East Java, Indonesia" → "Surabaya"
        "Jakarta, Indonesia" → "Jakarta"
        "Remote" → "Remote"
        "Bandung, Jawa Barat" → "Bandung"
        "Medan, Sumatera Utara" → "Medan"
        "Unknown Place" → "Other"
        
        Args:
            location: Original location string
            
        Returns:
            Normalized location (City name first, then province, then Other)
        """
        if not location:
            return "Other"
        
        location_lower = location.lower()
        
        # Check untuk remote first
        if any(word in location_lower for word in ['remote', 'work from home', 'wfh']):
            return "Remote"
        
        # Extract possible city name (usually first word atau before comma)
        city_candidate = location_lower.split(',')[0].strip()
        
        # Check apakah itu valid city
        if city_candidate in self.CITIES:
            # Return dengan proper casing
            for city_key, city_val in self.LOCATION_MAPPING.items():
                if city_key == city_candidate:
                    return city_val
        
        # Check setiap mapping (untuk province dan special cases)
        for keyword, normalized in self.LOCATION_MAPPING.items():
            if keyword in location_lower:
                return normalized
        
        # Fallback
        return "Other"


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

def example_usage():
    """Contoh penggunaan JobTitleNormalizer"""
    
    normalizer = JobTitleNormalizer()
    
    # Test cases
    test_titles = [
        "Senior Data Scientist - Remote",
        "Junior Machine Learning Engineer (Contract)",
        "Data Engineer (Full Time)",
        "Backend Engineer",
        "Software Engineer - Data",
        "Machine Learning Engineer",
        "AI Engineer (Relocation provided)",
        "NLP Specialist Lead",
        "Data Analyst, Senior Level",
        "Business Intelligence Analyst",
        "Frontend Developer",
        "AI ML Engineer (Computer Vision)",
        "Data Support Operational Staff",
        "Data Annotator",
        "Full-Time Digital Analyst",
    ]
    
    print("\n" + "="*80)
    print("JOB TITLE NORMALIZATION & FILTERING SYSTEM")
    print("="*80)
    
    accepted_count = 0
    rejected_count = 0
    excluded_count = 0
    
    for title in test_titles:
        result = normalizer.normalize(title)
        
        status = result['status']
        if status == JobStatus.ACCEPTED:
            accepted_count += 1
            symbol = "✅"
        elif status == JobStatus.EXCLUDED:
            excluded_count += 1
            symbol = "🚫"
        else:
            rejected_count += 1
            symbol = "❌"
        
        print(f"\n{symbol} {status.upper()}")
        print(f"   Original:  {result['job_title_original']}")
        print(f"   Clean:     {result['job_title_clean']}")
        if result['job_category']:
            print(f"   Category:  {result['job_category']}")
        if result['reason']:
            print(f"   Reason:    {result['reason']}")
    
    print("\n" + "="*80)
    print("SUMMARY:")
    print(f"  ✅ Accepted:  {accepted_count}")
    print(f"  ❌ Rejected:  {rejected_count}")
    print(f"  🚫 Excluded:  {excluded_count}")
    print(f"  Total:     {len(test_titles)}")
    print("="*80 + "\n")
    
    # Location normalization examples
    print("\nLOCATION NORMALIZATION EXAMPLES:")
    print("-" * 80)
    
    test_locations = [
        "Surabaya, East Java, Indonesia",
        "Jakarta, Indonesia",
        "Remote",
        "Bandung, Jawa Barat",
        "Medan, Sumatera Utara",
        "Unknown Place",
    ]
    
    for loc in test_locations:
        normalized = normalizer.normalize_location(loc)
        print(f"  {loc:40} → {normalized}")
    
    print("-" * 80 + "\n")


if __name__ == "__main__":
    example_usage()
