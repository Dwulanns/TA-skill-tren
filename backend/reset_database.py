"""
Reset Database - Keep Keywords, Jobs, Admin, SkillTypes
Delete: Skills, JobSkills, JobAnalysis (reset ID from 1)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_context, engine
from database.models import JobSkill, JobAnalysis, Skill
from sqlalchemy import text

def reset_database():
    """Reset database - delete skills, job_skills, job_analysis"""
    
    print("=" * 70)
    print("🔄 DATABASE RESET")
    print("=" * 70)
    
    with get_db_context() as db:
        # Step 1: Delete from tables with foreign keys (careful order!)
        print("\n🗑️  Deleting data...")
        
        # Delete job_analysis (references jobs)
        job_analysis_count = db.query(JobAnalysis).count()
        print(f"  Deleting {job_analysis_count} job_analysis records...")
        db.query(JobAnalysis).delete()
        db.commit()
        print(f"  ✓ Deleted job_analysis")
        
        # Delete job_skills (pivot table - references jobs & skills)
        job_skills_count = db.query(JobSkill).count()
        print(f"  Deleting {job_skills_count} job_skills records...")
        db.query(JobSkill).delete()
        db.commit()
        print(f"  ✓ Deleted job_skills")
        
        # Delete skills (referenced by job_skills)
        skills_count = db.query(Skill).count()
        print(f"  Deleting {skills_count} skill records...")
        db.query(Skill).delete()
        db.commit()
        print(f"  ✓ Deleted skills")
        
        print(f"\n✅ Data deleted successfully!")
    
    # Step 2: Reset sequences (for PostgreSQL auto-increment)
    print(f"\n🔢 Resetting ID sequences...")
    try:
        with engine.connect() as conn:
            # Reset sequences to 1
            sequences = [
                'job_analysis_id_seq',
                'job_skills_id_seq',
                'skills_id_seq',
            ]
            
            for seq in sequences:
                try:
                    conn.execute(text(f"ALTER SEQUENCE {seq} RESTART WITH 1"))
                    print(f"  ✓ Reset {seq}")
                except Exception as e:
                    print(f"  ⚠️  {seq} not found (OK for SQLite)")
            
            conn.commit()
    except Exception as e:
        print(f"  ℹ️  Sequence reset skipped (SQLite doesn't need it)")
    
    # Step 3: Verify
    print(f"\n✅ Database reset complete!")
    
    with get_db_context() as db:
        from database.models import Keyword, Job, Admin, SkillType
        
        print(f"\n📊 Summary (kept data):")
        print(f"  • Keywords: {db.query(Keyword).count()}")
        print(f"  • Jobs: {db.query(Job).count()}")
        print(f"  • Skill Types: {db.query(SkillType).count()}")
        print(f"  • Admin: {db.query(Admin).count()}")
        
        print(f"\n📊 Summary (deleted data):")
        print(f"  • Skills: {db.query(Skill).count()}")
        print(f"  • JobSkills: {db.query(JobSkill).count()}")
        print(f"  • JobAnalysis: {db.query(JobAnalysis).count()}")
    
    print("\n" + "=" * 70)
    print("✨ Ready for new data!")
    print("=" * 70)

if __name__ == "__main__":
    reset_database()
