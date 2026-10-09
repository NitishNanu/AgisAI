/**
 * AegisAI Mission Control — Supercharged Operational Command Center
 * Features:
 * - 6-Stage Mission Lifecycle Stepper
 * - AI SITREP (Situation Report) synthesis via MissionOperationsAgent
 * - Dynamic Medevac Trauma ER Hospital Transfer Routing
 * - Live Anomaly & Bottleneck alerts HUD
 * - Status filtering & Interactive Route Focus
 */

import React, { useState } from "react";
import { missionService } from "../services/missionService";

const LIFECYCLE_STEPS = [
    { key: "DISPATCHED", label: "Dispatched", icon: "📋" },
    { key: "EN_ROUTE", label: "En Route", icon: "🚚" },
    { key: "ARRIVED", label: "On Scene", icon: "🎯" },
    { key: "OPERATIONAL", label: "Triage & Rescue", icon: "⚙️" },
    { key: "MEDEVAC", label: "Hospital Medevac", icon: "🏥" },
    { key: "COMPLETED", label: "Completed", icon: "✅" },
];

export function MissionControl({
    missions = [],
    onUpdateStatus,
    onSelectMission,
    selectedMissionId,
}) {
    const [filterStatus, setFilterStatus] = useState("ALL");
    const [sitrepModalOpen, setSitrepModalOpen] = useState(false);
    const [activeSitrep, setActiveSitrep] = useState(null);
    const [loadingSitrep, setLoadingSitrep] = useState(false);

    const [medevacModalOpen, setMedevacModalOpen] = useState(false);
    const [activeMedevac, setActiveMedevac] = useState(null);
    const [loadingMedevac, setLoadingMedevac] = useState(false);

    const [actionMessage, setActionMessage] = useState(null);

    const showNotification = (msg) => {
        setActionMessage(msg);
        setTimeout(() => setActionMessage(null), 3500);
    };

    const getNextStatus = (currentStatus) => {
        switch (currentStatus) {
            case "ASSIGNED":
            case "DISPATCHED":
                return "EN_ROUTE";
            case "EN_ROUTE":
                return "ARRIVED";
            case "ARRIVED":
                return "OPERATIONAL";
            case "OPERATIONAL":
                return "MEDEVAC";
            case "MEDEVAC":
                return "COMPLETED";
            default:
                return "COMPLETED";
        }
    };

    const getNextStatusLabel = (currentStatus) => {
        switch (currentStatus) {
            case "ASSIGNED":
            case "DISPATCHED":
                return "🚚 Mark En Route";
            case "EN_ROUTE":
                return "🎯 Confirm On Scene";
            case "ARRIVED":
                return "⚙️ Begin Triage / Extrication";
            case "OPERATIONAL":
                return "🏥 Initiate Medevac Transport";
            case "MEDEVAC":
                return "✅ Complete Mission";
            default:
                return "✅ Complete Mission";
        }
    };

    const handleGenerateSITREP = async (assignmentId) => {
        setLoadingSitrep(true);
        setSitrepModalOpen(true);
        try {
            const data = await missionService.getMissionSITREP(assignmentId);
            setActiveSitrep(data);
        } catch (err) {
            console.error("SITREP error:", err);
            showNotification("⚠️ Failed to generate SITREP.");
        } finally {
            setLoadingSitrep(false);
        }
    };

    const handleOpenMedevac = async (assignmentId) => {
        setLoadingMedevac(true);
        setMedevacModalOpen(true);
        try {
            const data = await missionService.getMedevacRecommendation(assignmentId);
            setActiveMedevac(data);
        } catch (err) {
            console.error("Medevac error:", err);
            showNotification("⚠️ Failed to load Medevac plan.");
        } finally {
            setLoadingMedevac(false);
        }
    };

    const filteredMissions = missions.filter((m) => {
        if (filterStatus === "ALL") return true;
        if (filterStatus === "ACTIVE") return m.status !== "COMPLETED" && m.status !== "CANCELLED";
        if (filterStatus === "EN_ROUTE") return m.status === "EN_ROUTE" || m.status === "DISPATCHED";
        if (filterStatus === "ON_SCENE") return m.status === "ARRIVED" || m.status === "OPERATIONAL";
        if (filterStatus === "MEDEVAC") return m.status === "MEDEVAC";
        if (filterStatus === "COMPLETED") return m.status === "COMPLETED";
        return true;
    });

    return (
        <div className="mission-control-panel">
            {/* ── HEADER ── */}
            <div className="panel-header" style={{ marginBottom: 16 }}>
                <span className="panel-icon">🚨</span>
                <div>
                    <h2 className="panel-title">Active Mission Control</h2>
                    <p className="panel-subtitle">Real-time tactical fleet dispatch & in-flight surveillance</p>
                </div>
            </div>

            {/* NOTIFICATION TOAST */}
            {actionMessage && (
                <div className="toast-notification">
                    <span>{actionMessage}</span>
                </div>
            )}

            {/* ── FILTER CHIPS ── */}
            <div className="mission-filter-bar">
                {["ALL", "ACTIVE", "EN_ROUTE", "ON_SCENE", "MEDEVAC", "COMPLETED"].map((f) => (
                    <button
                        key={f}
                        className={`filter-chip ${filterStatus === f ? "active" : ""}`}
                        onClick={() => setFilterStatus(f)}
                    >
                        {f.replace("_", " ")}
                    </button>
                ))}
            </div>

            {filteredMissions.length === 0 ? (
                <div className="empty-state">
                    <span className="empty-icon">🛡️</span>
                    <p>No missions found for this filter.</p>
                    <span>Dispatch a rescue team from Active Incidents to initiate a mission.</span>
                </div>
            ) : (
                <div className="missions-list">
                    {filteredMissions.map((mission) => {
                        const isSelected = selectedMissionId === mission.assignment_id;
                        const status = mission.status || "DISPATCHED";

                        return (
                            <div
                                key={mission.assignment_id}
                                className={`mission-card ${isSelected ? "selected-mission" : ""}`}
                            >
                                <div className="mission-header">
                                    <div className="mission-title">
                                        <h3>🚨 {mission.disaster?.title || "Emergency Incident"}</h3>
                                        <span className={`severity-badge ${mission.disaster?.severity?.toLowerCase() || "high"}`}>
                                            {mission.disaster?.severity || "HIGH"}
                                        </span>
                                    </div>
                                    <span className={`mission-status-badge status-${status.toLowerCase().replace(/_/g, "-")}`}>
                                        {status}
                                    </span>
                                </div>

                                {/* LIFECYCLE STEPPER */}
                                <div className="mission-stepper">
                                    {LIFECYCLE_STEPS.map((step, idx) => {
                                        const currentIdx = LIFECYCLE_STEPS.findIndex((s) => s.key === status);
                                        const isDone = currentIdx > idx;
                                        const isCurrent = currentIdx === idx || (status === "ASSIGNED" && idx === 0);

                                        return (
                                            <div
                                                key={step.key}
                                                className={`step-item ${isDone ? "done" : ""} ${isCurrent ? "current" : ""}`}
                                                title={step.label}
                                            >
                                                <div className="step-circle">{step.icon}</div>
                                                <span className="step-text">{step.label}</span>
                                            </div>
                                        );
                                    })}
                                </div>

                                <div className="mission-body">
                                    <div className="mission-detail-row">
                                        <span>🚑 Response Team:</span>
                                        <strong>{mission.team?.name || "Unit"}</strong>
                                    </div>

                                    <div className="mission-detail-row">
                                        <span>🚙 Vehicle & Crew:</span>
                                        <span>{mission.team?.vehicle_type || "Emergency Squad"} ({mission.team?.members || 4} crew)</span>
                                    </div>

                                    <div className="mission-route-stats">
                                        <div className="stat-pill">
                                            <span>🚗 Road Distance</span>
                                            <strong>{mission.distance_km || "—"} km</strong>
                                        </div>

                                        <div className="stat-pill">
                                            <span>⏱ Est. ETA</span>
                                            <strong>{mission.eta_minutes || "—"} min</strong>
                                        </div>
                                    </div>
                                </div>

                                {/* ACTION BUTTONS */}
                                <div className="mission-actions-grid">
                                    {onSelectMission && (
                                        <button
                                            className="action-btn focus-btn"
                                            onClick={() => onSelectMission(mission)}
                                        >
                                            🗺️ Focus Route
                                        </button>
                                    )}

                                    <button
                                        className="action-btn ai-sitrep-btn"
                                        onClick={() => handleGenerateSITREP(mission.assignment_id)}
                                    >
                                        🧠 AI SITREP
                                    </button>

                                    <button
                                        className="action-btn medevac-btn"
                                        onClick={() => handleOpenMedevac(mission.assignment_id)}
                                    >
                                        🏥 Medevac ER
                                    </button>

                                    {onUpdateStatus && status !== "COMPLETED" && (
                                        <button
                                            className="action-btn progress-btn"
                                            onClick={() => onUpdateStatus(mission.assignment_id, getNextStatus(status))}
                                        >
                                            {getNextStatusLabel(status)}
                                        </button>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {/* ── AI SITREP MODAL ── */}
            {sitrepModalOpen && (
                <div className="modal-backdrop" onClick={() => setSitrepModalOpen(false)}>
                    <div className="modal-box sitrep-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <span>🧠</span>
                                <h3>AI Tactical Mission SITREP</h3>
                            </div>
                            <button className="modal-close-btn" onClick={() => setSitrepModalOpen(false)}>✕</button>
                        </div>

                        {loadingSitrep ? (
                            <div className="modal-loading">
                                <div className="spinner" />
                                <p>MissionOperationsAgent is auditing telemetry & formulating tactical SITREP...</p>
                            </div>
                        ) : activeSitrep ? (
                            <div className="sitrep-content">
                                <div className="sitrep-banner">
                                    <div>
                                        <h4>{activeSitrep.incident_title}</h4>
                                        <p>Unit: <strong>{activeSitrep.team_name}</strong> ({activeSitrep.vehicle_type})</p>
                                    </div>
                                    <div className="sitrep-metrics">
                                        <span>⏱ Elapsed: {activeSitrep.elapsed_minutes}m</span>
                                        <span>🚗 Distance Left: {activeSitrep.distance_remaining_km} km</span>
                                    </div>
                                </div>

                                {/* ANOMALY AUDIT */}
                                {activeSitrep.anomalies?.length > 0 && (
                                    <div className="sitrep-anomalies-section">
                                        <h5>⚠️ Telemetry Anomalies Detected ({activeSitrep.anomalies.length})</h5>
                                        {activeSitrep.anomalies.map((anom, idx) => (
                                            <div key={idx} className={`anomaly-card ${anom.severity.toLowerCase()}`}>
                                                <div className="anomaly-header">
                                                    <strong>{anom.anomaly_type}</strong>
                                                    <span className="anomaly-badge">{anom.severity}</span>
                                                </div>
                                                <p>{anom.description}</p>
                                                <span className="anomaly-remedy">💡 Remedy: {anom.recommended_action}</span>
                                            </div>
                                        ))}
                                    </div>
                                )}

                                {/* OPERATIONAL MILESTONES */}
                                <div className="sitrep-section">
                                    <h5>📋 Operational Milestones</h5>
                                    <ul className="milestone-timeline">
                                        {activeSitrep.operational_milestones?.map((m, idx) => (
                                            <li key={idx}><span>✓</span> {m}</li>
                                        ))}
                                    </ul>
                                </div>

                                {/* TACTICAL NEXT STEPS */}
                                <div className="sitrep-section">
                                    <h5>🎯 Tactical Directives & Next Steps</h5>
                                    <ul className="next-steps-list">
                                        {activeSitrep.tactical_next_steps?.map((step, idx) => (
                                            <li key={idx}>👉 {step}</li>
                                        ))}
                                    </ul>
                                </div>

                                {activeSitrep.backup_recommended && (
                                    <div className="backup-alert-box">
                                        <span>🚨 Backup Unit Recommended: <strong>{activeSitrep.recommended_backup_type}</strong></span>
                                        <button
                                            className="request-backup-btn"
                                            onClick={() => showNotification(`Requested backup ${activeSitrep.recommended_backup_type}!`)}
                                        >
                                            Dispatch Reinforcement
                                        </button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <p>No SITREP data available.</p>
                        )}
                    </div>
                </div>
            )}

            {/* ── MEDEVAC HOSPITAL MODAL ── */}
            {medevacModalOpen && (
                <div className="modal-backdrop" onClick={() => setMedevacModalOpen(false)}>
                    <div className="modal-box medevac-modal" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <span>🏥</span>
                                <h3>Trauma Medevac Hospital Routing</h3>
                            </div>
                            <button className="modal-close-btn" onClick={() => setMedevacModalOpen(false)}>✕</button>
                        </div>

                        {loadingMedevac ? (
                            <div className="modal-loading">
                                <div className="spinner" />
                                <p>Evaluating ICU bed capacity & calculating road transit times...</p>
                            </div>
                        ) : activeMedevac ? (
                            <div className="medevac-content">
                                <div className="medevac-triage-card">
                                    <p>{activeMedevac.triage_notes}</p>
                                    <span className="patient-count-badge">
                                        Critical Patients: <strong>{activeMedevac.critical_patients_count}</strong>
                                    </span>
                                </div>

                                <h4>Primary Recommended Facility</h4>
                                <div className="hospital-card best-facility">
                                    <div className="hosp-info">
                                        <h5>🏆 {activeMedevac.selected_hospital.hospital_name}</h5>
                                        <span>{activeMedevac.selected_hospital.trauma_level}</span>
                                        <div className="hosp-stats">
                                            <span>🛏️ Total Available: <strong>{activeMedevac.selected_hospital.available_beds}</strong></span>
                                            <span>🩺 ICU Beds: <strong>{activeMedevac.selected_hospital.icu_beds_available}</strong></span>
                                            <span>🚗 Distance: <strong>{activeMedevac.selected_hospital.distance_km} km</strong> ({activeMedevac.selected_hospital.eta_minutes} min)</span>
                                        </div>
                                    </div>
                                    <div className="hosp-action">
                                        <button
                                            className="transfer-btn"
                                            onClick={() => {
                                                onUpdateStatus && onUpdateStatus(activeMedevac.assignment_id, "MEDEVAC");
                                                setMedevacModalOpen(false);
                                                showNotification(`In-transit to ${activeMedevac.selected_hospital.hospital_name}!`);
                                            }}
                                        >
                                            🚑 Route Medevac
                                        </button>
                                    </div>
                                </div>

                                {activeMedevac.alternative_hospitals?.length > 0 && (
                                    <>
                                        <h4 style={{ marginTop: 16 }}>Secondary Alternative Facilities</h4>
                                        <div className="alt-hospitals-list">
                                            {activeMedevac.alternative_hospitals.map((hosp) => (
                                                <div key={hosp.hospital_id} className="hospital-card">
                                                    <div className="hosp-info">
                                                        <h5>{hosp.hospital_name}</h5>
                                                        <span>{hosp.trauma_level} • {hosp.distance_km} km • {hosp.available_beds} beds ({hosp.icu_beds_available} ICU)</span>
                                                    </div>
                                                    <button
                                                        className="alt-transfer-btn"
                                                        onClick={() => {
                                                            onUpdateStatus && onUpdateStatus(activeMedevac.assignment_id, "MEDEVAC");
                                                            setMedevacModalOpen(false);
                                                            showNotification(`Diverted to ${hosp.hospital_name}!`);
                                                        }}
                                                    >
                                                        Divert Here
                                                    </button>
                                                </div>
                                            ))}
                                        </div>
                                    </>
                                )}
                            </div>
                        ) : (
                            <p>No Medevac facilities found.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

export default MissionControl;