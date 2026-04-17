#!/bin/bash
# Deploy admin balance sync changes

cd "/Users/machine/My Drive/Github Projects/Namaskah. app"

echo "✅ Staging changes..."
git add -A

echo "✅ Committing..."
git commit -m "feat: implement admin balance sync with TextVerified API

- Add BalanceService for unified balance management
- Add TransactionService for complete audit trail  
- Update purchase flow to sync admin balance from TextVerified
- Add database migration for balance_last_synced field
- Add comprehensive unit tests
- Preserve transaction history for analytics
- Fix code formatting (black, flake8)"

echo "✅ Pushing to remote..."
git push origin main

echo "✅ Deployment complete! Check CI at:"
echo "https://github.com/yourusername/namaskah-sms/actions"
