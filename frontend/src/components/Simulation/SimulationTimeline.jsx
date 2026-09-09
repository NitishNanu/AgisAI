/**
 * AegisAI Simulation Timeline & Checkpoint Manager
 */

import React, { useState, useEffect } from "react";
import simulationService from "../../services/simulationService";

export function SimulationTimeline({ currentTick = 0, isRunning = false, onTickSeek }) {
    const [checkpoints, setCheckpoints] = useState([]);
    const [checkpointName, setCheckpointName] = useState("");
    const [saving, setSaving] = useState(false);

    const handleCreateCheckpoint = async (e) => {
        e.preventDefault();
        if (!checkpointName.trim()) return;

        setSaving(true);
        try {
            await simulationService.createCheckpoint(checkpointName);
            setCheckpoints((prev) => [
                ...prev,
                { name: checkpointName, tick: currentTick, time: new Date().toLocaleTimeString() }
            ]);
            setCheckpointName("");
        } catch (err) {
            console.error("Failed to save checkpoint:", err);
            alert("Failed to save simulation checkpoint.");
        } finally {
            setSaving(false);
        }
    };

    // Calculate progression markers along a 50-tick horizon
    const horizonTicks = Math.max(50, Math.ceil((currentTick + 10) / 10) * 10);
    const tickPercent = Math.min(100, Math.max(0, (currentTick / horizonTicks) * 100));

    return (
        <div className="simulation-timeline-card">
            <div className="timeline-header">
                <div className="timeline-title">
                    <span>⏱️</span>
                    <h4>Simulation Timeline & History Tracker</h4>
                </div>
                <span className="timeline-badge">Tick #{currentTick} / {horizonTicks}</span>
            </div>

            {/* PROGRESSION BAR */}
            <div className="timeline-bar-container">
                <div className="timeline-track">
                    <div
                        className="timeline-progress-fill"
                        style={{ width: `${tickPercent}%` }}
                    />
                    <div
                        className="timeline-needle"
                        style={{ left: `${tickPercent}%` }}
                    >
                        <span className="needle-dot" />
                        <span className="needle-tooltip">Tick {currentTick}</span>
                    </div>
                </div>

                <div className="timeline-ticks-labels">
                    <span>Tick 0</span>
                    <span>Tick {Math.round(horizonTicks * 0.25)}</span>
                    <span>Tick {Math.round(horizonTicks * 0.5)}</span>
                    <span>Tick {Math.round(horizonTicks * 0.75)}</span>
                    <span>Tick {horizonTicks}</span>
                </div>
            </div>

            {/* CHECKPOINTS BAR */}
            <div className="timeline-checkpoint-form-row">
                <form onSubmit={handleCreateCheckpoint} style={{ display: "flex", gap: 8, flex: 1 }}>
                    <input
                        type="text"
                        placeholder="Checkpoint Name (e.g. Pre-Fire Surge)..."
                        value={checkpointName}
                        onChange={(e) => setCheckpointName(e.target.value)}
                        className="checkpoint-input"
                    />
                    <button
                        type="submit"
                        className="btn-checkpoint-save"
                        disabled={saving || !checkpointName.trim()}
                    >
                        {saving ? "Saving..." : "💾 Save Checkpoint"}
                    </button>
                </form>

                {checkpoints.length > 0 && (
                    <div className="checkpoints-chips-row">
                        {checkpoints.map((cp, idx) => (
                            <span key={idx} className="checkpoint-chip" title={`Recorded at ${cp.time}`}>
                                📍 {cp.name} (Tick {cp.tick})
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default SimulationTimeline;
