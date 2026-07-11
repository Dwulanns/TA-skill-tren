"""
Verify Admin Account and Debug Login
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection import get_db_context
from database.models import Admin
from config_auth import get_password_hash, verify_password

def verify_admin():
    """Verify admin account exists and test password"""
    
    email = "admin@skilltren.com"
    password = "admin123456"
    
    print("=" * 70)
    print("ADMIN ACCOUNT VERIFICATION")
    print("=" * 70)
    
    with get_db_context() as db:
        # Check if admin exists
        admin = db.query(Admin).filter(Admin.email == email).first()
        
        if not admin:
            print(f"\n❌ Admin NOT found in database!")
            print(f"   Email: {email}")
            print(f"\n📋 Available admins in database:")
            all_admins = db.query(Admin).all()
            if all_admins:
                for a in all_admins:
                    print(f"   - {a.email} (username: {a.username}, active: {a.is_active})")
            else:
                print("   (No admins found)")
            return False
        
        print(f"\n✅ Admin found in database!")
        print(f"   Email: {admin.email}")
        print(f"   Username: {admin.username}")
        print(f"   Is Active: {admin.is_active}")
        print(f"   Password Hash: {admin.password_hash[:50]}...")
        
        # Test password verification
        print(f"\n🔐 Testing password verification...")
        print(f"   Provided password: {password}")
        print(f"   Testing with verify_password()...")
        
        is_valid = verify_password(password, admin.password_hash)
        print(f"   Result: {is_valid}")
        
        if is_valid:
            print(f"\n✅ Password verification PASSED!")
            print(f"   Login should work!")
        else:
            print(f"\n❌ Password verification FAILED!")
            print(f"   The stored password hash doesn't match the provided password")
            
            # Try re-hashing and storing
            print(f"\n🔧 Attempting to fix: re-hash and update password...")
            new_hash = get_password_hash(password)
            admin.password_hash = new_hash
            db.commit()
            db.refresh(admin)
            
            # Test again
            is_valid = verify_password(password, admin.password_hash)
            if is_valid:
                print(f"✅ Password fix successful!")
            else:
                print(f"❌ Password fix failed!")
        
        return is_valid

if __name__ == "__main__":
    success = verify_admin()
    print("=" * 70)
    if success:
        print("✅ Admin account is ready for login!")
    else:
        print("⚠️  There's an issue with the admin account")
    print("=" * 70)
