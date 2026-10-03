/**
 * AegisAI Resources Panel
 * Shows Hospitals, Shelters, and Rescue Fleet in one consolidated view
 */

import React, { useState } from "react";

const RESOURCE_TABS = [
    { id: "HOSPITALS", label: "Hospitals", icon: "🏥" },
    { id: "SHELTERS", label: "Shelters", icon: "🏠" },
    { id: "FLEET", label: "Rescue Fleet", icon: "🚑" },
];

export function ResourcesPanel({ hospitals = [], shelters = [], rescueTeams = [] }) {
    const [resourceTab, setResourceTab] = useState("HOSPITALS");

    return (
        <div className="resources-panel">
            <div className="panel-header">
                <span className="panel-icon">🏥</span>
                <div>
                    <h2 className="panel-title">Resources</h2>
                    <p className="panel-subtitle">Hospitals, shelters & rescue fleet status</p>
                </div>
            </div>

            {/* RESOURCE SUB-TABS */}
            <div className="resource-sub-tabs">
                {RESOURCE_TABS.map((t) => (
                    <button
                        key={t.id}
                        className={`resource-sub-tab ${resourceTab === t.id ? "active" : ""}`}
                        onClick={() => setResourceTab(t.id)}
                    >
                        {t.icon} {t.label}
                    </button>
                ))}
            </div>

            {/* HOSPITALS */}
            {resourceTab === "HOSPITALS" && (
                <div className="resource-list">
                    {hospitals.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-icon">🏥</span>
                            <p>No hospital data available.</p>
                        </div>
                    ) : (
                        hospitals.map((h) => {
                            const pct = h.total_beds > 0
                                ? Math.round(((h.available_beds ?? h.total_beds) / h.total_beds) * 100)
                                : 0;
                            const statusColor = pct > 50 ? "#22c55e" : pct > 20 ? "#f59e0b" : "#ef4444";
                            return (
                                <div key={h.id} className="resource-card">
                                    <div className="resource-card-header">
                                        <span className="resource-card-icon">🏥</span>
                                        <div className="resource-card-info">
                                            <strong>{h.name || "Hospital"}</strong>
                                            <span>{h.address || h.location || "Location N/A"}</span>
                                        </div>
                                        <div
                                            className="resource-status-dot"
                                            style={{ background: statusColor }}
                                            title={`${pct}% capacity free`}
                                        />
                                    </div>
                                    <div className="resource-bar-wrap">
                                        <div className="resource-bar-track">
                                            <div
                                                className="resource-bar-fill"
                                                style={{ width: `${pct}%`, background: statusColor }}
                                            />
                                        </div>
                                        <span className="resource-bar-label">
                                            {h.available_beds ?? "—"} / {h.total_beds ?? "—"} beds free
                                        </span>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            )}

            {/* SHELTERS */}
            {resourceTab === "SHELTERS" && (
                <div className="resource-list">
                    {shelters.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-icon">🏠</span>
                            <p>No shelter data available.</p>
                        </div>
                    ) : (
                        shelters.map((s) => {
                            const cap = s.current_occupancy && s.capacity
                                ? Math.round((s.current_occupancy / s.capacity) * 100)
                                : 0;
                            const isOpen = s.is_open !== false;
                            return (
                                <div key={s.id} className="resource-card">
                                    <div className="resource-card-header">
                                        <span className="resource-card-icon">🏠</span>
                                        <div className="resource-card-info">
                                            <strong>{s.name || "Shelter"}</strong>
                                            <span>{s.address || "Location N/A"}</span>
                                        </div>
                                        <span
                                            className="resource-open-badge"
                                            style={{
                                                background: isOpen ? "#22c55e22" : "#ef444422",
                                                color: isOpen ? "#22c55e" : "#ef4444",
                                                border: `1px solid ${isOpen ? "#22c55e55" : "#ef444455"}`,
                                            }}
                                        >
                                            {isOpen ? "OPEN" : "CLOSED"}
                                        </span>
                                    </div>
                                    <div className="resource-bar-wrap">
                                        <div className="resource-bar-track">
                                            <div
                                                className="resource-bar-fill"
                                                style={{
                                                    width: `${Math.min(cap, 100)}%`,
                                                    background: cap < 80 ? "#22c55e" : "#ef4444",
                                                }}
                                            />
                                        </div>
                                        <span className="resource-bar-label">
                                            {s.current_occupancy ?? 0} / {s.capacity ?? "—"} occupants
                                        </span>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            )}

            {/* RESCUE FLEET */}
            {resourceTab === "FLEET" && (
                <div className="resource-list">
                    {rescueTeams.length === 0 ? (
                        <div className="empty-state">
                            <span className="empty-icon">🚑</span>
                            <p>No rescue teams available.</p>
                        </div>
                    ) : (
                        rescueTeams.map((team) => {
                            const STATUS_COLOR = {
                                AVAILABLE: "#22c55e",
                                DISPATCHED: "#f97316",
                                EN_ROUTE: "#3b82f6",
                                ARRIVED: "#a855f7",
                                INACTIVE: "#6b7280",
                            };
                            const col = STATUS_COLOR[team.status] || "#6b7280";
                            return (
                                <div key={team.id} className="resource-card fleet-card">
                                    <div className="resource-card-header">
                                        <span className="resource-card-icon">🚑</span>
                                        <div className="resource-card-info">
                                            <strong>{team.name || team.team_name || "Unit"}</strong>
                                            <span>{team.vehicle_type || "Rescue Vehicle"} • {team.members || "—"} members</span>
                                        </div>
                                        <span
                                            className="fleet-status-badge"
                                            style={{
                                                background: col + "22",
                                                color: col,
                                                border: `1px solid ${col}55`,
                                            }}
                                        >
                                            {team.status || "UNKNOWN"}
                                        </span>
                                    </div>
                                </div>
                            );
                        })
                    )}
                </div>
            )}
        </div>
    );
}

export default ResourcesPanel;
