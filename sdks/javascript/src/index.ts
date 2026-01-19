import axios, { AxiosInstance } from 'axios';

export interface NamaskahConfig {
    apiKey: string;
    baseUrl?: string;
    timeout?: number;
}

export interface ForwardingConfig {
    email_enabled?: boolean;
    email_address?: string;
    webhook_enabled?: boolean;
    webhook_url?: string;
    webhook_secret?: string;
    forward_all?: boolean;
}

export class NamaskahClient {
    private api: AxiosInstance;

    constructor(config: NamaskahConfig) {
        this.api = axios.create({
            baseURL: config.baseUrl || 'https://api.namaskah.com/api',
            timeout: config.timeout || 10000,
            headers: {
                'Authorization': `Bearer ${config.apiKey}`,
                'Content-Type': 'application/json',
                'X-SDK-Client': 'javascript-sdk-v1'
            }
        });
    }

    /**
     * SMS Verification Methods
     */
    public verify = {
        /**
         * Get available countries for verification
         */
        getCountries: async () => {
            const response = await this.api.get('/countries');
            return response.data;
        },

        /**
         * Get available services for a country
         */
        getServices: async (country: string) => {
            const response = await this.api.get(`/services?country=${country}`);
            return response.data;
        },

        /**
         * Request a phone number for verification
         */
        requestNumber: async (service: string, country: string) => {
            const response = await this.api.post('/verify/request', { service, country });
            return response.data;
        },

        /**
         * Get the code for an active order
         */
        getCode: async (orderId: string) => {
            const response = await this.api.get(`/verify/code/${orderId}`);
            return response.data;
        }
    };

    /**
     * Forwarding Configuration
     */
    public forwarding = {
        /**
         * Get current forwarding configuration
         */
        getConfig: async () => {
            const response = await this.api.get('/forwarding');
            return response.data;
        },

        /**
         * Update forwarding configuration
         */
        updateConfig: async (config: ForwardingConfig) => {
            const response = await this.api.post('/forwarding/configure', null, { params: config });
            return response.data;
        },

        /**
         * Test current forwarding configuration
         */
        test: async (testMessage?: string) => {
            const response = await this.api.post('/forwarding/test', null, {
                params: { test_message: testMessage }
            });
            return response.data;
        }
    };

    /**
     * Analytics
     */
    public analytics = {
        /**
         * Get analytics summary
         */
        getSummary: async (from?: string, to?: string) => {
            const response = await this.api.get('/analytics/summary', {
                params: { from, to }
            });
            return response.data;
        }
    };

    /**
     * Blacklist
     */
    public blacklist = {
        /**
         * Get blacklist entries
         */
        getEntries: async (serviceName?: string) => {
            const response = await this.api.get('/blacklist', {
                params: { service_name: serviceName }
            });
            return response.data;
        },

        /**
         * Add phone to blacklist
         */
        add: async (phoneNumber: string, reason?: string, serviceName?: string) => {
            const response = await this.api.post('/blacklist', {
                phone_number: phoneNumber,
                reason,
                service_name: serviceName
            });
            return response.data;
        },

        /**
         * Remove phone from blacklist
         */
        remove: async (blacklistId: string) => {
            const response = await this.api.delete(`/blacklist/${blacklistId}`);
            return response.data;
        }
    };
}

export default NamaskahClient;
