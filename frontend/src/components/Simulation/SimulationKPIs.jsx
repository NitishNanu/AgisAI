/**
 * AegisAI Simulation KPIs & Mission Control Telemetry Ribbon
 */

import React from "react";

export function SimulationKPIs({
    disastersCount = 0,
    missionsCount = 0,
    availableTeamsCount = 0,
    totalTeamsCount = 0,
    hospitals = [],
    cityState = null
}) {
    // Calculate total hospital capacity free %
    const totalBeds = hospitals.reduce((acc, h) => acc + (h.total_beds || 100), 0);
    const availableBeds = hospitals.reduce((acc, h) => acc + (h.available_beds || h.total_beds || 50), 0);
    const bedFreePct = totalBeds > 0 ? Math.round((availableBeds / totalBeds) * 100) : 75;

    const endangeredCount = cityState?.endangered_citizens || 0;
    const injuredCount = cityState?.injured_citizens || 0;
    const citizensAtRisk = endangeredCount + injuredCount;

    // Operational Health Score (100 minus penalty for disasters and injured)
    const healthScore = Math.max(20, Math.min(100, 100 - (disastersCount * 8) - (injuredCount * 2)));

    return (
        <div className="simulation-kpis-ribbon">
            <div className="kpi-card">
                <span className="kpi-icon">🚨</span>
                <div className="kpi-content">
                    <span className="kpi-label">ACTIVE DISASTERS</span>
                    <strong className={`kpi-val ${disastersCount > 0 ? "text-danger" : ""}`}>{disastersCount}</strong>
                </div>
            </div>

            <div className="kpi-card">
                <span className="kpi-icon">📡</span>
                <div className="kpi-content">
                    <span className="kpi-label">DEPLOYED MISSIONS</span>
                    <strong className="kpi-val text-primary">{missionsCount}</strong>
                </div>
            </div>

            <div className="kpi-card">
                <span className="kpi-icon">🚑</span>
                <div className="kpi-content">
                    <span className="kpi-label">FLEET READINESS</span>
                    <strong className="kpi-val text-success">
                        {availableTeamsCount} / {totalTeamsCount} <span className="kpi-sub">Units</span>
                    </strong>
                </div>
            </div>

            <div className="kpi-card">
                <span className="kpi-icon">🏥</span>
                <div className="kpi-content">
                    <span className="kpi-label">ER BED AVAILABILITY</span>
                    <strong className="kpi-val">{bedFreePct}% <span className="kpi-sub">Free</span></strong>
                </div>
            </div>

            <div className="kpi-card">
                <span className="kpi-icon">👥</span>
                <div className="kpi-content">
                    <span className="kpi-label">POPULATION AT RISK</span>
                    <strong className={`kpi-val ${citizensAtRisk > 0 ? "text-warning" : ""}`}>
                        {citizensAtRisk} <span className="kpi-sub">Agents</span>
                    </strong>
                </div>
            </div>

            <div className="kpi-card">
                <span className="kpi-icon">🛡️</span>
                <div className="kpi-content">
                    <span className="kpi-label">OPERATIONAL HEALTH</span>
                    <strong className="kpi-val text-info">{healthScore}/100</strong>
                </div>
            </div>
        </div>
    );
}

export default SimulationKPIs;
