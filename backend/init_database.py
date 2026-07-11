"""
Master Database & Admin Setup Script
One-stop initialization untuk:
1. Create database tables
2. Seed skill types & keywords
3. Create admin account
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import init_db, get_db_context
from database.models import SkillType, Keyword, Admin
from config_auth import get_password_hash, verify_password

# ============================================================================
# SKILL TYPES
# ============================================================================

SKILL_TYPES = [
    {"name": "tech_stack", "description": "Technologies, tools, platforms: programming languages, frameworks, libraries, databases, cloud services (e.g., Python, TensorFlow, Docker, AWS)"},
    {"name": "technical_skill", "description": "Technical capabilities and methods: Machine Learning, Data Analysis, Deep Learning, NLP, Computer Vision"},
    {"name": "soft_skill", "description": "Non-technical interpersonal skills: Communication, Leadership, Teamwork, Problem Solving"}
]

# ============================================================================
# JOB KEYWORDS
# ============================================================================

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

# ============================================================================
# ADMIN CREDENTIALS
# ============================================================================

ADMIN_EMAIL = "admin@skilltren.com"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123456"


def seed_skill_types(db):
    """Insert default skill types"""
    print("\n🌱 Seeding skill types...")
    
    for skill_type_data in SKILL_TYPES:
        existing = db.query(SkillType).filter(SkillType.name == skill_type_data["name"]).first()
        
        if not existing:
            skill_type = SkillType(**skill_type_data)
            db.add(skill_type)
            print(f"  ✓ Added: {skill_type_data['name']}")
        else:
            print(f"  ⏭  Exists: {skill_type_data['name']}")
    
    db.commit()
    print("✅ Skill types seeded!")


def seed_keywords(db):
    """Insert default job keywords"""
    print("\n📌 Seeding job keywords...")
    
    for keyword_text in JOB_KEYWORDS:
        existing = db.query(Keyword).filter(Keyword.keyword == keyword_text).first()
        
        if not existing:
            keyword = Keyword(keyword=keyword_text)
            db.add(keyword)
            print(f"  ✓ Added: {keyword_text}")
        else:
            print(f"  ⏭  Exists: {keyword_text}")
    
    db.commit()
    print("✅ Keywords seeded!")


def setup_admin(db):
    """Create admin account if not exists, then verify"""
    print("\n👤 Setting up admin account...")
    
    # Check if admin exists (by email or username)
    admin = db.query(Admin).filter(
        (Admin.email == ADMIN_EMAIL) | (Admin.username == ADMIN_USERNAME)
    ).first()
    
    if not admin:
        print(f"  📝 Creating new admin account...")
        
        try:
            # Create new admin
            admin = Admin(
                email=ADMIN_EMAIL,
                username=ADMIN_USERNAME,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                is_active=1
            )
            
            db.add(admin)
            db.commit()
            db.refresh(admin)
            
            print(f"  ✓ Admin created")
        except Exception as e:
            print(f"  ⚠️  Error creating admin: {str(e)}")
            db.rollback()
            # Try to fetch existing
            admin = db.query(Admin).filter(Admin.username == ADMIN_USERNAME).first()
            if admin:
                print(f"  ℹ️  Found existing admin: {admin.email}")
    else:
        print(f"  ⏭  Admin already exists: {admin.email}")
    
    # Verify password
    if admin:
        print(f"\n  🔐 Verifying password...")
        is_valid = verify_password(ADMIN_PASSWORD, admin.password_hash)
        
        if not is_valid:
            print(f"  ⚠️  Password mismatch, fixing...")
            admin.password_hash = get_password_hash(ADMIN_PASSWORD)
            db.commit()
            db.refresh(admin)
        
        print(f"✅ Admin account ready!")
    
    return admin


def main():
    print("=" * 70)
    print("🚀 DATABASE & ADMIN INITIALIZATION")
    print("=" * 70)
    
    # Step 1: Create tables
    print("\n📊 Step 1: Creating database tables...")
    init_db()
    print("✅ Tables created!")
    
    # Step 2: Seed data
    with get_db_context() as db:
        seed_skill_types(db)
        seed_keywords(db)
        admin = setup_admin(db)
    
    # Summary
    print("\n" + "=" * 70)
    print("✨ INITIALIZATION COMPLETE!")
    print("=" * 70)
    
    with get_db_context() as db:
        skill_type_count = db.query(SkillType).count()
        keyword_count = db.query(Keyword).count()
        admin_count = db.query(Admin).count()
        
        print(f"\n📊 Database Summary:")
        print(f"  • Skill types: {skill_type_count}")
        print(f"  • Keywords: {keyword_count}")
        print(f"  • Admin accounts: {admin_count}")
    
    print(f"\n🔐 Admin Credentials:")
    print(f"  • Email: {ADMIN_EMAIL}")
    print(f"  • Password: {ADMIN_PASSWORD}")
    
    print(f"\n🎯 Next steps:")
    print(f"  1. Start backend: python -m uvicorn api.main:app --reload")
    print(f"  2. Start frontend: npm run dev")
    print(f"  3. Login to admin panel with credentials above")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
