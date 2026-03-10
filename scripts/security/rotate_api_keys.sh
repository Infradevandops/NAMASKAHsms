#!/bin/bash
# API Key Rotation Script
# Addresses: Rotate PAYSTACK_SECRET_KEY, Rotate TEXTVERIFIED_API_KEY

echo "🔐 API Key Rotation Checklist"
echo "============================="

echo ""
echo "⚠️  CRITICAL: Rotate these API keys immediately"
echo ""

echo "1. PAYSTACK_SECRET_KEY"
echo "   Current: sk_live_*** (exposed in logs)"
echo "   Action: Generate new key in Paystack dashboard"
echo "   Update: Render environment variables"
echo ""

echo "2. TEXTVERIFIED_API_KEY" 
echo "   Current: *** (exposed in logs)"
echo "   Action: Generate new key in TextVerified dashboard"
echo "   Update: Render environment variables"
echo ""

echo "3. EMERGENCY_SECRET"
echo "   Current: Not set"
echo "   Action: Generate random 32+ character string"
echo "   Update: Add to Render or leave unset to disable"
echo ""

echo "🔧 Rotation Steps:"
echo ""
echo "Step 1: Generate New Keys"
echo "- Paystack: Dashboard → Settings → API Keys → Generate"
echo "- TextVerified: Account → API → Regenerate Key"
echo "- Emergency: openssl rand -hex 32"
echo ""

echo "Step 2: Update Environment Variables"
echo "- Go to Render dashboard"
echo "- Select namaskah service"
echo "- Environment → Edit"
echo "- Update keys"
echo "- Deploy"
echo ""

echo "Step 3: Verify"
echo "- Test payment initialization"
echo "- Test SMS verification"
echo "- Check application logs"
echo ""

echo "🚨 Security Notes:"
echo "- Never commit keys to git"
echo "- Use environment variables only"
echo "- Monitor for key exposure in logs"
echo "- Rotate keys quarterly"