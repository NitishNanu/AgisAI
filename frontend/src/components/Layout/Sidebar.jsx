/**
 * AegisAI Premium Sidebar Navigation
 * Features:
 * - Collapsible icon-only / full-width modes
 * - Section navigation with live KPI badges
 * - WebSocket real-time status
 * - User profile & role badge
 * - Auth trigger
 */

import React, { useState, useEffect } from "react";
import { useAuth } from "../../context/AuthContext";
import wsManager from "../../services/websocketManager";

const NAV_ITEMS = [
    {
        id: "INCIDENTS",
        label: "Incidents",
        icon: "🚨",
        desc: "Active disasters & smart dispatch",
        badge: null, // filled dynamically
    },
    {
        id: "MISSIONS",
        label: "Missions",
        icon: "📡",
        desc: "Active mission control & status",
        badge: null,
    },
    {
        id: "SCENARIO",
        label: "Scenario Studio",
        icon: "🛠️",
        desc: "Design & launch custom scenarios",
        badge: null,
    },
    {
        id: "SIMULATION",
        label: "Digital Twin",
        icon: "🌐",
        desc: "City simulation telemetry & HUD",
        badge: null,
    },
    {
        id: "PREDICTIONS",
        label: "Predictive AI",
        icon: "🔮",
        desc: "AI-powered disaster forecasting",
        badge: null,
    },
    {
        id: "ANALYTICS",
        label: "Analytics",
        icon: "📊",
        desc: "Operational metrics & reports",
        badge: "NEW",
    },
    {
        id: "RESOURCES",
        label: "Resources",
        icon: "🏥",
        desc: "Hospitals, shelters & rescue fleet",
        badge: null,
    },
    {
        id: "SETTINGS",
        label: "Settings",
        icon: "⚙️",
        desc: "System configuration & preferences",
        badge: null,
    },
];

const ROLE_COLORS = {
    ADMIN: "#f43f5e",
    COMMANDER: "#f97316",
    DISPATCHER: "#3b82f6",
    MEDIC: "#22c55e",
    RESPONDER: "#a855f7",
    CITIZEN: "#6b7280",
};

export function Sidebar({
    activeTab,
    onTabChange,
    onOpenAuthModal,
    onOpenLibrary,
    onOpenWhatIf,
    onOpenSpawnModal,
    disastersCount = 0,
    missionsCount = 0,
}) {
    const { user, isAuthenticated, logout, role } = useAuth();
    const [collapsed, setCollapsed] = useState(false);
    const [wsStatus, setWsStatus] = useState(wsManager.getStatus());

    useEffect(() => {
        const unsub = wsManager.onStatusChange(setWsStatus);
        return unsub;
    }, []);

    const wsIndicator = {
        CONNECTED: { label: "LIVE", color: "#22c55e", pulse: true },
        CONNECTING: { label: "CONNECTING", color: "#f59e0b", pulse: true },
        RECONNECTING: { label: "RECONNECTING", color: "#f59e0b", pulse: true },
        DISCONNECTED: { label: "OFFLINE", color: "#ef4444", pulse: false },
        ERROR: { label: "ERROR", color: "#ef4444", pulse: false },
    }[wsStatus] || { label: "OFFLINE", color: "#ef4444", pulse: false };

    // Inject live badge counts
    const navWithBadges = NAV_ITEMS.map((item) => {
        if (item.id === "INCIDENTS" && disastersCount > 0)
            return { ...item, badge: disastersCount, badgeAlert: true };
        if (item.id === "MISSIONS" && missionsCount > 0)
            return { ...item, badge: missionsCount, badgeAlert: false };
        return item;
    });

    return (
        <aside className={`aegis-sidebar ${collapsed ? "collapsed" : ""}`}>
            {/* ── BRAND ── */}
            <div className="sidebar-brand">
                <div className="brand-icon-wrap">🛡️</div>
                {!collapsed && (
                    <div className="brand-text-wrap">
                        <span className="brand-title">AegisAI</span>
                        <span className="brand-sub">Emergency Response</span>
                    </div>
                )}
                <button
                    className="sidebar-collapse-btn"
                    onClick={() => setCollapsed(!collapsed)}
                    title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
                >
                    {collapsed ? "▶" : "◀"}
                </button>
            </div>

            {/* ── WS STATUS ── */}
            <div className={`sidebar-ws-status ${collapsed ? "collapsed" : ""}`}>
                <span
                    className={`ws-dot ${wsIndicator.pulse ? "pulse" : ""}`}
                    style={{ background: wsIndicator.color }}
                />
                {!collapsed && (
                    <span className="ws-label" style={{ color: wsIndicator.color }}>
                        {wsIndicator.label}
                    </span>
                )}
            </div>

            {/* ── SECTION LABEL ── */}
            {!collapsed && <div className="sidebar-section-label">NAVIGATION</div>}

            {/* ── NAV ITEMS ── */}
            <nav className="sidebar-nav">
                {navWithBadges.map((item) => (
                    <button
                        key={item.id}
                        className={`sidebar-nav-item ${activeTab === item.id ? "active" : ""}`}
                        onClick={() => onTabChange(item.id)}
                        title={collapsed ? `${item.label} — ${item.desc}` : ""}
                    >
                        <span className="nav-icon">{item.icon}</span>
                        {!collapsed && (
                            <div className="nav-text">
                                <span className="nav-label">{item.label}</span>
                                <span className="nav-desc">{item.desc}</span>
                            </div>
                        )}
                        {item.badge !== null && (
                            <span
                                className={`nav-badge ${item.badgeAlert ? "badge-alert" : "badge-info"}`}
                            >
                                {item.badge}
                            </span>
                        )}
                    </button>
                ))}
            </nav>

            {/* ── QUICK ACTIONS ── */}
            {!collapsed && (
                <>
                    <div className="sidebar-section-label" style={{ marginTop: 8 }}>QUICK ACTIONS</div>
                    <div className="sidebar-quick-actions">
                        <button className="quick-action-btn" onClick={onOpenSpawnModal} title="Spawn Incident">
                            <span>⚡</span> Spawn Incident
                        </button>
                        <button className="quick-action-btn" onClick={onOpenWhatIf} title="What-If Scenario">
                            <span>🔬</span> What-If Analysis
                        </button>
                        <button className="quick-action-btn" onClick={onOpenLibrary} title="Scenario Library">
                            <span>📚</span> Scenario Library
                        </button>
                    </div>
                </>
            )}

            {/* ── SPACER ── */}
            <div className="sidebar-spacer" />

            {/* ── USER PROFILE ── */}
            <div className={`sidebar-user ${collapsed ? "collapsed" : ""}`}>
                {isAuthenticated && user ? (
                    <>
                        <div className="user-avatar" style={{ background: ROLE_COLORS[role] || "#6b7280" }}>
                            {(user.name || role || "?")[0].toUpperCase()}
                        </div>
                        {!collapsed && (
                            <div className="user-details">
                                <span className="user-name-text">{user.name}</span>
                                <span
                                    className="user-role-badge"
                                    style={{
                                        background: ROLE_COLORS[role] + "33",
                                        color: ROLE_COLORS[role] || "#6b7280",
                                        border: `1px solid ${ROLE_COLORS[role] || "#6b7280"}55`,
                                    }}
                                >
                                    {role}
                                </span>
                            </div>
                        )}
                        {!collapsed && (
                            <button className="user-logout-btn" onClick={logout} title="Sign Out">
                                🚪
                            </button>
                        )}
                    </>
                ) : (
                    <button
                        className={`sidebar-signin-btn ${collapsed ? "icon-only" : ""}`}
                        onClick={onOpenAuthModal}
                        title="Sign In"
                    >
                        <span>🔑</span>
                        {!collapsed && " Sign In"}
                    </button>
                )}
            </div>
        </aside>
    );
}

export default Sidebar;
