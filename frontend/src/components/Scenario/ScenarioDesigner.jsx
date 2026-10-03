/**
 * AegisAI Scenario Designer Studio
 * Full-screen modal overlay — a premium visual scenario builder.
 * Features: preset chips, tabbed wizard, live impact preview, validation, launch.
 */

import React, { useState, useEffect } from "react";
import scenarioService from "../../services/scenarioService";

/* ── Section tab definitions ─────────────────────────────── */
const SECTIONS = [
    { id: "DISASTER",       icon: "🚨", label: "Hazard" },
    { id: "ENVIRONMENT",    icon: "🌦️", label: "Weather" },
    { id: "POPULATION",     icon: "👥", label: "Population" },
    { id: "RESOURCES",      icon: "🚑", label: "Fleet" },
    { id: "MEDICAL",        icon: "🏥", label: "Medical" },
    { id: "INFRASTRUCTURE", icon: "🛣️", label: "Lifelines" },
    { id: "SIMULATION",     icon: "⚙️", label: "Clock" },
];

const SEVERITY_COLORS = {
    LOW: "#22c55e", MODERATE: "#f59e0b",
    HIGH: "#f97316", SEVERE: "#ef4444", CRITICAL: "#a855f7",
};

export function ScenarioDesigner({ onScenarioLaunched, onOpenLibrary }) {
    const [presets, setPresets] = useState([]);
    const [activeSection, setActiveSection] = useState("DISASTER");

    // Core
    const [name, setName] = useState("Urban Seismic Rupture Scenario");
    const [description, setDescription] = useState("High-density commercial core earthquake simulation with structural collapse.");

    // Disaster
    const [disasterType, setDisasterType] = useState("EARTHQUAKE");
    const [severity, setSeverity] = useState("HIGH");
    const [latitude, setLatitude] = useState(30.7399);
    const [longitude, setLongitude] = useState(76.783);
    const [radiusKm, setRadiusKm] = useState(5.0);
    const [magnitude, setMagnitude] = useState(6.8);
    const [depthKm, setDepthKm] = useState(10.0);

    // Environment
    const [weatherPreset, setWeatherPreset] = useState("CLEAR");
    const [temperature, setTemperature] = useState(28.0);
    const [windSpeed, setWindSpeed] = useState(12.0);
    const [visibility, setVisibility] = useState(10.0);

    // Population
    const [populationCount, setPopulationCount] = useState(60000);
    const [populationDensity, setPopulationDensity] = useState("HIGH");
    const [vulnerablePct, setVulnerablePct] = useState(15.0);

    // Resources
    const [ambulances, setAmbulances] = useState(12);
    const [fireTrucks, setFireTrucks] = useState(8);
    const [policeUnits, setPoliceUnits] = useState(15);
    const [rescueTeams, setRescueTeams] = useState(10);
    const [drones, setDrones] = useState(4);
    const [helicopters, setHelicopters] = useState(2);

    // Medical / Shelters
    const [totalBeds, setTotalBeds] = useState(1400);
    const [icuBeds, setIcuBeds] = useState(180);
    const [emergencyLevel, setEmergencyLevel] = useState("NORMAL");
    const [shelterCapacity, setShelterCapacity] = useState(8000);
    const [shelterOccupancy, setShelterOccupancy] = useState(400);

    // Infrastructure
    const [roadDamagePct, setRoadDamagePct] = useState(15.0);
    const [roadClosurePct, setRoadClosurePct] = useState(10.0);
    const [bridgeDamagePct, setBridgeDamagePct] = useState(5.0);
    const [powerOutagePct, setPowerOutagePct] = useState(20.0);

    // Simulation
    const [durationMins, setDurationMins] = useState(60);
    const [speedMultiplier, setSpeedMultiplier] = useState(2.0);
    const [randomSeed, setRandomSeed] = useState(101);

    // UI
    const [preview, setPreview] = useState(null);
    const [validation, setValidation] = useState(null);
    const [loadingAction, setLoadingAction] = useState(false);
    const [statusMessage, setStatusMessage] = useState(null);
    const [statusType, setStatusType] = useState("info"); // info | success | error

    useEffect(() => {
        scenarioService.getPresets().then(setPresets).catch(console.warn);
    }, []);

    const buildPayload = () => ({
        name, description,
        disaster: {
            type: disasterType, severity,
            latitude: Number(latitude), longitude: Number(longitude),
            radius_km: Number(radiusKm), magnitude: Number(magnitude), depth_km: Number(depthKm),
        },
        environment: {
            weather_preset: weatherPreset,
            temperature_celsius: Number(temperature),
            humidity_percent: 60,
            wind_speed_kmh: Number(windSpeed),
            visibility_km: Number(visibility),
        },
        population: {
            count: Number(populationCount),
            density: populationDensity,
            vulnerable_percentage: Number(vulnerablePct),
        },
        resources: {
            ambulances: Number(ambulances), fire_trucks: Number(fireTrucks),
            police_units: Number(policeUnits), rescue_teams: Number(rescueTeams),
            drones: Number(drones), helicopters: Number(helicopters),
        },
        hospitals: { total_beds: Number(totalBeds), icu_beds: Number(icuBeds), emergency_capacity_level: emergencyLevel },
        shelters: { capacity: Number(shelterCapacity), initial_occupancy: Number(shelterOccupancy) },
        infrastructure: {
            road_damage_percentage: Number(roadDamagePct),
            road_closure_percentage: Number(roadClosurePct),
            bridge_damage_percentage: Number(bridgeDamagePct),
            power_outage_percentage: Number(powerOutagePct),
        },
        simulation: { duration_minutes: Number(durationMins), speed: Number(speedMultiplier), random_seed: Number(randomSeed) },
    });

    // Auto-preview (debounced)
    useEffect(() => {
        const t = setTimeout(async () => {
            try {
                const res = await scenarioService.previewScenario(buildPayload());
                setPreview(res);
            } catch { /* ignore */ }
        }, 600);
        return () => clearTimeout(t);
    }, [name, disasterType, severity, latitude, longitude, radiusKm, populationCount, populationDensity, vulnerablePct, ambulances, fireTrucks, policeUnits, rescueTeams, totalBeds, shelterCapacity, roadDamagePct]);

    const showStatus = (msg, type = "info") => {
        setStatusMessage(msg);
        setStatusType(type);
        setTimeout(() => setStatusMessage(null), 4000);
    };

    const applyPreset = (p) => {
        const c = p.configuration;
        setName(c.name);
        setDescription(c.description || "");
        setDisasterType(c.disaster.type);
        setSeverity(c.disaster.severity);
        setLatitude(c.disaster.latitude);
        setLongitude(c.disaster.longitude);
        setRadiusKm(c.disaster.radius_km);
        if (c.disaster.magnitude) setMagnitude(c.disaster.magnitude);
        setWeatherPreset(c.environment.weather_preset);
        setTemperature(c.environment.temperature_celsius);
        setWindSpeed(c.environment.wind_speed_kmh);
        setPopulationCount(c.population.count);
        setPopulationDensity(c.population.density);
        setVulnerablePct(c.population.vulnerable_percentage);
        setAmbulances(c.resources.ambulances);
        setFireTrucks(c.resources.fire_trucks);
        setPoliceUnits(c.resources.police_units);
        setRescueTeams(c.resources.rescue_teams);
        setDrones(c.resources.drones);
        setHelicopters(c.resources.helicopters);
        setTotalBeds(c.hospitals.total_beds);
        setIcuBeds(c.hospitals.icu_beds);
        setShelterCapacity(c.shelters.capacity);
        setRoadDamagePct(c.infrastructure.road_damage_percentage);
        setRoadClosurePct(c.infrastructure.road_closure_percentage);
        setDurationMins(c.simulation.duration_minutes);
        setSpeedMultiplier(c.simulation.speed);
        setRandomSeed(c.simulation.random_seed);
        showStatus(`✨ Preset applied: ${p.name}`, "success");
    };

    const handleValidate = async () => {
        setLoadingAction(true);
        try {
            const res = await scenarioService.validateScenario(buildPayload());
            setValidation(res);
            if (res.is_valid) showStatus("✅ Blueprint is valid and ready to launch!", "success");
            else showStatus(`⚠️ ${res.errors.length} validation error(s) found.`, "error");
        } catch { showStatus("Validation failed.", "error"); }
        finally { setLoadingAction(false); }
    };

    const handleSave = async () => {
        setLoadingAction(true);
        try {
            const saved = await scenarioService.createScenario(buildPayload());
            showStatus(`💾 Saved: "${saved.name}" (${saved.id.slice(0, 8)}...)`, "success");
        } catch (err) {
            showStatus(err?.response?.data?.message || "Save failed.", "error");
        } finally { setLoadingAction(false); }
    };

    const handleLaunch = async () => {
        setLoadingAction(true);
        try {
            const saved = await scenarioService.createScenario(buildPayload());
            const run = await scenarioService.launchScenario(saved.id);
            showStatus(`🚀 Launched! Run ID: ${run.id?.slice(0, 8)}...`, "success");
            if (onScenarioLaunched) onScenarioLaunched(saved, run);
        } catch (err) {
            showStatus(err?.response?.data?.message || "Launch failed.", "error");
        } finally { setLoadingAction(false); }
    };

    const sectionIndex = SECTIONS.findIndex((s) => s.id === activeSection);
    const isFirst = sectionIndex === 0;
    const isLast = sectionIndex === SECTIONS.length - 1;
    const goNext = () => !isLast && setActiveSection(SECTIONS[sectionIndex + 1].id);
    const goPrev = () => !isFirst && setActiveSection(SECTIONS[sectionIndex - 1].id);

    return (
        <div className="sd-overlay">
            {/* ── HEADER ── */}
            <div className="sd-header">
                <div className="sd-header-left">
                    <span className="sd-header-icon">🛠️</span>
                    <div>
                        <h2 className="sd-title">Scenario Designer Studio</h2>
                        <p className="sd-subtitle">Build, validate & launch reproducible disaster blueprints</p>
                    </div>
                </div>
                <button className="sd-library-btn" onClick={onOpenLibrary}>
                    📁 Scenario Library
                </button>
            </div>

            {/* ── PRESET CHIPS ── */}
            {presets.length > 0 && (
                <div className="sd-presets-bar">
                    <span className="sd-presets-label">⚡ Quick Presets</span>
                    <div className="sd-presets-scroll">
                        {presets.map((p) => (
                            <button
                                key={p.preset_id}
                                className="sd-preset-chip"
                                onClick={() => applyPreset(p)}
                                title={p.description}
                                style={{ "--chip-color": SEVERITY_COLORS[p.severity] || "#6b7280" }}
                            >
                                <span>{p.icon}</span>
                                <span className="sd-preset-name">{p.name}</span>
                                <span
                                    className="sd-preset-badge"
                                    style={{ color: SEVERITY_COLORS[p.severity] || "#6b7280" }}
                                >
                                    {p.severity}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* ── STATUS BANNER ── */}
            {statusMessage && (
                <div className={`sd-status-banner sd-status-${statusType}`}>
                    {statusMessage}
                </div>
            )}

            {/* ── SCENARIO TITLE ── */}
            <div className="sd-title-row">
                <div className="sd-field-wrap full">
                    <label className="sd-label">Scenario Name</label>
                    <input
                        className="sd-input"
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Enter scenario name..."
                    />
                </div>
            </div>

            {/* ── BODY: WIZARD + PREVIEW ── */}
            <div className="sd-body">
                {/* LEFT: WIZARD */}
                <div className="sd-wizard">
                    {/* Section Tabs */}
                    <div className="sd-section-tabs">
                        {SECTIONS.map((s, i) => (
                            <button
                                key={s.id}
                                className={`sd-section-tab ${activeSection === s.id ? "active" : ""} ${i < sectionIndex ? "done" : ""}`}
                                onClick={() => setActiveSection(s.id)}
                            >
                                <span className="sd-tab-icon">{s.icon}</span>
                                <span className="sd-tab-label">{s.label}</span>
                                {i < sectionIndex && <span className="sd-tab-check">✓</span>}
                            </button>
                        ))}
                    </div>

                    {/* Form Content */}
                    <div className="sd-form-body">

                        {/* DISASTER HAZARD */}
                        {activeSection === "DISASTER" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading">
                                    <span>🚨</span> Disaster Hazard Configuration
                                </div>
                                <div className="sd-row-2">
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">Hazard Type</label>
                                        <select className="sd-select" value={disasterType} onChange={(e) => setDisasterType(e.target.value)}>
                                            <option value="EARTHQUAKE">🌋 Seismic Earthquake</option>
                                            <option value="FLOOD">🌊 Flash Flood</option>
                                            <option value="FIRE">🔥 Industrial Fire</option>
                                            <option value="BUILDING_COLLAPSE">🏚️ Structural Collapse</option>
                                            <option value="GAS_LEAK">☣️ Toxic Gas Leak</option>
                                        </select>
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">Severity Level</label>
                                        <select className="sd-select" value={severity} onChange={(e) => setSeverity(e.target.value)}
                                            style={{ borderColor: SEVERITY_COLORS[severity] + "80" }}>
                                            <option value="LOW">🟢 LOW</option>
                                            <option value="MODERATE">🟡 MODERATE</option>
                                            <option value="HIGH">🟠 HIGH</option>
                                            <option value="SEVERE">🔴 SEVERE</option>
                                            <option value="CRITICAL">💥 CRITICAL</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="sd-row-2">
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">📍 Epicenter Latitude</label>
                                        <input className="sd-input" type="number" step="any" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">📍 Epicenter Longitude</label>
                                        <input className="sd-input" type="number" step="any" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
                                    </div>
                                </div>

                                <div className="sd-field-wrap full">
                                    <label className="sd-label">💥 Impact Radius: <strong>{radiusKm} km</strong></label>
                                    <input className="sd-range" type="range" min="0.5" max="25" step="0.5" value={radiusKm} onChange={(e) => setRadiusKm(e.target.value)} />
                                    <div className="sd-range-ends"><span>0.5 km</span><span>25 km</span></div>
                                </div>

                                {disasterType === "EARTHQUAKE" && (
                                    <div className="sd-row-2">
                                        <div className="sd-field-wrap">
                                            <label className="sd-label">📊 Magnitude (Richter)</label>
                                            <input className="sd-input" type="number" step="0.1" min="3" max="9.5" value={magnitude} onChange={(e) => setMagnitude(e.target.value)} />
                                        </div>
                                        <div className="sd-field-wrap">
                                            <label className="sd-label">⬇️ Focal Depth (km)</label>
                                            <input className="sd-input" type="number" min="1" max="200" value={depthKm} onChange={(e) => setDepthKm(e.target.value)} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* ENVIRONMENT */}
                        {activeSection === "ENVIRONMENT" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading"><span>🌦️</span> Environmental Conditions</div>
                                <div className="sd-field-wrap full">
                                    <label className="sd-label">Weather Preset</label>
                                    <div className="sd-weather-grid">
                                        {[
                                            { val: "CLEAR", icon: "☀️", label: "Clear" },
                                            { val: "RAIN", icon: "🌧️", label: "Rain" },
                                            { val: "HEAVY_RAIN", icon: "⛈️", label: "Heavy Rain" },
                                            { val: "STORM", icon: "🌪️", label: "Storm" },
                                            { val: "HIGH_WIND", icon: "💨", label: "Gale Wind" },
                                            { val: "EXTREME_HEAT", icon: "🔥", label: "Heatwave" },
                                        ].map((w) => (
                                            <button
                                                key={w.val}
                                                className={`sd-weather-btn ${weatherPreset === w.val ? "active" : ""}`}
                                                onClick={() => setWeatherPreset(w.val)}
                                            >
                                                <span style={{ fontSize: 22 }}>{w.icon}</span>
                                                <span>{w.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                <div className="sd-row-3">
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">🌡️ Temp: <strong>{temperature}°C</strong></label>
                                        <input className="sd-range" type="range" min="-10" max="50" step="1" value={temperature} onChange={(e) => setTemperature(e.target.value)} />
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">💨 Wind: <strong>{windSpeed} km/h</strong></label>
                                        <input className="sd-range" type="range" min="0" max="150" step="5" value={windSpeed} onChange={(e) => setWindSpeed(e.target.value)} />
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">👁️ Visibility: <strong>{visibility} km</strong></label>
                                        <input className="sd-range" type="range" min="0.5" max="20" step="0.5" value={visibility} onChange={(e) => setVisibility(e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* POPULATION */}
                        {activeSection === "POPULATION" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading"><span>👥</span> Exposed Population</div>
                                <div className="sd-row-2">
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">Total Exposed Population</label>
                                        <input className="sd-input" type="number" step="1000" min="1000" max="1000000" value={populationCount} onChange={(e) => setPopulationCount(e.target.value)} />
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">Urban Density Level</label>
                                        <select className="sd-select" value={populationDensity} onChange={(e) => setPopulationDensity(e.target.value)}>
                                            <option value="LOW">🏘️ Low — Suburban / Rural</option>
                                            <option value="MEDIUM">🏙️ Medium — Residential</option>
                                            <option value="HIGH">🌆 High — Urban Core</option>
                                            <option value="VERY_HIGH">🏢 Very High — Commercial Hub</option>
                                        </select>
                                    </div>
                                </div>
                                <div className="sd-field-wrap full">
                                    <label className="sd-label">🧓 Vulnerable Demographics: <strong>{vulnerablePct}%</strong> <span style={{ color: "#64748b", fontWeight: 400 }}>(elderly, children, care-dependent)</span></label>
                                    <input className="sd-range" type="range" min="0" max="50" step="1" value={vulnerablePct} onChange={(e) => setVulnerablePct(e.target.value)} />
                                    <div className="sd-range-ends"><span>0%</span><span>50%</span></div>
                                </div>
                            </div>
                        )}

                        {/* FLEET / RESOURCES */}
                        {activeSection === "RESOURCES" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading"><span>🚑</span> Emergency Response Fleet</div>
                                <div className="sd-resource-grid">
                                    {[
                                        { icon: "🚑", label: "Ambulances", val: ambulances, set: setAmbulances, max: 100 },
                                        { icon: "🚒", label: "Fire Engines", val: fireTrucks, set: setFireTrucks, max: 100 },
                                        { icon: "🚓", label: "Police Units", val: policeUnits, set: setPoliceUnits, max: 100 },
                                        { icon: "🛟", label: "Rescue Teams", val: rescueTeams, set: setRescueTeams, max: 100 },
                                        { icon: "🚁", label: "Drones", val: drones, set: setDrones, max: 50 },
                                        { icon: "🛸", label: "Helicopters", val: helicopters, set: setHelicopters, max: 20 },
                                    ].map(({ icon, label, val, set, max }) => (
                                        <div key={label} className="sd-resource-card">
                                            <div className="sd-resource-icon">{icon}</div>
                                            <div className="sd-resource-label">{label}</div>
                                            <div className="sd-resource-controls">
                                                <button className="sd-stepper-btn" onClick={() => set(Math.max(0, val - 1))}>−</button>
                                                <span className="sd-resource-val">{val}</span>
                                                <button className="sd-stepper-btn" onClick={() => set(Math.min(max, val + 1))}>+</button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* MEDICAL */}
                        {activeSection === "MEDICAL" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading"><span>🏥</span> Medical & Shelter Capacity</div>
                                <div className="sd-row-3">
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">🛏️ Hospital Beds</label>
                                        <input className="sd-input" type="number" min="100" max="10000" step="100" value={totalBeds} onChange={(e) => setTotalBeds(e.target.value)} />
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">💉 ICU Beds</label>
                                        <input className="sd-input" type="number" min="10" max="1000" step="10" value={icuBeds} onChange={(e) => setIcuBeds(e.target.value)} />
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">🏠 Shelter Capacity</label>
                                        <input className="sd-input" type="number" min="500" max="50000" step="500" value={shelterCapacity} onChange={(e) => setShelterCapacity(e.target.value)} />
                                    </div>
                                </div>
                                <div className="sd-field-wrap full">
                                    <label className="sd-label">Emergency Readiness Level</label>
                                    <div className="sd-readiness-grid">
                                        {[
                                            { val: "NORMAL", icon: "🟢", label: "Normal Operations", desc: "Full staff & supplies" },
                                            { val: "REDUCED", icon: "🟡", label: "Reduced Staffing", desc: "Limited capacity" },
                                            { val: "OVERLOADED", icon: "🔴", label: "Surge / Overloaded", desc: "Critical capacity" },
                                        ].map((r) => (
                                            <button
                                                key={r.val}
                                                className={`sd-readiness-btn ${emergencyLevel === r.val ? "active" : ""}`}
                                                onClick={() => setEmergencyLevel(r.val)}
                                            >
                                                <span className="sd-readiness-icon">{r.icon}</span>
                                                <span className="sd-readiness-label">{r.label}</span>
                                                <span className="sd-readiness-desc">{r.desc}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* INFRASTRUCTURE */}
                        {activeSection === "INFRASTRUCTURE" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading"><span>🛣️</span> Lifeline Infrastructure Damage</div>
                                {[
                                    { label: "🛣️ Road Network Damage", val: roadDamagePct, set: setRoadDamagePct },
                                    { label: "🚧 Road Blockades / Closures", val: roadClosurePct, set: setRoadClosurePct },
                                    { label: "🌉 Bridge Damage", val: bridgeDamagePct, set: setBridgeDamagePct },
                                    { label: "⚡ Power Grid Outage", val: powerOutagePct, set: setPowerOutagePct },
                                ].map(({ label, val, set }) => (
                                    <div key={label} className="sd-field-wrap full sd-infra-row">
                                        <div className="sd-infra-label-row">
                                            <label className="sd-label">{label}</label>
                                            <span className="sd-infra-pct"
                                                style={{ color: val > 50 ? "#ef4444" : val > 25 ? "#f59e0b" : "#22c55e" }}>
                                                {val}%
                                            </span>
                                        </div>
                                        <input className="sd-range" type="range" min="0" max="100" step="5" value={val} onChange={(e) => set(e.target.value)} />
                                        <div className="sd-infra-bar-preview">
                                            <div className="sd-infra-bar-fill"
                                                style={{
                                                    width: `${val}%`,
                                                    background: val > 50 ? "#ef4444" : val > 25 ? "#f59e0b" : "#22c55e"
                                                }} />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* SIMULATION CLOCK */}
                        {activeSection === "SIMULATION" && (
                            <div className="sd-form-section">
                                <div className="sd-section-heading"><span>⚙️</span> Simulation Clock & Reproducibility</div>
                                <div className="sd-row-3">
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">⏱️ Duration (minutes)</label>
                                        <input className="sd-input" type="number" min="10" max="720" step="10" value={durationMins} onChange={(e) => setDurationMins(e.target.value)} />
                                        <span className="sd-field-hint">{Math.round(durationMins / 60 * 10) / 10} hrs</span>
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">⚡ Speed Multiplier</label>
                                        <input className="sd-input" type="number" min="0.5" max="10" step="0.5" value={speedMultiplier} onChange={(e) => setSpeedMultiplier(e.target.value)} />
                                        <span className="sd-field-hint">{speedMultiplier}x real-time</span>
                                    </div>
                                    <div className="sd-field-wrap">
                                        <label className="sd-label">🎲 Deterministic Seed</label>
                                        <input className="sd-input" type="number" value={randomSeed} onChange={(e) => setRandomSeed(e.target.value)} />
                                        <span className="sd-field-hint">For reproducibility</span>
                                    </div>
                                </div>
                                {/* Validation Results */}
                                {validation && (
                                    <div className={`sd-validation-box ${validation.is_valid ? "valid" : "invalid"}`}>
                                        <div className="sd-validation-title">
                                            {validation.is_valid ? "✅ Blueprint Validated" : "⚠️ Validation Issues"}
                                        </div>
                                        {validation.errors?.length > 0 && (
                                            <ul className="sd-validation-list">
                                                {validation.errors.map((e, i) => <li key={i}>❌ {e}</li>)}
                                            </ul>
                                        )}
                                        {validation.warnings?.length > 0 && (
                                            <ul className="sd-validation-list">
                                                {validation.warnings.map((w, i) => <li key={i} style={{ color: "#f59e0b" }}>⚠️ {w}</li>)}
                                            </ul>
                                        )}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* PREV / NEXT NAVIGATION */}
                        <div className="sd-wizard-nav">
                            <button className="sd-nav-btn" onClick={goPrev} disabled={isFirst}>← Previous</button>
                            <div className="sd-step-dots">
                                {SECTIONS.map((s, i) => (
                                    <button
                                        key={s.id}
                                        className={`sd-step-dot ${i === sectionIndex ? "active" : i < sectionIndex ? "done" : ""}`}
                                        onClick={() => setActiveSection(s.id)}
                                        title={s.label}
                                    />
                                ))}
                            </div>
                            <button className="sd-nav-btn" onClick={goNext} disabled={isLast}>Next →</button>
                        </div>
                    </div>
                </div>

                {/* RIGHT: IMPACT PREVIEW ── */}
                <div className="sd-preview-panel">
                    <div className="sd-preview-header">
                        <h3>📊 Impact Preview</h3>
                        {preview && (
                            <span className="sd-risk-badge"
                                style={{
                                    background: (SEVERITY_COLORS[preview.risk_level] || "#6b7280") + "22",
                                    color: SEVERITY_COLORS[preview.risk_level] || "#6b7280",
                                    border: `1px solid ${(SEVERITY_COLORS[preview.risk_level] || "#6b7280")}44`,
                                }}>
                                {preview.risk_level} · {preview.baseline_risk_score}/100
                            </span>
                        )}
                    </div>

                    {preview ? (
                        <>
                            <div className="sd-preview-grid">
                                {[
                                    { label: "Affected Population", val: preview.affected_population?.toLocaleString(), unit: "residents", color: "#f1f5f9" },
                                    { label: "Estimated Casualties", val: `${preview.estimated_casualties_low}–${preview.estimated_casualties_high}`, unit: "injured", color: "#ef4444" },
                                    { label: "Projected Evacuees", val: preview.estimated_evacuees?.toLocaleString(), unit: "citizens", color: "#f59e0b" },
                                    { label: "Hospital Bed Demand", val: preview.hospital_demand_beds, unit: "beds", color: "#38bdf8" },
                                    { label: "Shelter Bed Demand", val: preview.shelter_demand_beds, unit: "beds", color: "#a855f7" },
                                    { label: "Resource Coverage", val: `${preview.resource_coverage_ratio}x`, unit: "ratio", color: preview.resource_coverage_ratio < 1 ? "#ef4444" : "#22c55e" },
                                ].map(({ label, val, unit, color }) => (
                                    <div key={label} className="sd-preview-metric">
                                        <div className="sd-preview-metric-val" style={{ color }}>{val}</div>
                                        <div className="sd-preview-metric-unit">{unit}</div>
                                        <div className="sd-preview-metric-label">{label}</div>
                                    </div>
                                ))}
                            </div>

                            {/* RISK SCORE BAR */}
                            <div className="sd-risk-bar-wrap">
                                <div className="sd-risk-bar-label">
                                    <span>Baseline Risk Score</span>
                                    <strong>{preview.baseline_risk_score}/100</strong>
                                </div>
                                <div className="sd-risk-bar-track">
                                    <div className="sd-risk-bar-fill"
                                        style={{
                                            width: `${preview.baseline_risk_score}%`,
                                            background: preview.baseline_risk_score > 70
                                                ? "linear-gradient(90deg, #f97316, #ef4444)"
                                                : preview.baseline_risk_score > 40
                                                    ? "linear-gradient(90deg, #f59e0b, #f97316)"
                                                    : "linear-gradient(90deg, #22c55e, #f59e0b)"
                                        }}
                                    />
                                </div>
                            </div>

                            {/* RISK FACTORS */}
                            {preview.risk_factors?.length > 0 && (
                                <div className="sd-risk-factors">
                                    <div className="sd-risk-factors-title">⚠️ Risk Drivers</div>
                                    {preview.risk_factors.map((f, i) => (
                                        <div key={i} className="sd-risk-factor-row">
                                            <span className="sd-risk-factor-dot" />
                                            {f}
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* WARNINGS */}
                            {preview.warnings?.length > 0 && (
                                <div className="sd-warnings-box">
                                    {preview.warnings.map((w, i) => (
                                        <div key={i} className="sd-warning-row">🚨 {w}</div>
                                    ))}
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="sd-preview-placeholder">
                            <div className="sd-preview-spinner" />
                            <p>Computing impact preview…</p>
                        </div>
                    )}
                </div>
            </div>

            {/* ── ACTION BAR ── */}
            <div className="sd-action-bar">
                <button className="sd-btn sd-btn-validate" onClick={handleValidate} disabled={loadingAction}>
                    {loadingAction ? <span className="sd-btn-spinner" /> : "🔍"} Validate Blueprint
                </button>
                <button className="sd-btn sd-btn-save" onClick={handleSave} disabled={loadingAction}>
                    {loadingAction ? <span className="sd-btn-spinner" /> : "💾"} Save Blueprint
                </button>
                <button className="sd-btn sd-btn-launch" onClick={handleLaunch} disabled={loadingAction}>
                    {loadingAction ? <span className="sd-btn-spinner" /> : "🚀"} Launch Digital Twin Simulation
                </button>
            </div>
        </div>
    );
}

export default ScenarioDesigner;
