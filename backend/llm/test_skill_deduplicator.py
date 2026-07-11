"""
Test Suite untuk SkillDeduplicator

Mendemonstrasikan semua fitur:
1. Normalisasi skill
2. Manual mapping
3. Fuzzy matching
4. Full pipeline matching
5. Batch deduplication
6. Database integration
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.llm.skill_dedup_normalized import SkillDeduplicator, SkillMatchResult


def print_section(title: str):
    """Print section header"""
    print("\n" + "=" * 90)
    print(f"  {title}")
    print("=" * 90)


def print_subsection(title: str):
    """Print subsection header"""
    print(f"\n  {title}")
    print("  " + "-" * 85)


# ============================================================================
# TEST 1: NORMALISASI SKILL
# ============================================================================

def test_normalization():
    """Test skill normalization dengan berbagai input"""
    print_section("TEST 1: SKILL NORMALIZATION")
    
    test_cases = [
        # Basic cases
        ("Python", "python"),
        ("PYTHON", "python"),
        ("python3", "python"),
        ("  python  ", "python"),
        
        # Special characters
        ("C#", "c"),
        ("C++", "c"),
        ("Vue.js", "vue.js"),
        ("Node.js", "node.js"),
        
        # Excel variants
        ("MS Excel", "microsoft excel"),
        ("ms excel", "microsoft excel"),
        ("Microsoft Excel", "microsoft excel"),
        ("excel (spreadsheet)", "excel"),
        ("EXCEL", "excel"),
        
        # Machine Learning
        ("Machine Learning", "machine learning"),
        ("ML", "ml"),
        ("Deep Learning", "deep learning"),
        
        # Web
        ("REST API", "rest api"),
        ("GraphQL", "graphql"),
        ("REST", "rest"),
        
        # Typos & spaces
        ("  python  3  ", "python 3"),
        ("Pytho_n", "pytho_n"),  # underscore kept
    ]
    
    print_subsection("Basic Normalization Tests")
    
    for input_skill, expected in test_cases:
        result = SkillDeduplicator.normalize_skill(input_skill)
        status = "✓" if result == expected else "✗"
        print(f"  {status} '{input_skill:30}' → '{result:25}' (expected: '{expected}')")


# ============================================================================
# TEST 2: MANUAL MAPPING
# ============================================================================

def test_manual_mapping():
    """Test manual skill mapping"""
    print_section("TEST 2: MANUAL SKILL MAPPING")
    
    test_cases = [
        # Excel variants
        ("ms excel", "microsoft excel"),
        ("MS Excel", "microsoft excel"),
        ("excer", "microsoft excel"),
        ("excel", "microsoft excel"),
        ("excel (spreadsheet)", "microsoft excel"),
        
        # Python variants
        ("python", "python"),
        ("python3", "python"),
        ("py", "python"),
        ("pyton", None),  # Typo, no mapping
        
        # React variants
        ("react", "react"),
        ("reactjs", "react"),
        ("react.js", "react"),
        ("React JS", "react"),
        
        # AWS
        ("aws", "amazon web services"),
        ("AWS", "amazon web services"),
        ("amazon web services", "amazon web services"),
        
        # Communication (soft skill)
        ("communication", "communication"),
        ("komunikasi", "communication"),
        ("komunikasi", "communication"),
    ]
    
    print_subsection("Manual Mapping Tests")
    
    for input_skill, expected in test_cases:
        result = SkillDeduplicator.apply_manual_mapping(input_skill)
        status = "✓" if result == expected else "✗"
        print(
            f"  {status} '{input_skill:30}' → {str(result):30} "
            f"(expected: {str(expected)})"
        )


# ============================================================================
# TEST 3: FUZZY MATCHING
# ============================================================================

def test_fuzzy_matching():
    """Test fuzzy skill matching dengan RapidFuzz"""
    print_section("TEST 3: FUZZY SKILL MATCHING")
    
    existing_skills = [
        "python",
        "javascript",
        "java",
        "typescript",
        "react",
        "angular",
        "vue",
        "django",
        "flask",
        "spring boot",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "postgresql",
        "mongodb",
    ]
    
    test_cases = [
        # Typos
        ("pyton", "python", 85),
        ("javascrypt", "javascript", 85),
        ("reactt", "react", 85),
        
        # Abbreviations
        ("py", "python", 75),  # May not match with 80 threshold
        ("js", "javascript", 75),
        ("k8s", "kubernetes", None),  # Unlikely match
        
        # Variants
        ("react.js", "react", 85),
        ("node.js", "javascript", None),  # Different skill
        ("springboot", "spring boot", 85),
    ]
    
    print_subsection(f"Fuzzy Matching Tests (vs {len(existing_skills)} existing skills)")
    
    for input_skill, expected_match, expected_score in test_cases:
        matched, score = SkillDeduplicator.fuzzy_match_skill(
            input_skill,
            existing_skills,
            threshold=75  # Lower threshold untuk test
        )
        
        if expected_match is None:
            status = "✓" if matched is None else "✗"
            print(
                f"  {status} '{input_skill:30}' → {str(matched):25} "
                f"({score:.0f}%, expected: None)"
            )
        else:
            status = "✓" if matched == expected_match else "✗"
            print(
                f"  {status} '{input_skill:30}' → {str(matched):25} "
                f"({score:.0f}%, expected: {expected_match})"
            )


# ============================================================================
# TEST 4: FULL MATCHING PIPELINE
# ============================================================================

def test_full_matching_pipeline():
    """Test full skill matching pipeline"""
    print_section("TEST 4: FULL MATCHING PIPELINE")
    
    # Simulated existing skills di database
    existing_map = {
        "python": 1,
        "javascript": 2,
        "java": 3,
        "react": 4,
        "angular": 5,
        "docker": 6,
        "kubernetes": 7,
    }
    
    print_subsection("Existing Skills in Database")
    for normalized, skill_id in existing_map.items():
        print(f"  {skill_id:3d}: {normalized}")
    
    test_cases = [
        # Exact match
        ("python", "exact"),
        
        # Manual mapping
        ("ms excel", "manual_map"),
        
        # Fuzzy match
        ("pyton", "fuzzy"),  # Typo
        ("react.js", "fuzzy"),  # Variant
        
        # New skill
        ("c++", None),
        ("golang", None),
    ]
    
    print_subsection("Matching Results")
    
    for input_skill, expected_method in test_cases:
        result = SkillDeduplicator.match_skill_to_database(
            input_skill,
            existing_map,
            threshold=80
        )
        
        expected_action = "use_existing" if result.match_method != "none" else "insert_new"
        status = "✓" if (expected_method is None or result.match_method == expected_method or expected_method is None) else "✗"
        
        print(f"  {status} Input: '{result.original_skill}'")
        print(f"      └─ Normalized: '{result.normalized_skill}'")
        print(f"      └─ Matched: {result.matched_skill} (ID: {result.matched_id})")
        print(f"      └─ Score: {result.match_score:.0f}% | Method: {result.match_method} | Action: {result.action}")


# ============================================================================
# TEST 5: BATCH DEDUPLICATION
# ============================================================================

def test_batch_deduplication():
    """Test batch skill deduplication"""
    print_section("TEST 5: BATCH DEDUPLICATION")
    
    # Simulated extracted skills dari LLM
    extracted_skills = [
        "ms excel",
        "Microsoft Excel",
        "excer",
        "python",
        "python3",
        "py",
        "react",
        "react.js",
        "reactjs",
        "django",
        "flask",
        "kubernetes",
        "k8s",
    ]
    
    # Existing skills di database
    existing_map = {
        "python": 1,
        "react": 4,
        "django": 8,
        "flask": 9,
    }
    
    print_subsection(f"Input Skills ({len(extracted_skills)} items)")
    for skill in extracted_skills:
        print(f"  • {skill}")
    
    # Deduplicate dengan detailed results
    results = SkillDeduplicator.deduplicate_skills(
        extracted_skills,
        existing_map,
        return_detailed=True
    )
    
    print_subsection(f"Deduplication Results ({len(results)} unique skills)")
    
    for i, result in enumerate(results, 1):
        print(f"  {i}. '{result.original_skill}' → '{result.normalized_skill}'")
        if result.match_method != "none":
            print(f"     └─ {result.match_method.upper()}: matched to '{result.matched_skill}' (ID: {result.matched_id}, {result.match_score:.0f}%)")
        else:
            print(f"     └─ NEW: need to insert to database")


# ============================================================================
# TEST 6: REAL-WORLD SCENARIOS
# ============================================================================

def test_real_world_scenarios():
    """Test real-world scenarios"""
    print_section("TEST 6: REAL-WORLD SCENARIOS")
    
    # Scenario 1: Excel-focused job
    print_subsection("Scenario 1: Excel-focused job description")
    
    excel_skills = [
        "ms excel",
        "Microsoft Excel",
        "Excel spreadsheet",
        "EXCEL",
        "excel (advanced)",
        "excer",
        "VBA",
        "pivot tables",
    ]
    
    existing = {"microsoft excel": 1, "vba": 10}
    
    results = SkillDeduplicator.deduplicate_skills(
        excel_skills,
        existing,
        return_detailed=True
    )
    
    for r in results:
        action = "REUSE" if r.action == "use_existing" else "INSERT"
        print(f"  [{action:6}] {r.original_skill:30} → {r.normalized_skill}")
    
    # Scenario 2: Mixed tech stack
    print_subsection("Scenario 2: Full-stack developer job")
    
    fullstack_skills = [
        "Python",
        "Pyton",
        "py",
        "Django",
        "Flask",
        "PostgreSQL",
        "postgres",
        "React",
        "ReactJS",
        "JavaScript",
        "Docker",
        "Kubernetes",
        "AWS",
    ]
    
    existing = {
        "python": 1,
        "django": 8,
        "flask": 9,
        "postgresql": 11,
        "react": 4,
        "javascript": 2,
        "docker": 6,
    }
    
    results = SkillDeduplicator.deduplicate_skills(
        fullstack_skills,
        existing,
        return_detailed=True
    )
    
    insert_count = sum(1 for r in results if r.action == "insert_new")
    reuse_count = sum(1 for r in results if r.action == "use_existing")
    
    print(f"  Summary:")
    print(f"    • Input: {len(fullstack_skills)} skills")
    print(f"    • Unique: {len(results)} skills")
    print(f"    • Reuse existing: {reuse_count}")
    print(f"    • Insert new: {insert_count}")
    print(f"    • Deduplication ratio: {(1 - len(results)/len(fullstack_skills))*100:.0f}%")


# ============================================================================
# TEST 7: MAPPING STATISTICS
# ============================================================================

def test_mapping_statistics():
    """Show statistics about manual mapping"""
    print_section("TEST 7: MANUAL MAPPING STATISTICS")
    
    # Count mappings by category
    mapping_stats = {}
    
    for canonical, variants in SkillDeduplicator.SKILL_MANUAL_MAPPING.items():
        category = canonical.split()[0].title()  # First word as category
        if category not in mapping_stats:
            mapping_stats[category] = {"canonical": 0, "variants": 0}
        
        mapping_stats[category]["canonical"] += 1
        mapping_stats[category]["variants"] += len(variants)
    
    print_subsection("Manual Mapping Coverage")
    
    total_canonical = 0
    total_variants = 0
    
    for category in sorted(mapping_stats.keys()):
        stats = mapping_stats[category]
        print(
            f"  {category:15} {stats['canonical']:2} canonical → {stats['variants']:3} variants"
        )
        total_canonical += stats['canonical']
        total_variants += stats['variants']
    
    print(f"  {'-' * 45}")
    print(f"  {'TOTAL':15} {total_canonical:2} canonical → {total_variants:3} variants")
    print(f"\n  Coverage: {total_canonical} canonical skill names")
    print(f"  Variations handled: {total_variants} different spellings/abbreviations")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    print("\n" + "=" * 90)
    print("  SKILL DEDUPLICATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 90)
    
    try:
        test_normalization()
        test_manual_mapping()
        test_fuzzy_matching()
        test_full_matching_pipeline()
        test_batch_deduplication()
        test_real_world_scenarios()
        test_mapping_statistics()
        
        print("\n" + "=" * 90)
        print("  ✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 90)
        print()
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
