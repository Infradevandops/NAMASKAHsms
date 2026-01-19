class Users {
    constructor(client) {
        this.client = client;
    }

    /**
     * Get current user profile.
     * @returns {Promise<Object>} User profile.
     */
    async getProfile() {
        const response = await this.client.get('/user/profile');
        return response.data;
    }

    /**
     * Get user balance.
     * @returns {Promise<Object>} Balance info.
     */
    async getBalance() {
        const response = await this.client.get('/billing/balance');
        return response.data;
    }
}

module.exports = Users;
