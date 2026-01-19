class Verifications {
    constructor(client) {
        this.client = client;
    }

    /**
     * Create a new verification.
     * @param {Object} data - Verification details.
     * @param {string} data.service - Service name (e.g., 'whatsapp').
     * @param {string} data.country - Country code (e.g., 'US').
     * @returns {Promise<Object>} Verification object.
     */
    async create(data) {
        const response = await this.client.post('/verify', data);
        return response.data;
    }

    /**
     * Get verification status.
     * @param {string} id - Verification ID.
     * @returns {Promise<Object>} Verification status.
     */
    async get(id) {
        const response = await this.client.get(`/verify/${id}`);
        return response.data;
    }

    /**
     * Cancel a verification.
     * @param {string} id - Verification ID.
     * @returns {Promise<Object>} Response.
     */
    async cancel(id) {
        const response = await this.client.post(`/verify/${id}/cancel`);
        return response.data;
    }
}

module.exports = Verifications;
