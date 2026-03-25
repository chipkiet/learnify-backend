"""
Test script to verify Google OAuth workflow is working properly
Run: python test_google_auth.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.conf import settings
from apps.users.models import AuthProvider

User = get_user_model()

def check_google_config():
    """Check if Google OAuth configuration is complete"""
    print("\n" + "="*60)
    print("🔍 GOOGLE OAUTH CONFIGURATION CHECK")
    print("="*60)
    
    checks = {
        "GOOGLE_CLIENT_ID": bool(settings.GOOGLE_CLIENT_ID),
        "GOOGLE_CLIENT_SECRET": bool(settings.GOOGLE_CLIENT_SECRET),
        "GOOGLE_REDIRECT_URI": bool(settings.GOOGLE_REDIRECT_URI),
        "GOOGLE_LOGIN_REDIRECT_URL": bool(settings.GOOGLE_LOGIN_REDIRECT_URL),
    }
    
    all_good = True
    for key, present in checks.items():
        status = "✅" if present else "❌"
        value = getattr(settings, key, "NOT SET")
        print(f"{status} {key}")
        if present:
            print(f"   → {value[:50]}...")
        else:
            all_good = False
            print(f"   → MISSING! Add to .env file")
    
    return all_good

def check_database():
    """Check if database has any Google OAuth users"""
    print("\n" + "="*60)
    print("📊 DATABASE CHECK")
    print("="*60)
    
    google_users = User.objects.filter(auth_provider=AuthProvider.GOOGLE)
    total_users = User.objects.count()
    
    print(f"Total users: {total_users}")
    print(f"Google OAuth users: {google_users.count()}")
    
    if google_users.exists():
        print("\n✅ Google OAuth users found:")
        for user in google_users:
            print(f"  • {user.email}")
            print(f"    - Full name: {user.full_name}")
            print(f"    - Avatar: {user.avatar[:50]}..." if user.avatar else "    - Avatar: NOT SET")
            print(f"    - Created: {user.created_at}")
    else:
        print("\n⚠️ No Google OAuth users yet (normal for first run)")

def check_endpoints():
    """Check if Google OAuth endpoints are registered"""
    print("\n" + "="*60)
    print("🔗 ENDPOINTS CHECK")
    print("="*60)
    
    from django.urls import reverse
    
    try:
        google_login_url = reverse('google-login')
        google_callback_url = reverse('google-callback')
        profile_url = reverse('profile')
        
        print(f"✅ Google Login Endpoint: /api/auth{google_login_url}")
        print(f"✅ Google Callback Endpoint: /api/auth{google_callback_url}")
        print(f"✅ Profile Endpoint: /api/auth{profile_url}")
    except Exception as e:
        print(f"❌ Error checking endpoints: {e}")

def check_imports():
    """Check if all required modules are available"""
    print("\n" + "="*60)
    print("📦 DEPENDENCIES CHECK")
    print("="*60)
    
    dependencies = {
        'requests': 'For Google API calls',
        'rest_framework_simplejwt': 'For JWT token generation',
        'corsheaders': 'For CORS support',
    }
    
    for package, description in dependencies.items():
        try:
            __import__(package)
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED - {description}")
            print(f"   Run: pip install {package}")

def run_all_checks():
    """Run all checks"""
    print("\n" + "🚀 " * 20)
    print("LEARNIFY GOOGLE OAUTH WORKFLOW TEST")
    print("🚀 " * 20)
    
    try:
        config_ok = check_google_config()
        check_database()
        check_endpoints()
        check_imports()
        
        print("\n" + "="*60)
        print("📝 SUMMARY")
        print("="*60)
        
        if config_ok:
            print("✅ All configurations are set!")
            print("\nNext steps:")
            print("1. Visit: http://localhost:5173/login")
            print("2. Click 'Sign in with Google'")
            print("3. Authenticate with your Google account")
            print("4. Check this script again to verify user was created")
        else:
            print("❌ Some configurations are missing!")
            print("\nTo fix:")
            print("1. Copy .env template from GOOGLE_OAUTH_SETUP.md")
            print("2. Fill in your Google OAuth credentials")
            print("3. Run this script again")
        
        print("\n📖 See GOOGLE_OAUTH_SETUP.md for detailed setup instructions")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_all_checks()
