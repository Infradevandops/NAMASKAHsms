import { createStore } from 'zustand/vanilla'
import { persist, createJSONStorage } from 'zustand/middleware'

export interface User {
    id: string;
    email: string;
    credits: number;
    plan_tier: string;
}

export interface AuthState {
    accessToken: string | null;
    refreshToken: string | null;
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;

    setTokens: (accessToken: string, refreshToken?: string) => void;
    setUser: (user: User) => void;
    logout: () => void;
    setError: (error: string) => void;
    setLoading: () => void;
}

export const authStore = createStore<AuthState>()(
    persist(
        (set) => ({
            accessToken: null,
            refreshToken: null,
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            setTokens: (accessToken: string, refreshToken?: string) => set({
                accessToken,
                refreshToken: refreshToken || null,
                isAuthenticated: true,
                error: null
            }),

            setUser: (user: User) => set({ user, isLoading: false }),

            logout: () => set({
                accessToken: null,
                refreshToken: null,
                user: null,
                isAuthenticated: false,
                error: null
            }),

            setError: (error: string) => set({ error, isLoading: false }),

            setLoading: () => set({ isLoading: true })
        }),
        {
            name: 'auth-storage',
            storage: createJSONStorage(() => localStorage),
        }
    )
)
