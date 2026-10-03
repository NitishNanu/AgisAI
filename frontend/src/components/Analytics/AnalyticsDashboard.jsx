/**
 * AegisAI Analytics Dashboard
 * Operational metrics, response time trends, resource utilisation
 */

import React, { useEffect, useState } from "react";
import simulationService from "../../services/simulationService";

export function AnalyticsDashboard({ cityState, disasters = [], missions = [], rescueTeams = [] }) {
    const [simEvents, setSimEvents] = useState([]);

    useEffect(() => {
        simulationService.getSimulationEvents(20).then(setSimEvents).catch(() => {});
    }, []);

    const completedMissions = missions.filter((m) => m.status === "COMPLETED").length;
    const activeMissions = missions.filter((m) => m.status !== "COMPLETED").length;
    const availableTeams = rescueTeams.filter((t) => t.status === "AVAILABLE").length;
    const dispatchedTeams = rescueTeams.filter((t) => t.status === "DISPATCHED").length;

    const avgEta =
        missions.length > 0
            ? Math.round(missions.reduce((a, m) => a + (m.eta_minutes || 0), 0) / missions.length)
            : 0;

    const disasterTypes = disasters.reduce((acc, d) => {
        acc[d.disaster_type] = (acc[d.disaster_type] || 0) + 1;
        return acc;
    }, {});

    const severityBreakdown = disasters.reduce((acc, d) => {
        acc[d.severity] = (acc[d.severity] || 0) + 1;
        return acc;
    }, {});

    const SEVERITY_COLORS = {
        CRITICAL: "#ef4444",
        HIGH: "#f97316",
        MEDIUM: "#f59e0b",
        LOW: "#22c55e",
    };

    return (
        <div className="analytics-panel">
            <div className="panel-header">
                <span className="panel-icon">📊</span>
                <div>
                    <h2 className="panel-title">Operational Analytics</h2>
                    <p className="panel-subtitle">Real-time operational metrics & system health</p>
                </div>
            </div>

            {/* MISSION METRICS */}
            <div className="analytics-section">
                <h3 className="analytics-section-title">Mission Performance</h3>
                <div className="analytics-stat-grid">
                    <div className="analytics-stat">
                        <div className="analytics-stat-val text-primary">{activeMissions}</div>
                        <div className="analytics-stat-label">Active Missions</div>
                    </div>
                    <div className="analytics-stat">
                        <div className="analytics-stat-val text-success">{completedMissions}</div>
                        <div className="analytics-stat-label">Completed</div>
                    </div>
                    <div className="analytics-stat">
                        <div className="analytics-stat-val text-warning">{avgEta} min</div>
                        <div className="analytics-stat-label">Avg ETA</div>
                    </div>
                    <div className="analytics-stat">
                        <div className="analytics-stat-val">{missions.length}</div>
                        <div className="analytics-stat-label">Total Missions</div>
                    </div>
                </div>
            </div>

            {/* FLEET UTILISATION */}
            <div className="analytics-section">
                <h3 className="analytics-section-title">Fleet Utilisation</h3>
                <div className="fleet-bar-wrap">
                    <div className="fleet-bar-labels">
                        <span>Available: {availableTeams}</span>
                        <span>Deployed: {dispatchedTeams}</span>
                    </div>
                    <div className="fleet-bar-track">
                        <div
                            className="fleet-bar-fill available"
                            style={{
                                width: rescueTeams.length > 0
                                    ? `${(availableTeams / rescueTeams.length) * 100}%`
                                    : "0%",
                            }}
                        />
                        <div
                            className="fleet-bar-fill deployed"
                            style={{
                                width: rescueTeams.length > 0
                                    ? `${(dispatchedTeams / rescueTeams.length) * 100}%`
                                    : "0%",
                            }}
                        />
                    </div>
                    <div className="fleet-bar-legend">
                        <span><span className="legend-dot" style={{ background: "#22c55e" }} /> Available</span>
                        <span><span className="legend-dot" style={{ background: "#f97316" }} /> Deployed</span>
                        <span><span className="legend-dot" style={{ background: "#6b7280" }} /> Inactive</span>
                    </div>
                </div>
            </div>

            {/* DISASTER TYPE BREAKDOWN */}
            {Object.keys(disasterTypes).length > 0 && (
                <div className="analytics-section">
                    <h3 className="analytics-section-title">Incident Type Breakdown</h3>
                    <div className="breakdown-list">
                        {Object.entries(disasterTypes).map(([type, count]) => (
                            <div key={type} className="breakdown-item">
                                <span className="breakdown-label">{type.replace(/_/g, " ")}</span>
                                <div className="breakdown-bar-track">
                                    <div
                                        className="breakdown-bar-fill"
                                        style={{ width: `${(count / disasters.length) * 100}%` }}
                                    />
                                </div>
                                <span className="breakdown-count">{count}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* SEVERITY DISTRIBUTION */}
            {Object.keys(severityBreakdown).length > 0 && (
                <div className="analytics-section">
                    <h3 className="analytics-section-title">Severity Distribution</h3>
                    <div className="severity-pills">
                        {Object.entries(severityBreakdown).map(([sev, count]) => (
                            <div
                                key={sev}
                                className="severity-pill"
                                style={{
                                    background: (SEVERITY_COLORS[sev] || "#6b7280") + "22",
                                    border: `1px solid ${SEVERITY_COLORS[sev] || "#6b7280"}55`,
                                    color: SEVERITY_COLORS[sev] || "#6b7280",
                                }}
                            >
                                <strong>{count}</strong> {sev}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* DIGITAL TWIN CITIZEN STATUS */}
            {cityState && (
                <div className="analytics-section">
                    <h3 className="analytics-section-title">Citizen Status (Digital Twin)</h3>
                    <div className="citizen-status-grid">
                        {[
                            { label: "Safe", val: cityState.safe_citizens, color: "#22c55e" },
                            { label: "Endangered", val: cityState.endangered_citizens, color: "#ef4444" },
                            { label: "Evacuating", val: cityState.evacuating_citizens, color: "#f59e0b" },
                            { label: "Injured", val: cityState.injured_citizens, color: "#f97316" },
                            { label: "Rescued", val: cityState.rescued_citizens, color: "#3b82f6" },
                        ].map(({ label, val, color }) => (
                            <div key={label} className="citizen-stat-card" style={{ borderLeft: `3px solid ${color}` }}>
                                <div className="citizen-val" style={{ color }}>{val ?? 0}</div>
                                <div className="citizen-label">{label}</div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* RECENT SIMULATION EVENTS */}
            {simEvents.length > 0 && (
                <div className="analytics-section">
                    <h3 className="analytics-section-title">Recent Simulation Events</h3>
                    <div className="sim-event-log">
                        {simEvents.slice(0, 8).map((ev, i) => (
                            <div key={i} className="sim-event-row">
                                <span className="sim-event-tick">T{ev.tick}</span>
                                <span className="sim-event-type">{ev.event_type?.replace(/_/g, " ")}</span>
                                <span className="sim-event-desc">{ev.description}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}

export default AnalyticsDashboard;
