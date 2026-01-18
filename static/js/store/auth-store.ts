// @ts-check
import { createStore } from 'zustand/vanilla'
import { persist, createJSONStorage } from 'zustand/middleware'

/**
 * @typedef {Object} User
 * @property {string} id
 * @property {string} email
 * @property {number} credits
 * @property {string} plan_tier
 */

/**
 * @typedef {Object} AuthState
 * @property {string|null} accessToken
 * @property {string|null} refreshToken
 * @property {User|null} user
 * @property {boolean} isAuthenticated
 * @property {boolean} isLoading
 * @property {string|null} error
 * 
 * @typedef {Object} AuthActions
 * @property {(token: string, refreshToken?: string) => void} setTokens
 * @property {(user: User) => void} setUser
 * @property {() => void} logout
 * @property {(error: string) => void} setError
 * @property {() => void} setLoading
 * 
 * @typedef {AuthState & AuthActions} AuthStore
 */

export const authStore = createStore(
    persist(
        (set) => ({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            /**
             * @param {string} accessToken
             * @param {string|null} [refreshToken]
             */
            setTokens: (accessToken, refreshToken) => set({
                accessToken,
                refreshToken: refreshToken || null,
                isAuthenticated: true,
                error: null
            }),

            /** @param {User} user */
            setUser: (user) => set({ user, isLoading: false }),

            logout: () => set({
                accessToken: null,
                refreshToken: null,
                user: null,
                isAuthenticated: false,
                error: null
            }),

            /** @param {string} error */
            setError: (error) => set({ error, isLoading: false }),

            setLoading: () => set({ isLoading: true })
        }),
        {
            name: 'auth-storage', // name of the item in the storage (must be unique)
            storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
        }
    )
)
