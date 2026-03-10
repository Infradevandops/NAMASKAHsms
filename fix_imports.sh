#!/bin/bash
# Fix F821 import errors

cd "/Users/machine/My Drive/Github Projects/Namaskah. app"

# Fix waitlist.py - add missing imports
sed -i '' '6a\
from app.models.waitlist import Waitlist\
from app.schemas.waitlist import WaitlistJoin, WaitlistResponse
' app/api/core/waitlist.py

# Fix pricing_template.py - change BaseModel to Base
sed -i '' 's/class PricingTemplate(BaseModel):/class PricingTemplate(Base):/' app/models/pricing_template.py
sed -i '' 's/class TierPricing(BaseModel):/class TierPricing(Base):/' app/models/pricing_template.py
sed -i '' 's/class PricingHistory(BaseModel):/class PricingHistory(Base):/' app/models/pricing_template.py
sed -i '' 's/class UserPricingAssignment(BaseModel):/class UserPricingAssignment(Base):/' app/models/pricing_template.py

echo "Fixed import errors"
