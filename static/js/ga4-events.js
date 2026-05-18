/**
 * GA4 Event Tracking
 * Call these functions at the right points in your app flows.
 * gtag is loaded globally via base.html.
 */

function gtagEvent(eventName, params) {
  if (typeof gtag === 'undefined') return;
  gtag('event', eventName, params);
}

// Call after successful registration
export function trackSignup(method = 'email') {
  gtagEvent('sign_up', { method });
}

// Call after successful payment webhook confirmation
export function trackPayment(transactionId, amountUsd) {
  gtagEvent('purchase', {
    transaction_id: transactionId,
    value: amountUsd,
    currency: 'USD',
  });
}

// Call when SMS code is received
export function trackVerification(countryCode, serviceName) {
  gtagEvent('verification_success', {
    country: countryCode,
    service: serviceName,
  });
}

// Call after tier upgrade completes
export function trackTierUpgrade(fromTier, toTier) {
  gtagEvent('upgrade', { from_tier: fromTier, to_tier: toTier });
}
