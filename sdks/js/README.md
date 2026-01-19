# Namaskah Node.js SDK

Official Node.js library for the Namaskah SMS Verification API.

## Installation

```bash
npm install namaskah-node-sdk
```

## Usage

```javascript
const Namaskah = require('namaskah-node-sdk');

const client = new Namaskah('YOUR_API_KEY');

// Verify a number
async function verify() {
  try {
    const verification = await client.verifications.create({
      service: 'whatsapp',
      country: 'US'
    });
    console.log('Verification created:', verification);
  } catch (error) {
    console.error('Error:', error);
  }
}

verify();
```

## Features

- Verifications (Create, Check Status, Cancel)
- User Management (Profile, Balance)
- Referrals (Stats, List)
