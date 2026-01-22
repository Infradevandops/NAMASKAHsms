## International Providers (Future Advancement)

The current system architecture supports international routing, but the fulfillment layer is limited to US-based numbers via TextVerified. To enable true global coverage, the following providers are recommended for integration:

1. **5SIM**
   - **Best for:** Cheap, disposable international numbers.
   - **Coverage:** 180+ countries.
   - **Integration Priority:** High (for cost-effective global scale).

2. **SMS-Activate**
   - **Best for:** High-reliability verified accounts (Telegram, WhatsApp).
   - **Coverage:** Global.
   - **Integration Priority:** Medium (as a premium fallback).

3. **GetSMS**
   - **Best for:** Specific niche regions.
   - **Integration Priority:** Low.

### Implementation Strategy
Future development should focus on creating `FiveSimService` and `SMSActivateService` classes adhering to the `SMSService` interface. The `SmartRouter` will then be updated to route non-US traffic to these providers automatically.

### ⚠️ Current Limitations
While the **frontend and backend architecture** fully supports selecting and routing 37+ countries (passing country codes to the provider), the **current active provider (TextVerified)** is primarily North American.
- **US/Canada/UK**: High availability.
- **Other Regions**: May experience empty service lists or low inventory until **5SIM** or **SMS-Activate** are integrated.
