/**
 * AegisAI Centralized API Client (Axios)
 * Handles automatic JWT injection, concurrent 401 token refresh queue, and error normalization.
 */

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        "Content-Type": "application/json"
    },
    timeout: 12000 // 12 seconds timeout for snappy UI recovery
});

// Flag and queue to handle concurrent 401 refresh operations
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

// ---------------------------------------------------------------------------
// Request Interceptor: Attach JWT Access Token
// ---------------------------------------------------------------------------
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem("aegis_access_token") || localStorage.getItem("access_token");
        if (token && token !== "null" && token !== "undefined" && token.trim() !== "") {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// ---------------------------------------------------------------------------
// Response Interceptor: 401 Token Refresh & Error Normalization
// ---------------------------------------------------------------------------
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Skip refresh logic for auth endpoints
        if (
            originalRequest.url?.includes("/auth/login") ||
            originalRequest.url?.includes("/auth/refresh") ||
            originalRequest.url?.includes("/auth/register")
        ) {
            return Promise.reject(error);
        }

        // If 401 Unauthorized received and not already retried
        if (error.response?.status === 401 && !originalRequest._retry) {
            const refreshToken = localStorage.getItem("aegis_refresh_token") || localStorage.getItem("refresh_token");

            if (!refreshToken) {
                // No refresh token available, session is expired
                window.dispatchEvent(new CustomEvent("aegis:auth_expired"));
                return Promise.reject(error);
            }

            if (isRefreshing) {
                // Queue concurrent requests while token is refreshing
                return new Promise((resolve, reject) => {
                    failedQueue.push({ resolve, reject });
                })
                    .then((newToken) => {
                        originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        return api(originalRequest);
                    })
                    .catch((err) => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            try {
                // Perform token refresh directly with standard axios to avoid recursion
                const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
                    refresh_token: refreshToken
                }, {
                    headers: { "Content-Type": "application/json" }
                });

                const tokenData = response.data?.data;
                const newAccessToken = tokenData?.access_token;
                const newRefreshToken = tokenData?.refresh_token;

                if (newAccessToken) {
                    localStorage.setItem("aegis_access_token", newAccessToken);
                    localStorage.setItem("access_token", newAccessToken);

                    if (newRefreshToken) {
                        localStorage.setItem("aegis_refresh_token", newRefreshToken);
                        localStorage.setItem("refresh_token", newRefreshToken);
                    }

                    api.defaults.headers.common.Authorization = `Bearer ${newAccessToken}`;
                    originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

                    processQueue(null, newAccessToken);
                    return api(originalRequest);
                } else {
                    throw new Error("Token refresh response payload invalid.");
                }
            } catch (refreshErr) {
                processQueue(refreshErr, null);
                localStorage.removeItem("aegis_access_token");
                localStorage.removeItem("access_token");
                localStorage.removeItem("aegis_refresh_token");
                localStorage.removeItem("refresh_token");
                localStorage.removeItem("aegis_user");

                window.dispatchEvent(new CustomEvent("aegis:auth_expired"));
                return Promise.reject(refreshErr);
            } finally {
                isRefreshing = false;
            }
        }

        return Promise.reject(error);
    }
);

export default api;