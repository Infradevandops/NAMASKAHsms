#!/bin/bash
# Debug TextVerified Initialization

SERVER="root@169.255.57.57"

echo "🔍 Debugging TextVerified Initialization..."
echo "==========================================="

# Test 1: Check library import
echo "📦 Test 1: Can Python import textverified?"
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms
source .venv/bin/activate
python3 << 'PYEOF'
try:
    import textverified
    print("✅ textverified module imported successfully")
    print(f"   Version: {textverified.__version__ if hasattr(textverified, '__version__') else 'unknown'}")
except ImportError as e:
    print(f"❌ Failed to import textverified: {e}")
PYEOF
EOF

echo ""
echo "🔑 Test 2: Check environment variables"
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms
source .venv/bin/activate
python3 << 'PYEOF'
import os
api_key = os.getenv("TEXTVERIFIED_API_KEY")
username = os.getenv("TEXTVERIFIED_USERNAME")
email = os.getenv("TEXTVERIFIED_EMAIL")

print(f"TEXTVERIFIED_API_KEY: {'✅ Set' if api_key else '❌ Missing'} ({len(api_key) if api_key else 0} chars)")
print(f"TEXTVERIFIED_USERNAME: {'✅ Set' if username else '❌ Missing'}")
print(f"TEXTVERIFIED_EMAIL: {'✅ Set' if email else '❌ Missing'} ({email if email else 'N/A'})")
PYEOF
EOF

echo ""
echo "🧪 Test 3: Simulate TextVerifiedService initialization"
ssh $SERVER << 'EOF'
cd /root/NAMASKAHsms
source .venv/bin/activate
python3 << 'PYEOF'
import os
import sys

# Load .env file
from dotenv import load_dotenv
load_dotenv()

try:
    import textverified
    print("✅ textverified imported")
except ImportError:
    print("❌ textverified NOT imported")
    textverified = None

api_key = os.getenv("TEXTVERIFIED_API_KEY")
api_username = os.getenv("TEXTVERIFIED_USERNAME") or os.getenv("TEXTVERIFIED_EMAIL")

print(f"\nInitialization check:")
print(f"  textverified module: {textverified is not None}")
print(f"  api_key: {bool(api_key)}")
print(f"  api_username: {bool(api_username)}")
print(f"  enabled: {textverified is not None and bool(api_key and api_username)}")

if textverified is not None and api_key and api_username:
    try:
        client = textverified.TextVerified(
            api_key=api_key,
            api_username=api_username,
        )
        print("\n✅ TextVerified client created successfully!")
    except Exception as e:
        print(f"\n❌ Failed to create client: {e}")
else:
    print("\n❌ Cannot create client - missing requirements")
PYEOF
EOF

echo ""
echo "==========================================="
echo "Diagnosis complete!"
