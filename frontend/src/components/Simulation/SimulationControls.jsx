/**
 * AegisAI Simulation Controls & Digital Twin Engine HUD
 * Features:
 * - Engine playback state controls (Start, Pause, Resume, Stop, Reset, Step 1 Tick)
 * - Speed multiplier selection
 * - Simulation Clock & Elapsed Time
 * - Dynamic Weather & Environmental Telemetry
 * - Traffic Congestion & Road Network Status
 * - Citizen Population State Machine Distribution
 */

import React, { useState } from "react";

export function SimulationControls({
    simulationState,
    cityState,
    onAction,
    onOpenWhatIf,
    onOpenSpawnModal,
    loadingAction
}) {
    const isRunning = simulationState?.is_running ?? false;
    const currentTick = simulationState?.current_tick ?? cityState?.tick_count ?? 0;
    const weather = cityState?.weather || { condition: "CLEAR", temperature_celsius: 28, wind_speed_kmh: 12, visibility_km: 10 };
    const traffic = cityState?.traffic || { road_congestion_factor: 1.0, average_speed_kmh: 45, blocked_roads_count: 0 };
    
    // Calculate elapsed time from ticks (assuming 1 tick = 10 sec in model time)
    const formatElapsedTime = (ticks) => {
        const totalSeconds = ticks * 10;
        const hrs = Math.floor(totalSeconds / 3600).toString().padStart(2, "0");
        const mins = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, "0");
        const secs = (totalSeconds % 60).toString().padStart(2, "0");
        return `${hrs}:${mins}:${secs}`;
    };

    const getWeatherIcon = (cond) => {
        switch (cond) {
            case "STORM": return "⛈️";
            case "RAIN": return "🌧️";
            case "FOG": return "🌫️";
            default: return "☀️";
        }
    };

    return (
        <div className="simulation-controls-card">
            {/* CLOCK & STATUS HEADER */}
            <div className="sim-header">
                <div className="sim-title-group">
                    <span className="sim-badge-label">🌐 DIGITAL TWIN ENGINE</span>
                    <div className="sim-status-row">
                        <span className={`sim-state-dot ${isRunning ? "dot-running" : "dot-paused"}`} />
                        <strong className="sim-state-text">{isRunning ? "ACTIVE SIMULATION" : "SIMULATION PAUSED"}</strong>
                    </div>
                </div>

                <div className="sim-clock-hud">
                    <div className="clock-metric">
                        <span className="label">SIM TIME</span>
                        <strong className="time-val">{formatElapsedTime(currentTick)}</strong>
                    </div>
                    <div className="clock-metric">
                        <span className="label">TICK</span>
                        <strong className="tick-val">#{currentTick}</strong>
                    </div>
                </div>
            </div>

            {/* ACTION BUTTONS ROW */}
            <div className="sim-actions-grid">
                {!isRunning ? (
                    <button
                        className="sim-btn btn-start"
                        onClick={() => onAction("start")}
                        disabled={loadingAction}
                        title="Start continuous digital twin simulation"
                    >
                        ▶ START
                    </button>
                ) : (
                    <button
                        className="sim-btn btn-pause"
                        onClick={() => onAction("pause")}
                        disabled={loadingAction}
                        title="Pause simulation clock"
                    >
                        ⏸ PAUSE
                    </button>
                )}

                <button
                    className="sim-btn btn-step"
                    onClick={() => onAction("tick")}
                    disabled={loadingAction}
                    title="Advance simulation by exactly 1 tick"
                >
                    ⏭ STEP TICK
                </button>

                <button
                    className="sim-btn btn-reset"
                    onClick={() => onAction("reset")}
                    disabled={loadingAction}
                    title="Reset simulation to initial state"
                >
                    ↻ RESET
                </button>

                <button
                    className="sim-btn btn-spawn"
                    onClick={onOpenSpawnModal}
                    title="Inject a simulated disaster into virtual city"
                >
                    ⚡ INJECT EVENT
                </button>

                <button
                    className="sim-btn btn-whatif"
                    onClick={onOpenWhatIf}
                    title="Open What-If AI comparative scenario analyzer"
                >
                    🧠 WHAT-IF LAB
                </button>
            </div>

            {/* TELEMETRY METRICS GRID */}
            <div className="sim-telemetry-grid">
                {/* Environmental Weather Box */}
                <div className="telemetry-box">
                    <div className="box-title">
                        <span>{getWeatherIcon(weather.condition)} WEATHER & ENVIRONMENT</span>
                        <span className={`badge-cond ${weather.condition?.toLowerCase()}`}>{weather.condition}</span>
                    </div>
                    <div className="telemetry-stats-row">
                        <div>
                            <span className="sub">Temp</span>
                            <strong>{weather.temperature_celsius?.toFixed(1)}°C</strong>
                        </div>
                        <div>
                            <span className="sub">Wind</span>
                            <strong>{weather.wind_speed_kmh?.toFixed(0)} km/h</strong>
                        </div>
                        <div>
                            <span className="sub">Visibility</span>
                            <strong>{weather.visibility_km?.toFixed(1)} km</strong>
                        </div>
                    </div>
                </div>

                {/* Traffic & Road State Box */}
                <div className="telemetry-box">
                    <div className="box-title">
                        <span>🚦 ROAD NETWORK & TRAFFIC</span>
                        <span className="badge-cond congestion">{traffic.road_congestion_factor?.toFixed(1)}x Congestion</span>
                    </div>
                    <div className="telemetry-stats-row">
                        <div>
                            <span className="sub">Avg Speed</span>
                            <strong>{traffic.average_speed_kmh?.toFixed(0)} km/h</strong>
                        </div>
                        <div>
                            <span className="sub">Blocked Roads</span>
                            <strong className={traffic.blocked_roads_count > 0 ? "text-danger" : ""}>
                                {traffic.blocked_roads_count}
                            </strong>
                        </div>
                    </div>
                </div>
            </div>

            {/* CITIZEN AGENT POPULATION STATE BAR */}
            {cityState && (
                <div className="citizen-state-section">
                    <div className="section-label">
                        <span>👥 CITIZEN POPULATION DYNAMICS ({cityState.total_citizens || 150} AGENTS)</span>
                    </div>
                    <div className="citizen-pills-row">
                        <div className="pill safe" title="Citizens in safe zones">
                            <span>🟢 Safe</span>
                            <strong>{cityState.safe_citizens || 0}</strong>
                        </div>
                        <div className="pill endangered" title="Citizens within disaster proximity">
                            <span>🟡 Endangered</span>
                            <strong>{cityState.endangered_citizens || 0}</strong>
                        </div>
                        <div className="pill evacuating" title="Citizens moving towards shelters">
                            <span>🟠 Evacuating</span>
                            <strong>{cityState.evacuating_citizens || 0}</strong>
                        </div>
                        <div className="pill injured" title="Injured citizens requiring medical rescue">
                            <span>🔴 Injured</span>
                            <strong>{cityState.injured_citizens || 0}</strong>
                        </div>
                        <div className="pill rescued" title="Rescued by response units">
                            <span>⚪ Rescued</span>
                            <strong>{cityState.rescued_citizens || 0}</strong>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default SimulationControls;
