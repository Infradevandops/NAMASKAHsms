# Verification Troubleshooting Guide

This guide covers common issues and solutions for SMS verifications on Namaskah.

## 1. Service Loading Errors
**Problem**: The service selection input is disabled or shows "Services unavailable".
- **Cause**: The SMS provider API is temporarily down or unreachable.
- **Solution**: 
    1. Wait 30-60 seconds and click the **Retry** button in the modal.
    2. Refresh the page.
    3. If the issue persists for more than 5 minutes, check our [Status Page](#) or contact support.

## 2. Area Code Fallbacks
**Problem**: You requested a specific area code but received a number with a different one.
- **Cause**: The requested area code was unavailable from our provider at that moment.
- **Behavior**: Our system automatically falls back to a nearby area code (usually in the same state) to ensure you get a working number.
- **Icon**: A **yellow warning icon (⚠️)** will appear next to the phone number in your history to indicate a fallback occurred.
- **Charging**: You are charged the standard rate. No extra credits are deducted for the fallback.

## 3. Carrier Mismatch (Strict Enforcement)
**Problem**: Your request failed with a "409 Conflict" or "Requested carrier unavailable" message.
- **Cause**: You requested a specific carrier (e.g., Verizon) that our provider could not fulfill.
- **Policy**: We strictly enforce carrier selection. If the provider assigns a different carrier than requested, we **automatically cancel and refund** the transaction immediately.
- **Solution**: 
    1. Try again in a few minutes.
    2. Try selecting "Any Carrier" if your use-case allows it.
    3. Select a different carrier.

## 4. Insufficient Credits
**Problem**: Request fails with "402 Payment Required".
- **Cause**: Your balance is lower than the total cost of the verification (Base Price + Filters).
- **Solution**: Visit the **Credits** section on your dashboard to top up.

## 5. Timing Out
**Problem**: "Waiting for SMS..." takes more than 10 minutes and then says "Expired" or "Timeout".
- **Cause**: The service you are verifying (e.g., Telegram) did not send the SMS to that number, or the provider missed it.
- **Solution**:
    1. Click "Cancel" to get an immediate refund (if available).
    2. Our **Auto-Refund** system will periodically scan for expired verifications and refund you automatically if no code was received.

---
For further assistance, reach out to **support@namaskah.app**.
