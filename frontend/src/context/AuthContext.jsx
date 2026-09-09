/**
 * AegisAI Authentication Context & Provider
 * Manages user session state, JWT lifecycle, RBAC roles, and login/logout workflows.
 */

import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import authService from "../services/authService";
import wsManager from "../services/websocketManager";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(authService.getCachedUser());
    const [token, setToken] = useState(
        localStorage.getItem("aegis_access_token") || localStorage.getItem("access_token")
    );
    const [isLoading, setIsLoading] = useState(true);

    // Hydrate user profile on initial mount if token exists
    const hydrateUser = useCallback(async () => {
        const storedToken = localStorage.getItem("aegis_access_token") || localStorage.getItem("access_token");
        if (storedToken) {
            try {
                const profile = await authService.getMe();
                setUser(profile);
                setToken(storedToken);
            } catch (err) {
                console.warn("[AuthContext] Profile hydration failed, clearing session:", err);
                authService.logout();
                setUser(null);
                setToken(null);
            }
        } else {
            setUser(null);
            setToken(null);
        }
        setIsLoading(false);
    }, []);

    useEffect(() => {
        hydrateUser();

        // Listen for session expiry from API interceptor
        const handleAuthExpired = () => {
            setUser(null);
            setToken(null);
        };

        window.addEventListener("aegis:auth_expired", handleAuthExpired);
        return () => {
            window.removeEventListener("aegis:auth_expired", handleAuthExpired);
        };
    }, [hydrateUser]);

    /**
     * User Login
     */
    const login = async (email, password) => {
        setIsLoading(true);
        try {
            const tokenData = await authService.login(email, password);
            setToken(tokenData.access_token);

            // Fetch and set full user profile
            const profile = await authService.getMe();
            setUser(profile);

            // Connect or reconnect WebSocket with token
            wsManager.connect(tokenData.access_token);

            return { success: true, user: profile };
        } catch (error) {
            console.error("[AuthContext] Login failed:", error);
            let message = "Invalid email or password.";
            const detail = error?.response?.data?.detail;
            if (Array.isArray(detail)) {
                message = detail.map((d) => d.msg || d.message).join(" • ");
            } else if (typeof detail === "string") {
                message = detail;
            } else if (error?.response?.data?.message) {
                message = error.response.data.message;
            } else if (error?.message) {
                message = error.message;
            }
            return { success: false, error: message };
        } finally {
            setIsLoading(false);
        }
    };

    /**
     * User Registration
     */
    const register = async (name, email, password, role = "CITIZEN") => {
        setIsLoading(true);
        try {
            await authService.register(name, email, password, role);
            // Auto login after registration
            return await login(email, password);
        } catch (error) {
            console.error("[AuthContext] Registration failed:", error);
            let message = "Registration failed.";
            if (error?.response?.status === 409) {
                message = `An account with email '${email}' already exists. Please switch to Sign In or use another email.`;
            } else {
                const detail = error?.response?.data?.detail;
                if (Array.isArray(detail)) {
                    message = detail.map((d) => d.msg || d.message).join(" • ");
                } else if (typeof detail === "string") {
                    message = detail;
                } else if (error?.response?.data?.message) {
                    message = error.response.data.message;
                } else if (error?.message) {
                    message = error.message;
                }
            }
            return { success: false, error: message };
        } finally {
            setIsLoading(false);
        }
    };

    /**
     * User Logout
     */
    const logout = () => {
        authService.logout();
        setUser(null);
        setToken(null);
        wsManager.disconnect();
    };

    /**
     * Role-Based Access Control Helper
     * @param {string | string[]} allowedRoles e.g. "ADMIN" or ["ADMIN", "COMMANDER", "DISPATCHER"]
     */
    const hasRole = (allowedRoles) => {
        if (!user || !user.role) return false;
        if (Array.isArray(allowedRoles)) {
            return allowedRoles.includes(user.role);
        }
        return user.role === allowedRoles;
    };

    const value = {
        user,
        token,
        isAuthenticated: Boolean(user && token),
        isLoading,
        login,
        register,
        logout,
        hasRole,
        role: user?.role || "GUEST"
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}

export default AuthContext;
