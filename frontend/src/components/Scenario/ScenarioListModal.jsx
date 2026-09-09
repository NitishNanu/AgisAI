/**
 * AegisAI Scenario Library Modal
 * Browse, clone, launch, and manage saved disaster scenario blueprints.
 */

import React, { useState, useEffect } from "react";
import scenarioService from "../../services/scenarioService";

export function ScenarioListModal({ isOpen, onClose, onLaunchScenario, onLoadScenario }) {
    const [scenarios, setScenarios] = useState([]);
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(false);

    const loadScenarios = async () => {
        setLoading(true);
        try {
            const data = await scenarioService.listScenarios({ search: search || undefined });
            setScenarios(data);
        } catch (err) {
            console.error("Failed to load scenario library:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (isOpen) {
            loadScenarios();
        }
    }, [isOpen, search]);

    if (!isOpen) return null;

    const handleClone = async (id, name) => {
        try {
            const cloned = await scenarioService.cloneScenario(id, `${name} (Branch)`);
            alert(`Scenario cloned: "${cloned.name}"`);
            loadScenarios();
        } catch (err) {
            alert("Failed to clone scenario.");
        }
    };

    const handleArchive = async (id) => {
        if (!confirm("Are you sure you want to archive this scenario blueprint?")) return;
        try {
            await scenarioService.archiveScenario(id);
            loadScenarios();
        } catch (err) {
            alert("Failed to archive scenario.");
        }
    };

    const handleLaunch = async (scenario) => {
        try {
            const run = await scenarioService.launchScenario(scenario.id);
            alert(`🚀 Scenario launched! Simulation Run ID: ${run.id}`);
            if (onLaunchScenario) {
                onLaunchScenario(scenario, run);
            }
            onClose();
        } catch (err) {
            alert("Failed to launch scenario simulation.");
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="scenario-library-modal" onClick={(e) => e.stopPropagation()}>
                {/* HEADER */}
                <div className="auth-modal-header">
                    <div>
                        <h2>📁 Disaster Scenario Blueprint Library</h2>
                        <p>Manage, clone, branch, and launch your saved simulation scenarios.</p>
                    </div>
                    <button className="modal-close-btn" onClick={onClose}>✕</button>
                </div>

                {/* SEARCH BAR */}
                <div className="library-search-bar">
                    <input
                        type="text"
                        placeholder="Search scenario blueprints by title or hazard..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                    />
                </div>

                {/* SCENARIOS LIST */}
                <div className="library-list-container">
                    {loading ? (
                        <div className="preview-placeholder">
                            <div className="spinner" />
                            <p>Loading scenario blueprints...</p>
                        </div>
                    ) : scenarios.length === 0 ? (
                        <div className="no-events-box" style={{ padding: 30 }}>
                            <p>No scenario blueprints found.</p>
                            <span>Create and save custom disaster blueprints in the Scenario Designer.</span>
                        </div>
                    ) : (
                        <div className="scenarios-grid">
                            {scenarios.map((sc) => (
                                <div key={sc.id} className="scenario-card-item">
                                    <div className="card-top-row">
                                        <span className="hazard-tag">🚨 {sc.disaster_type}</span>
                                        <span className={`badge-mini ${sc.severity?.toLowerCase()}`}>{sc.severity}</span>
                                        <span className="status-tag">{sc.status}</span>
                                    </div>
                                    <h4>{sc.name}</h4>
                                    <p className="card-desc">{sc.description || "No description provided."}</p>

                                    <div className="card-meta-row">
                                        <span>👥 {sc.population_count?.toLocaleString()} pop</span>
                                        <span>⭕ {sc.radius_km} km</span>
                                        <span>⏱ {sc.simulation_duration_minutes} min</span>
                                        <span>⚡ {sc.simulation_speed}x speed</span>
                                    </div>

                                    <div className="card-actions-row">
                                        <button className="btn-card-launch" onClick={() => handleLaunch(sc)}>
                                            🚀 Launch
                                        </button>
                                        <button className="btn-card-clone" onClick={() => handleClone(sc.id, sc.name)} title="Clone scenario for parameter variation">
                                            📑 Clone
                                        </button>
                                        <button className="btn-card-delete" onClick={() => handleArchive(sc.id)} title="Archive blueprint">
                                            🗑️ Archive
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ScenarioListModal;
