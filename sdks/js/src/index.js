const axios = require('axios');
const Verifications = require('./resources/verifications');
const Users = require('./resources/users');
const Referrals = require('./resources/referrals');

class NamaskahClient {
    /**
     * Initialize the Namaskah SDK client.
     * @param {string} apiKey - Your API key.
     * @param {string} dateUrl - Optional base URL (default: https://api.namaskah.com/api).
     */
    constructor(apiKey, baseUrl = 'https://api.namaskah.com/api') {
        if (!apiKey) {
            throw new Error('API Key is required to initialize NamaskahClient');
        }

        this.client = axios.create({
            baseURL: baseUrl,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
                'User-Agent': 'Namaskah-Node-SDK/1.0.0'
            }
        });

        this.verifications = new Verifications(this.client);
        this.users = new Users(this.client);
        this.referrals = new Referrals(this.client);
    }
}

module.exports = NamaskahClient;
