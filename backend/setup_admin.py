"""
Setup Admin Account
Run this script to create the first admin account
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_context
from database.models import Admin
from config_auth import get_password_hash

def create_admin():
    """Create admin account"""
    
    # Default admin credentials
    email = "admin@skilltren.com"
    username = "admin"
    password = "admin123456"
    
    with get_db_context() as db:
        # Check if admin already exists
        existing = db.query(Admin).filter(Admin.email == email).first()
        
        if existing:
            print(f"✅ Admin already exists!")
            print(f"   Email: {existing.email}")
            print(f"   Username: {existing.username}")
            print(f"   Is Active: {existing.is_active}")
            return
        
        # Create new admin
        admin = Admin(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            is_active=1
        )
        
        db.add(admin)
        db.commit()
        db.refresh(admin)
        
        print("✅ Admin account created successfully!")
        print(f"   Email: {email}")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print("\n🔐 Use these credentials to login in the admin panel")

if __name__ == "__main__":
    print("=" * 60)
    print("ADMIN ACCOUNT SETUP")
    print("=" * 60)
    create_admin()
    print("=" * 60)
