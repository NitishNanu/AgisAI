/**
 * AegisAI Header Navigation Bar
 * Features:
 * - Real-Time Telemetry Connection Indicator (LIVE / RECONNECTING / OFFLINE)
 * - User Role Clearance Badge
 * - Authenticated User Profile Dropdown & Logout
 * - Auth Modal trigger
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import wsManager from "../../services/websocketManager";

export function Navbar({ onOpenAuthModal }) {
    const { user, isAuthenticated, logout, role } = useAuth();
    const [wsStatus, setWsStatus] = useState(wsManager.getStatus());

    useEffect(() => {
        const unsubscribe = wsManager.onStatusChange((status) => {
            setWsStatus(status);
        });
        return unsubscribe;
    }, []);

    const getStatusIndicator = () => {
        switch (wsStatus) {
            case "CONNECTED":
                return {
                    label: "LIVE TELEMETRY",
                    className: "status-live",
                    dotClass: "dot-green",
                    icon: "🟢"
                };
            case "CONNECTING":
            case "RECONNECTING":
                return {
                    label: "RECONNECTING",
                    className: "status-reconnecting",
                    dotClass: "dot-yellow",
                    icon: "🟡"
                };
            default:
                return {
                    label: "OFFLINE",
                    className: "status-offline",
                    dotClass: "dot-red",
                    icon: "🔴"
                };
        }
    };

    const statusInfo = getStatusIndicator();

    const getRoleBadgeClass = (userRole) => {
        switch (userRole) {
            case "ADMIN":
                return "role-admin";
            case "COMMANDER":
                return "role-commander";
            case "DISPATCHER":
                return "role-dispatcher";
            case "MEDIC":
                return "role-medic";
            case "RESPONDER":
                return "role-responder";
            default:
                return "role-citizen";
        }
    };

    return (
        <header className="navbar-container">
            <div className="navbar-brand">
                <div className="brand-logo">🛡️</div>
                <div className="brand-text">
                    <h1>AegisAI</h1>
                    <span className="brand-subtitle">Emergency Response & Digital Twin Platform</span>
                </div>
            </div>

            <div className="navbar-actions">
                {/* WEBSOCKET REAL-TIME STATUS INDICATOR */}
                <div className={`telemetry-status-badge ${statusInfo.className}`} title={`WebSocket Telemetry Stream: ${wsStatus}`}>
                    <span className={`status-pulsing-dot ${statusInfo.dotClass}`} />
                    <span className="status-label">{statusInfo.label}</span>
                </div>

                {/* USER PROFILE & AUTH CONTROLS */}
                {isAuthenticated && user ? (
                    <div className="user-profile-widget">
                        <div className="user-info">
                            <span className="user-name">{user.name}</span>
                            <span className={`role-badge ${getRoleBadgeClass(role)}`}>
                                {role}
                            </span>
                        </div>
                        <button
                            className="btn-logout"
                            onClick={logout}
                            title="Sign out of AegisAI"
                        >
                            🚪 Sign Out
                        </button>
                    </div>
                ) : (
                    <button
                        className="btn-signin-primary"
                        onClick={onOpenAuthModal}
                    >
                        🔑 Sign In / Clearance
                    </button>
                )}
            </div>
        </header>
    );
}

export default Navbar;
