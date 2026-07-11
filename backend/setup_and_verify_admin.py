"""
Setup and Verify Admin Account - Single Script
Automatically creates admin if doesn't exist, then verifies the account
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_context
from database.models import Admin
from config_auth import get_password_hash, verify_password

def setup_and_verify_admin():
    """Create admin account if not exists, then verify it"""
    
    email = "admin@skilltren.com"
    username = "admin"
    password = "admin123456"
    
    print("=" * 70)
    print("ADMIN ACCOUNT SETUP & VERIFICATION")
    print("=" * 70)
    
    with get_db_context() as db:
        # Check if admin exists
        admin = db.query(Admin).filter(Admin.email == email).first()
        
        if not admin:
            print(f"\n📝 Admin tidak ditemukan. Membuat admin baru...")
            
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
            
            print(f"✅ Admin account berhasil dibuat!")
            print(f"   Email: {email}")
            print(f"   Username: {username}")
            print(f"   Password: {password}")
        else:
            print(f"\n✅ Admin sudah ada di database!")
            print(f"   Email: {admin.email}")
            print(f"   Username: {admin.username}")
        
        # Verify the account
        print(f"\n🔐 Verifikasi password...")
        print(f"   Testing password verification...")
        
        is_valid = verify_password(password, admin.password_hash)
        
        if is_valid:
            print(f"✅ Password verification PASSED!")
            print(f"\n✨ Admin account siap untuk login!")
            print(f"   Login credentials:")
            print(f"   - Email: {email}")
            print(f"   - Password: {password}")
            return True
        else:
            print(f"❌ Password verification FAILED!")
            print(f"   Attempting to fix: re-hash and update password...")
            
            # Fix password
            new_hash = get_password_hash(password)
            admin.password_hash = new_hash
            db.commit()
            db.refresh(admin)
            
            # Test again
            is_valid = verify_password(password, admin.password_hash)
            if is_valid:
                print(f"✅ Password fix successful!")
                print(f"\n✨ Admin account siap untuk login!")
                return True
            else:
                print(f"❌ Password fix failed!")
                return False

if __name__ == "__main__":
    success = setup_and_verify_admin()
    print("=" * 70)
    if success:
        print("✅ Setup Complete! Backend sudah siap.")
    else:
        print("⚠️  Ada masalah dengan admin account")
    print("=" * 70)
