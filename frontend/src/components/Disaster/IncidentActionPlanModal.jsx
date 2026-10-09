/**
 * AegisAI Incident Action Plan (IAP) Modal
 * Rendered when commander requests AI Incident Action Plan from IncidentCommanderAgent.
 */

import React from "react";

export function IncidentActionPlanModal({ isOpen, onClose, iap, loading, incidentTitle }) {
    if (!isOpen) return null;

    return (
        <div className="modal-backdrop" onClick={onClose}>
            <div className="modal-box iap-modal" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span>🧠</span>
                        <h3>Incident Action Plan (IAP) — {incidentTitle}</h3>
                    </div>
                    <button className="modal-close-btn" onClick={onClose}>✕</button>
                </div>

                {loading ? (
                    <div className="modal-loading">
                        <div className="spinner" />
                        <p>IncidentCommanderAgent is computing dynamic hazard envelopes & formulating IAP...</p>
                    </div>
                ) : iap ? (
                    <div className="iap-content">
                        {/* COMMANDER SUMMARY */}
                        <div className="iap-commander-directive">
                            <h4>🎖️ Commander Directive</h4>
                            <p>{iap.commander_summary}</p>
                            <div className="iap-meta-row">
                                <span>Perimeter: <strong>{iap.safety_perimeter_meters}m</strong></span>
                                <span>Evac Zone: <strong>{iap.evacuation_radius_meters}m</strong></span>
                                <span>Critical Patients: <strong>{iap.critical_patients}</strong></span>
                                <span>Containment: <strong>{iap.containment_status_pct}%</strong></span>
                            </div>
                        </div>

                        {/* STAGING AREA & REQUIRED FLEET */}
                        <div className="iap-two-col">
                            <div className="iap-card">
                                <h5>📍 Forward Staging Area (Upwind)</h5>
                                <strong>{iap.staging_area?.name}</strong>
                                <p>Coords: ({iap.staging_area?.latitude}, {iap.staging_area?.longitude})</p>
                                <span className="iap-sub">Access: {iap.staging_area?.access_corridor}</span>
                            </div>

                            <div className="iap-card">
                                <h5>🚑 Required Fleet Sizing</h5>
                                <div className="fleet-req-grid">
                                    {Object.entries(iap.required_resources || {}).map(([resType, count]) => (
                                        <div key={resType} className="fleet-req-pill">
                                            <span>{resType.replace(/_/g, " ")}:</span>
                                            <strong>{count}</strong>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* SECONDARY CASCADE RISKS */}
                        {iap.cascade_risks?.length > 0 && (
                            <div className="iap-section">
                                <h5>⚠️ Cascading Secondary Threat Matrix</h5>
                                <div className="cascade-grid">
                                    {iap.cascade_risks.map((risk, idx) => (
                                        <div key={idx} className="cascade-card">
                                            <div className="cascade-header">
                                                <strong>{risk.hazard_type.replace(/_/g, " ")}</strong>
                                                <span className="cascade-prob">{risk.probability_pct}% Prob</span>
                                            </div>
                                            <p>{risk.trigger_condition}</p>
                                            <span className="cascade-action">🛡️ Mitigation: {risk.mitigation_action}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* TACTICAL OBJECTIVES TIMELINE */}
                        <div className="iap-section">
                            <h5>🎯 Tactical Objectives by Phase</h5>
                            <div className="objectives-list">
                                {iap.tactical_objectives?.map((obj) => (
                                    <div key={obj.id} className={`objective-item ${obj.priority.toLowerCase()}`}>
                                        <div className="obj-phase-tag">{obj.phase} (T+{obj.target_time_minutes}m)</div>
                                        <div className="obj-main">
                                            <strong>[{obj.assigned_unit_type}]</strong> {obj.objective}
                                        </div>
                                        <span className="obj-priority">{obj.priority}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                ) : (
                    <p>No IAP data available.</p>
                )}
            </div>
        </div>
    );
}

export default IncidentActionPlanModal;
