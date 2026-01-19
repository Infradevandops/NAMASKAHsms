# Namaskah JavaScript SDK

Official JavaScript library for Namaskah SMS Verification API.

## Installation

```bash
npm install @namaskah/sdk
# or
yarn add @namaskah/sdk
```

## Usage

```javascript
import { NamaskahClient } from '@namaskah/sdk';

const client = new NamaskahClient({
  apiKey: 'your_api_key_here'
});

// Example: Request a verification number
async function main() {
  try {
    const countries = await client.verify.getCountries();
    console.log('Available countries:', countries);

    const number = await client.verify.requestNumber('whatsapp', 'US');
    console.log('Got number:', number);
  } catch (error) {
    console.error('API Error:', error.message);
  }
}

main();
```

## Features

- **SMS Verification**: Request numbers, receive codes, and manage verification orders.
- **Forwarding**: Configure email and webhook forwarding for received SMS.
- **Analytics**: Retrieve your usage statistics and performance metrics.
- **Blacklist**: Manage your personal blacklist of phone numbers.

## TypeScript Support

This library is written in TypeScript and includes full type definitions.

```typescript
import { NamaskahClient, ForwardingConfig } from '@namaskah/sdk';

const client = new NamaskahClient({ apiKey: '...' });
```

## License

MIT
