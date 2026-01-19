class Referrals {
    constructor(client) {
        this.client = client;
    }

    /**
     * Get referral statistics.
     * @returns {Promise<Object>} Referral stats.
     */
    async getStats() {
        const response = await this.client.get('/referrals/stats');
        return response.data;
    }

    /**
     * List referred users.
     * @returns {Promise<Array>} List of referrals.
     */
    async list() {
        const response = await this.client.get('/referrals/list');
        return response.data;
    }
}

module.exports = Referrals;
