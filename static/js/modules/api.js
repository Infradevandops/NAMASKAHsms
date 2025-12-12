/**
 * API Layer Module
 * Centralized API calls with error handling
 */

export const api = {
  /**
   * Get all countries (USA only)
   * @async
   * @returns {Promise<Object>} Countries data
   */
  async getCountries() {
    try {
      const response = await fetch('/api/countries/');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch countries:', error);
      throw error;
    }
  },

  /**
   * Get US area codes
   * @async
   * @returns {Promise<Object>} Area codes data
   */
  async getAreaCodes() {
    try {
      const response = await fetch('/api/countries/usa/area-codes');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch area codes:', error);
      throw error;
    }
  },

  /**
   * Get services for area code
   * @async
   * @param {string} areaCode - Area code
   * @returns {Promise<Object>} Services data
   */
  async getServices(areaCode) {
    try {
      const params = new URLSearchParams({ areaCode: areaCode || 'any' });
      const response = await fetch(`/api/countries/usa/services?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch services:', error);
      throw error;
    }
  },

  /**
   * Get available carriers
   * @async
   * @returns {Promise<Object>} Carriers data
   */
  async getCarriers() {
    try {
      const response = await fetch('/api/countries/usa/carriers');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch carriers:', error);
      throw error;
    }
  },

  /**
   * Get pricing for verification
   * @async
   * @param {string} service - Service name
   * @param {string} areaCode - Area code
   * @param {string} carrier - Carrier name
   * @returns {Promise<Object>} Pricing data
   */
  async getPricing(service, areaCode, carrier) {
    try {
      const params = new URLSearchParams({
        service,
        area_code: areaCode || 'any',
        carrier: carrier || 'any'
      });
      const response = await fetch(`/api/verification/pricing?${params}`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to fetch pricing:', error);
      throw error;
    }
  },

  /**
   * Purchase verification
   * @async
   * @param {string} service - Service name
   * @param {string} areaCode - Area code
   * @param {string} carrier - Carrier name
   * @returns {Promise<Object>} Purchase result
   */
  async purchaseVerification(service, areaCode, carrier) {
    try {
      const response = await fetch('/api/verification/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service, area_code: areaCode, carrier })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to purchase verification:', error);
      throw error;
    }
  }
  /**
   * Initialize payment
   * @async
   * @param {number} amount_usd - Amount in USD
   * @returns {Promise<Object>} Payment data with authorization_url
   */
  async initializePayment(amount_usd) {
    try {
      const response = await fetch('/api/billing/initialize-payment', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount_usd })
      });
      // 503 means Service Unavailable (Paystack not configured), handle gracefully
      if (response.status === 503) {
        throw new Error('Payment gateway unavailable. Please contact support.');
      }
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || `HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Failed to initialize payment:', error);
      throw error;
    }
  },

  /**
   * Save user settings
   * @async
   * @param {string} type - 'notifications', 'privacy', or 'billing'
   * @param {Object} data - Settings data
   * @returns {Promise<Object>} Result
   */
  async saveSettings(type, data) {
    try {
      const response = await fetch(`/api/user/settings/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (error) {
      console.error('Failed to save settings:', error);
      throw error;
    }
  },

  /**
   * Logout all devices
   * @async
   * @returns {Promise<Object>} Result
   */
  async logoutAll() {
    try {
      const response = await fetch('/api/user/logout-all', { method: 'POST' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (e) { throw e; }
  },

  /**
   * Delete account
   * @async
   * @param {string} password - User password
   * @returns {Promise<Object>} Result
   */
  async deleteAccount(password) {
    try {
      const response = await fetch('/api/user/delete-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } catch (e) { throw e; }
  }
};
