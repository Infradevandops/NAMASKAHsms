/**
 * Frontend response validation utilities
 * Validates API responses and logs errors for debugging
 */

class ResponseValidationError extends Error {
    constructor(message, missingFields = []) {
        super(message);
        this.name = 'ResponseValidationError';
        this.missingFields = missingFields;
    }
}

/**
 * Check if all required fields are present in the response
 * @param {Object} data - The response data
 * @param {Array<string>} requiredFields - List of required field names
 * @returns {{valid: boolean, missing: Array<string>}}
 */
function checkRequiredFields(data, requiredFields) {
    if (!data || typeof data !== 'object') {
        return { valid: false, missing: requiredFields };
    }
    
    const missing = requiredFields.filter(field => !(field in data));
    return {
        valid: missing.length === 0,
        missing: missing
    };
}

/**
 * Validate /api/tiers/ response
 * @param {Object} data - The response data
 * @returns {{valid: boolean, error: string|null}}
 */
function validateTiersListResponse(data) {
    const requiredFields = ['tiers'];
    const check = checkRequiredFields(data, requiredFields);
    
    if (!check.valid) {
        const error = `Missing required fields: ${check.missing.join(', ')}`;
        console.error('[Response Validation] /api/tiers/ -', error);
        return { valid: false, error };
    }
    
    if (!Array.isArray(data.tiers)) {
        const error = 'tiers must be an array';
        console.error('[Response Validation] /api/tiers/ -', error);
        return { valid: false, error };
    }
    
    if (data.tiers.length !== 4) {
        const error = `Expected 4 tiers, got ${data.tiers.length}`;
        console.warn('[Response Validation] /api/tiers/ -', error);
        // Don't fail validation, just warn
    }
    
    // Validate each tier has required fields
    const tierFields = ['tier', 'name', 'price_monthly', 'price_display', 'quota_usd', 'overage_rate', 'features'];
    for (let i = 0; i < data.tiers.length; i++) {
        const tierCheck = checkRequiredFields(data.tiers[i], tierFields);
        if (!tierCheck.valid) {
            const error = `Tier ${i} missing fields: ${tierCheck.missing.join(', ')}`;
            console.error('[Response Validation] /api/tiers/ -', error);
            return { valid: false, error };
        }
    }
    
    return { valid: true, error: null };
}

/**
 * Validate /api/tiers/current response
 * @param {Object} data - The response data
 * @returns {{valid: boolean, error: string|null}}
 */
function validateCurrentTierResponse(data) {
    const requiredFields = [
        'current_tier',
        'tier_name',
        'price_monthly',
        'quota_usd',
        'quota_used_usd',
        'quota_remaining_usd',
        'sms_count',
        'within_quota',
        'overage_rate',
        'features'
    ];
    
    const check = checkRequiredFields(data, requiredFields);
    
    if (!check.valid) {
        const error = `Missing required fields: ${check.missing.join(', ')}`;
        console.error('[Response Validation] /api/tiers/current -', error);
        return { valid: false, error };
    }
    
    return { valid: true, error: null };
}

/**
 * Validate /api/analytics/summary response
 * @param {Object} data - The response data
 * @returns {{valid: boolean, error: string|null}}
 */
function validateAnalyticsSummaryResponse(data) {
    const requiredFields = [
        'total_verifications',
        'successful_verifications',
        'success_rate',
        'total_spent'
    ];
    
    const check = checkRequiredFields(data, requiredFields);
    
    if (!check.valid) {
        const error = `Missing required fields: ${check.missing.join(', ')}`;
        console.error('[Response Validation] /api/analytics/summary -', error);
        return { valid: false, error };
    }
    
    return { valid: true, error: null };
}

/**
 * Validate /api/dashboard/activity/recent response
 * @param {Array} data - The response data (array of activities)
 * @returns {{valid: boolean, error: string|null}}
 */
function validateDashboardActivityResponse(data) {
    if (!Array.isArray(data)) {
        const error = 'Response must be an array';
        console.error('[Response Validation] /api/dashboard/activity/recent -', error);
        return { valid: false, error };
    }
    
    const activityFields = ['id', 'service_name', 'phone_number', 'status'];
    
    for (let i = 0; i < data.length; i++) {
        const check = checkRequiredFields(data[i], activityFields);
        if (!check.valid) {
            const error = `Activity ${i} missing fields: ${check.missing.join(', ')}`;
            console.error('[Response Validation] /api/dashboard/activity/recent -', error);
            return { valid: false, error };
        }
    }
    
    return { valid: true, error: null };
}

/**
 * Validate API response based on endpoint
 * @param {string} endpoint - The API endpoint path
 * @param {*} data - The response data
 * @returns {{valid: boolean, error: string|null}}
 */
function validateResponse(endpoint, data) {
    try {
        if (endpoint.includes('/api/tiers/current')) {
            return validateCurrentTierResponse(data);
        } else if (endpoint.includes('/api/tiers')) {
            return validateTiersListResponse(data);
        } else if (endpoint.includes('/api/analytics/summary')) {
            return validateAnalyticsSummaryResponse(data);
        } else if (endpoint.includes('/api/dashboard/activity/recent')) {
            return validateDashboardActivityResponse(data);
        }
        
        // Unknown endpoint, skip validation
        return { valid: true, error: null };
    } catch (error) {
        console.error('[Response Validation] Unexpected error:', error);
        return { valid: false, error: error.message };
    }
}

/**
 * Show validation error to user
 * @param {string} message - Error message to display
 */
function showValidationError(message) {
    console.error('[Response Validation Error]', message);
    
    // Create error notification
    const errorDiv = document.createElement('div');
    errorDiv.className = 'validation-error-notification';
    errorDiv.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #fee;
        border: 1px solid #fcc;
        border-radius: 8px;
        padding: 16px;
        max-width: 400px;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    `;
    
    errorDiv.innerHTML = `
        <div style="display: flex; align-items: start; gap: 12px;">
            <div style="color: #c00; font-size: 20px;">⚠️</div>
            <div style="flex: 1;">
                <div style="font-weight: 600; color: #c00; margin-bottom: 4px;">Data Validation Error</div>
                <div style="font-size: 14px; color: #666;">${message}</div>
                <div style="font-size: 12px; color: #999; margin-top: 8px;">Please refresh the page or contact support if the issue persists.</div>
            </div>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; font-size: 20px; cursor: pointer; color: #999;">&times;</button>
        </div>
    `;
    
    document.body.appendChild(errorDiv);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 10000);
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        checkRequiredFields,
        validateTiersListResponse,
        validateCurrentTierResponse,
        validateAnalyticsSummaryResponse,
        validateDashboardActivityResponse,
        validateResponse,
        showValidationError,
        ResponseValidationError
    };
}
