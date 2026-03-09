#!/bin/bash

# Configure GitLab repo with token
cd "/Users/machine/My Drive/Github Projects/NAMASKAHsms-gitlab"

echo "🔧 Configuring GitLab token..."

# Set remote URL with token
git remote set-url origin https://oauth2:glpat-Oxf0N5r_-ehxfRhM86DOnG86MQp1Omg5MmxqCw.01.1202lxyp0@gitlab.com/oghenesuvwe-group/NAMASKAHsms.git

echo "✅ Token configured!"
echo ""

# Test connection
echo "🧪 Testing connection..."
git fetch origin

echo ""
echo "✅ Setup complete! You can now:"
echo "   - Run ./check_gitlab_updates.sh"
echo "   - Run ./pull_gitlab_updates.sh"
echo ""
