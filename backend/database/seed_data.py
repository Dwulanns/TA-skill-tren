"""
Seed initial skill types to database
Run this once after creating tables
NOTE: Use setup_database.py untuk setup lengkap (drop + create + seed)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_context, init_db
from database.models import SkillType, Keyword

# Skill types: tech_stack, technical_skill & soft_skill
SKILL_TYPES = [
    {"name": "tech_stack", "description": "Technologies, tools, platforms: programming languages, frameworks, libraries, databases, cloud services (e.g., Python, TensorFlow, Docker, AWS)"},
    {"name": "technical_skill", "description": "Technical capabilities and methods: Machine Learning, Data Analysis, Deep Learning, NLP, Computer Vision"},
    {"name": "soft_skill", "description": "Non-technical interpersonal skills: Communication, Leadership, Teamwork, Problem Solving"}
]

# Default job keywords
JOB_KEYWORDS = [
    "Data Analyst",
    "Data Scientist",
    "Data Engineer",
    "Data Developer",
    "Data Architect",
    "Data Specialist",
    "Business Intelligence",
    "Machine Learning",
    "AI Engineer",
    "AI Research",
    "AI Scientist",
    "AI Developer",
    "Prompt Engineer",
    "NLP Engineer",
    "Computer Vision",
    "Deep Learning Engineer"
]


def seed_skill_types():
    """Insert default skill types"""
    print("🌱 Seeding skill types...")
    
    with get_db_context() as db:
        for skill_type_data in SKILL_TYPES:
            existing = db.query(SkillType).filter(SkillType.name == skill_type_data["name"]).first()
            
            if not existing:
                skill_type = SkillType(**skill_type_data)
                db.add(skill_type)
                print(f"  ✓ Added: {skill_type_data['name']}")
            else:
                print(f"  ⏭  Exists: {skill_type_data['name']}")
        
        db.commit()
    
    print("✅ Skill types ready!")


def seed_keywords():
    """Insert default job keywords"""
    print("\n Seeding job keywords...")
    
    with get_db_context() as db:
        for keyword_text in JOB_KEYWORDS:
            existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
            
            if not existing:
                keyword = Keyword(keyword=keyword_text)
                db.add(keyword)
                print(f"  ✓ Added: {keyword_text}")
            else:
                print(f"  ⏭  Exists: {keyword_text}")
        
        db.commit()
    
    print("✅ Keywords ready!")


def main():
    print("=" * 70)
    print("DATABASE INITIALIZATION")
    print("=" * 70)
    
    # Create tables
    print("\n📊 Creating database tables...")
    init_db()
    print("✅ Tables created!")
    
    # Seed data
    seed_skill_types()
    seed_keywords()
    
    print("\n" + "=" * 70)
    print("✅ DATABASE READY!")
    print("=" * 70)
    
    # Show summary
    with get_db_context() as db:
        skill_type_count = db.query(SkillType).count()
        keyword_count = db.query(Keyword).count()
        
        print(f"\n Summary:")
        print(f"  • Skill types: {skill_type_count}")
        print(f"  • Keywords: {keyword_count}")
    
    print("\n✅ Ready to scrape jobs!")
    print("   Run: python backend\\scraper\\main_scraper.py")


if __name__ == "__main__":
    main()
