/**
 * AegisAI Inject Simulated Incident Modal
 * Injects synthetic emergency events directly into the Digital Twin virtual city.
 */

import React, { useState } from "react";
import simulationService from "../../services/simulationService";

const QUICK_LOCATIONS = [
    { label: "Sector 17 Commercial Hub", lat: 30.7399, lon: 76.7830 },
    { label: "Sector 22 Residential Core", lat: 30.7339, lon: 76.7727 },
    { label: "Industrial Zone 1", lat: 30.7150, lon: 76.7600 },
    { label: "PGI Medical Corridor", lat: 30.7646, lon: 76.7754 },
    { label: "Mohali Gateway", lat: 30.7046, lon: 76.7179 },
];

export function SpawnIncidentModal({ isOpen, onClose, onIncidentSpawned }) {
    const [incidentType, setIncidentType] = useState("FIRE");
    const [severity, setSeverity] = useState("HIGH");
    const [latitude, setLatitude] = useState(30.7399);
    const [longitude, setLongitude] = useState(76.7830);
    const [radius, setRadius] = useState(1000);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    if (!isOpen) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const payload = {
                incident_type: incidentType,
                severity: severity,
                latitude: Number(latitude),
                longitude: Number(longitude),
                affected_radius_meters: Number(radius),
            };

            await simulationService.spawnIncident(payload);
            if (onIncidentSpawned) {
                onIncidentSpawned();
            }
            onClose();
        } catch (err) {
            console.error("Failed to spawn incident:", err);
            setError(err?.response?.data?.message || err?.message || "Failed to spawn incident in simulation.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="auth-modal-card" onClick={(e) => e.stopPropagation()}>
                {/* HEADER */}
                <div className="auth-modal-header">
                    <div>
                        <h2>⚡ Inject Simulated Incident</h2>
                        <p>Trigger a simulated disaster event to test response times and routing.</p>
                    </div>
                    <button className="modal-close-btn" onClick={onClose}>✕</button>
                </div>

                {/* QUICK LOCATION SHORTCUTS */}
                <div className="quick-personas-section">
                    <div className="section-label">📍 Quick Coordinates Preset:</div>
                    <div className="personas-grid">
                        {QUICK_LOCATIONS.map((loc) => (
                            <button
                                key={loc.label}
                                type="button"
                                className="persona-chip"
                                onClick={() => {
                                    setLatitude(loc.lat);
                                    setLongitude(loc.lon);
                                }}
                            >
                                <span className="persona-icon">🎯</span>
                                <div className="persona-meta">
                                    <strong>{loc.label}</strong>
                                    <span className="badge-mini">{loc.lat.toFixed(3)}, {loc.lon.toFixed(3)}</span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>

                {error && (
                    <div className="auth-error-alert">
                        ⚠️ {error}
                    </div>
                )}

                <form className="auth-form" onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Disaster Classification</label>
                        <select value={incidentType} onChange={(e) => setIncidentType(e.target.value)}>
                            <option value="FIRE">🔥 Urban / Structural Fire</option>
                            <option value="FLOOD">🌊 Flash Flood / Inundation</option>
                            <option value="EARTHQUAKE">🌋 Seismic Event / Earthquake</option>
                            <option value="GAS_LEAK">☣️ Toxic Chemical / Gas Leak</option>
                            <option value="BUILDING_COLLAPSE">🏚️ Structural Collapse</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Severity Level</label>
                        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                            <option value="LOW">🟡 LOW (Local Alert)</option>
                            <option value="MEDIUM">🟠 MEDIUM (Regional Impact)</option>
                            <option value="HIGH">🔴 HIGH (Mass Casualty Potential)</option>
                            <option value="CRITICAL">🟣 CRITICAL (Catastrophic Major Disaster)</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label>Affected Blast / Dispersion Radius: {(radius / 1000).toFixed(1)} km</label>
                        <input
                            type="range"
                            min="300"
                            max="5000"
                            step="100"
                            value={radius}
                            onChange={(e) => setRadius(e.target.value)}
                        />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                        <div className="form-group">
                            <label>Latitude</label>
                            <input
                                type="number"
                                step="any"
                                value={latitude}
                                onChange={(e) => setLatitude(e.target.value)}
                                required
                            />
                        </div>
                        <div className="form-group">
                            <label>Longitude</label>
                            <input
                                type="number"
                                step="any"
                                value={longitude}
                                onChange={(e) => setLongitude(e.target.value)}
                                required
                            />
                        </div>
                    </div>

                    <button
                        type="submit"
                        className="auth-submit-btn"
                        disabled={loading}
                    >
                        {loading ? "Spawning Event..." : "💥 Inject Simulated Event"}
                    </button>
                </form>
            </div>
        </div>
    );
}

export default SpawnIncidentModal;
