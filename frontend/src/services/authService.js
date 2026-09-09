/**
 * AegisAI Authentication Service
 * Endpoints for user registration, credential login, token refresh, and profile fetching.
 */

import api from "./api";

export const authService = {
    /**
     * Authenticate with email and password
     * POST /api/v1/auth/login
     */
    async login(email, password) {
        const response = await api.post("/auth/login", { email, password });
        const tokenData = response.data?.data;
        if (tokenData?.access_token) {
            localStorage.setItem("aegis_access_token", tokenData.access_token);
            localStorage.setItem("access_token", tokenData.access_token);
            if (tokenData.refresh_token) {
                localStorage.setItem("aegis_refresh_token", tokenData.refresh_token);
                localStorage.setItem("refresh_token", tokenData.refresh_token);
            }
        }
        return tokenData;
    },

    /**
     * Register a new user account
     * POST /api/v1/auth/register
     */
    async register(name, email, password, role = "CITIZEN") {
        const response = await api.post("/auth/register", {
            name,
            email,
            password,
            role
        });
        return response.data?.data;
    },

    /**
     * Get current authenticated user profile
     * GET /api/v1/auth/me
     */
    async getMe() {
        const response = await api.get("/auth/me");
        const user = response.data?.data;
        if (user) {
            localStorage.setItem("aegis_user", JSON.stringify(user));
        }
        return user;
    },

    /**
     * Exchange refresh token for a new access token
     * POST /api/v1/auth/refresh
     */
    async refreshToken(refreshToken) {
        const response = await api.post("/auth/refresh", {
            refresh_token: refreshToken
        });
        return response.data?.data;
    },

    /**
     * Clear all stored tokens and session data
     */
    logout() {
        localStorage.removeItem("aegis_access_token");
        localStorage.removeItem("access_token");
        localStorage.removeItem("aegis_refresh_token");
        localStorage.removeItem("refresh_token");
        localStorage.removeItem("aegis_user");
    },

    /**
     * Get currently stored cached user
     */
    getCachedUser() {
        try {
            const raw = localStorage.getItem("aegis_user");
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    },

    /**
     * Check if an access token exists in storage
     */
    hasToken() {
        const token = localStorage.getItem("aegis_access_token") || localStorage.getItem("access_token");
        return Boolean(token && token.trim() !== "");
    }
};

export default authService;
