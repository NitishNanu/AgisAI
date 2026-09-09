/**
 * AegisAI Scenario Designer & Simulation Blueprint Studio
 * Visual interactive emergency operations scenario builder.
 */

import React, { useState, useEffect } from "react";
import scenarioService from "../../services/scenarioService";

export function ScenarioDesigner({ onScenarioLaunched, onOpenLibrary }) {
    const [presets, setPresets] = useState([]);
    const [activeSection, setActiveSection] = useState("DISASTER"); // DISASTER | ENVIRONMENT | POPULATION | RESOURCES | MEDICAL | INFRASTRUCTURE | SIMULATION
    
    // Core Form State
    const [name, setName] = useState("Urban Seismic Rupture Scenario");
    const [description, setDescription] = useState("High-density commercial core earthquake simulation with structural collapse.");
    
    // Disaster
    const [disasterType, setDisasterType] = useState("EARTHQUAKE");
    const [severity, setSeverity] = useState("HIGH");
    const [latitude, setLatitude] = useState(30.7399);
    const [longitude, setLongitude] = useState(76.7830);
    const [radiusKm, setRadiusKm] = useState(5.0);
    const [magnitude, setMagnitude] = useState(6.8);
    const [depthKm, setDepthKm] = useState(10.0);

    // Environment
    const [weatherPreset, setWeatherPreset] = useState("CLEAR");
    const [temperature, setTemperature] = useState(28.0);
    const [humidity, setHumidity] = useState(60.0);
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

    // Hospitals & Shelters
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

    // UI States
    const [preview, setPreview] = useState(null);
    const [validation, setValidation] = useState(null);
    const [loadingAction, setLoadingAction] = useState(false);
    const [statusMessage, setStatusMessage] = useState(null);

    // Load Presets on Mount
    useEffect(() => {
        scenarioService.getPresets().then(setPresets).catch(console.warn);
    }, []);

    // Build Current Payload
    const buildPayload = () => ({
        name,
        description,
        disaster: {
            type: disasterType,
            severity,
            latitude: Number(latitude),
            longitude: Number(longitude),
            radius_km: Number(radiusKm),
            magnitude: Number(magnitude),
            depth_km: Number(depthKm),
        },
        environment: {
            weather_preset: weatherPreset,
            temperature_celsius: Number(temperature),
            humidity_percent: Number(humidity),
            wind_speed_kmh: Number(windSpeed),
            visibility_km: Number(visibility),
        },
        population: {
            count: Number(populationCount),
            density: populationDensity,
            vulnerable_percentage: Number(vulnerablePct),
        },
        resources: {
            ambulances: Number(ambulances),
            fire_trucks: Number(fireTrucks),
            police_units: Number(policeUnits),
            rescue_teams: Number(rescueTeams),
            drones: Number(drones),
            helicopters: Number(helicopters),
        },
        hospitals: {
            total_beds: Number(totalBeds),
            icu_beds: Number(icuBeds),
            emergency_capacity_level: emergencyLevel,
        },
        shelters: {
            capacity: Number(shelterCapacity),
            initial_occupancy: Number(shelterOccupancy),
        },
        infrastructure: {
            road_damage_percentage: Number(roadDamagePct),
            road_closure_percentage: Number(roadClosurePct),
            bridge_damage_percentage: Number(bridgeDamagePct),
            power_outage_percentage: Number(powerOutagePct),
        },
        simulation: {
            duration_minutes: Number(durationMins),
            speed: Number(speedMultiplier),
            random_seed: Number(randomSeed),
        },
    });

    // Auto-update Preview debounced
    useEffect(() => {
        const timer = setTimeout(async () => {
            try {
                const payload = buildPayload();
                const res = await scenarioService.previewScenario(payload);
                setPreview(res);
                setValidation(null);
            } catch (err) {
                // Ignore transient validation errors during editing
            }
        }, 500);
        return () => clearTimeout(timer);
    }, [
        name, disasterType, severity, latitude, longitude, radiusKm,
        populationCount, populationDensity, vulnerablePct,
        ambulances, fireTrucks, policeUnits, rescueTeams,
        totalBeds, shelterCapacity, roadDamagePct
    ]);

    // Apply Preset
    const applyPreset = (preset) => {
        const c = preset.configuration;
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

        setStatusMessage(`Loaded preset: ${preset.name}`);
        setTimeout(() => setStatusMessage(null), 3000);
    };

    // Validate Action
    const handleValidate = async () => {
        setLoadingAction(true);
        try {
            const res = await scenarioService.validateScenario(buildPayload());
            setValidation(res);
            if (res.is_valid) {
                setStatusMessage("✅ Scenario configuration is 100% valid.");
            } else {
                setStatusMessage(`⚠️ Found ${res.errors.length} validation error(s).`);
            }
        } catch (err) {
            setStatusMessage("Validation failed.");
        } finally {
            setLoadingAction(false);
        }
    };

    // Save Scenario Blueprint
    const handleSaveScenario = async () => {
        setLoadingAction(true);
        try {
            const saved = await scenarioService.createScenario(buildPayload());
            setStatusMessage(`💾 Saved scenario: "${saved.name}" (ID: ${saved.id.slice(0, 8)}...)`);
        } catch (err) {
            console.error("Save scenario failed:", err);
            const msg = err?.response?.data?.message || err?.message || "Failed to save scenario.";
            alert(msg);
        } finally {
            setLoadingAction(false);
        }
    };

    // Launch Scenario Simulation
    const handleLaunch = async () => {
        setLoadingAction(true);
        try {
            // 1. Create Scenario
            const saved = await scenarioService.createScenario(buildPayload());
            // 2. Launch Scenario
            const run = await scenarioService.launchScenario(saved.id);
            alert(`🚀 Scenario launched successfully!\nSimulation Run ID: ${run.id}\nSwitching to Digital Twin live stream...`);
            if (onScenarioLaunched) {
                onScenarioLaunched(saved, run);
            }
        } catch (err) {
            console.error("Launch scenario failed:", err);
            const msg = err?.response?.data?.message || err?.message || "Failed to launch scenario simulation.";
            alert(msg);
        } finally {
            setLoadingAction(false);
        }
    };

    return (
        <div className="scenario-designer-container">
            {/* HEADER & PRESETS BAR */}
            <div className="scenario-header-bar">
                <div>
                    <h2>🛠️ Scenario Designer Studio</h2>
                    <p>Design, validate, and execute reproducible disaster simulation blueprints.</p>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <button className="btn-library-trigger" onClick={onOpenLibrary}>
                        📁 Scenario Library
                    </button>
                </div>
            </div>

            {/* PRESETS CHIPS BAR */}
            {presets.length > 0 && (
                <div className="presets-quick-bar">
                    <span className="presets-title">⚡ Quick Presets:</span>
                    <div className="presets-scroll-row">
                        {presets.map((p) => (
                            <button
                                key={p.preset_id}
                                className="preset-chip-btn"
                                onClick={() => applyPreset(p)}
                                title={p.description}
                            >
                                <span>{p.icon}</span>
                                <strong>{p.name}</strong>
                                <span className={`badge-mini ${p.severity?.toLowerCase()}`}>{p.severity}</span>
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {statusMessage && (
                <div className="scenario-status-banner">
                    {statusMessage}
                </div>
            )}

            {/* MAIN TWO-COLUMN WORKSPACE */}
            <div className="designer-workspace-grid">
                {/* LEFT COLUMN: PARAMETER CONFIGURATION TABS */}
                <div className="designer-config-card">
                    {/* SECTION TABS */}
                    <div className="designer-nav-tabs">
                        <button className={`nav-tab-btn ${activeSection === "DISASTER" ? "active" : ""}`} onClick={() => setActiveSection("DISASTER")}>🚨 Hazard</button>
                        <button className={`nav-tab-btn ${activeSection === "ENVIRONMENT" ? "active" : ""}`} onClick={() => setActiveSection("ENVIRONMENT")}>🌦️ Weather</button>
                        <button className={`nav-tab-btn ${activeSection === "POPULATION" ? "active" : ""}`} onClick={() => setActiveSection("POPULATION")}>👥 Population</button>
                        <button className={`nav-tab-btn ${activeSection === "RESOURCES" ? "active" : ""}`} onClick={() => setActiveSection("RESOURCES")}>🚑 Fleet</button>
                        <button className={`nav-tab-btn ${activeSection === "MEDICAL" ? "active" : ""}`} onClick={() => setActiveSection("MEDICAL")}>🏥 Medical</button>
                        <button className={`nav-tab-btn ${activeSection === "INFRASTRUCTURE" ? "active" : ""}`} onClick={() => setActiveSection("INFRASTRUCTURE")}>🛣️ Lifelines</button>
                        <button className={`nav-tab-btn ${activeSection === "SIMULATION" ? "active" : ""}`} onClick={() => setActiveSection("SIMULATION")}>⚙️ Clock</button>
                    </div>

                    <div className="designer-section-body">
                        {/* GENERAL INFO (Always Visible) */}
                        <div className="form-group" style={{ marginBottom: 12 }}>
                            <label>Scenario Title</label>
                            <input
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Scenario Name..."
                                required
                            />
                        </div>

                        {/* TAB 1: DISASTER HAZARD */}
                        {activeSection === "DISASTER" && (
                            <div className="section-form-fields">
                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Hazard Type</label>
                                        <select value={disasterType} onChange={(e) => setDisasterType(e.target.value)}>
                                            <option value="EARTHQUAKE">🌋 Seismic Earthquake</option>
                                            <option value="FLOOD">🌊 Monsoon Flash Flood</option>
                                            <option value="FIRE">🔥 Industrial Chemical Fire</option>
                                            <option value="BUILDING_COLLAPSE">🏚️ Structural Collapse</option>
                                            <option value="GAS_LEAK">☣️ Toxic Chemical Gas Leak</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Severity Level</label>
                                        <select value={severity} onChange={(e) => setSeverity(e.target.value)}>
                                            <option value="LOW">🟡 LOW</option>
                                            <option value="MODERATE">🟠 MODERATE</option>
                                            <option value="HIGH">🔴 HIGH</option>
                                            <option value="SEVERE">🟣 SEVERE</option>
                                            <option value="CRITICAL">💥 CRITICAL</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Epicenter Latitude</label>
                                        <input type="number" step="any" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>Epicenter Longitude</label>
                                        <input type="number" step="any" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Affected Impact Radius: {radiusKm} km</label>
                                    <input type="range" min="0.5" max="25.0" step="0.5" value={radiusKm} onChange={(e) => setRadiusKm(e.target.value)} />
                                </div>

                                {disasterType === "EARTHQUAKE" && (
                                    <div className="form-row-2">
                                        <div className="form-group">
                                            <label>Magnitude (Richter)</label>
                                            <input type="number" step="0.1" min="3.0" max="9.5" value={magnitude} onChange={(e) => setMagnitude(e.target.value)} />
                                        </div>
                                        <div className="form-group">
                                            <label>Focal Depth (km)</label>
                                            <input type="number" min="1" max="200" value={depthKm} onChange={(e) => setDepthKm(e.target.value)} />
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}

                        {/* TAB 2: ENVIRONMENT */}
                        {activeSection === "ENVIRONMENT" && (
                            <div className="section-form-fields">
                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Weather Preset</label>
                                        <select value={weatherPreset} onChange={(e) => setWeatherPreset(e.target.value)}>
                                            <option value="CLEAR">☀️ Clear Skies</option>
                                            <option value="RAIN">🌧️ Moderate Rain</option>
                                            <option value="HEAVY_RAIN">⛈️ Heavy Monsoon Downpour</option>
                                            <option value="STORM">🌪️ Severe Storm</option>
                                            <option value="HIGH_WIND">💨 Gale Winds</option>
                                            <option value="EXTREME_HEAT">🔥 Extreme Heatwave</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Temperature: {temperature}°C</label>
                                        <input type="range" min="-10" max="50" step="1" value={temperature} onChange={(e) => setTemperature(e.target.value)} />
                                    </div>
                                </div>

                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Wind Speed: {windSpeed} km/h</label>
                                        <input type="range" min="0" max="150" step="5" value={windSpeed} onChange={(e) => setWindSpeed(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>Visibility: {visibility} km</label>
                                        <input type="range" min="0.5" max="20" step="0.5" value={visibility} onChange={(e) => setVisibility(e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TAB 3: POPULATION */}
                        {activeSection === "POPULATION" && (
                            <div className="section-form-fields">
                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Exposed Population Count</label>
                                        <input type="number" step="1000" min="1000" max="1000000" value={populationCount} onChange={(e) => setPopulationCount(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>Urban Density Level</label>
                                        <select value={populationDensity} onChange={(e) => setPopulationDensity(e.target.value)}>
                                            <option value="LOW">Low (Suburban / Rural)</option>
                                            <option value="MEDIUM">Medium (Residential)</option>
                                            <option value="HIGH">High (Urban Core)</option>
                                            <option value="VERY_HIGH">Very High (Commercial Plaza)</option>
                                        </select>
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Vulnerable Demographic Share: {vulnerablePct}% (Elderly, Children, Special Care)</label>
                                    <input type="range" min="0" max="50" step="1" value={vulnerablePct} onChange={(e) => setVulnerablePct(e.target.value)} />
                                </div>
                            </div>
                        )}

                        {/* TAB 4: RESOURCES */}
                        {activeSection === "RESOURCES" && (
                            <div className="section-form-fields">
                                <div className="form-row-3">
                                    <div className="form-group">
                                        <label>🚑 Ambulances</label>
                                        <input type="number" min="0" max="100" value={ambulances} onChange={(e) => setAmbulances(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>🚒 Fire Engines</label>
                                        <input type="number" min="0" max="100" value={fireTrucks} onChange={(e) => setFireTrucks(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>🚓 Police Cruisers</label>
                                        <input type="number" min="0" max="100" value={policeUnits} onChange={(e) => setPoliceUnits(e.target.value)} />
                                    </div>
                                </div>
                                <div className="form-row-3">
                                    <div className="form-group">
                                        <label>🛟 Rescue Teams</label>
                                        <input type="number" min="0" max="100" value={rescueTeams} onChange={(e) => setRescueTeams(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>🚁 Aerial Drones</label>
                                        <input type="number" min="0" max="50" value={drones} onChange={(e) => setDrones(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>🛸 Helicopters</label>
                                        <input type="number" min="0" max="20" value={helicopters} onChange={(e) => setHelicopters(e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TAB 5: MEDICAL & SHELTERS */}
                        {activeSection === "MEDICAL" && (
                            <div className="section-form-fields">
                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Total Hospital Beds</label>
                                        <input type="number" min="100" max="10000" step="100" value={totalBeds} onChange={(e) => setTotalBeds(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>ICU Beds</label>
                                        <input type="number" min="10" max="1000" step="10" value={icuBeds} onChange={(e) => setIcuBeds(e.target.value)} />
                                    </div>
                                </div>

                                <div className="form-row-2">
                                    <div className="form-group">
                                        <label>Shelter Capacity (Citizens)</label>
                                        <input type="number" min="500" max="50000" step="500" value={shelterCapacity} onChange={(e) => setShelterCapacity(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>Emergency Readiness</label>
                                        <select value={emergencyLevel} onChange={(e) => setEmergencyLevel(e.target.value)}>
                                            <option value="NORMAL">Normal Operation</option>
                                            <option value="REDUCED">Reduced Staffing</option>
                                            <option value="OVERLOADED">Surge / Overloaded</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* TAB 6: INFRASTRUCTURE */}
                        {activeSection === "INFRASTRUCTURE" && (
                            <div className="section-form-fields">
                                <div className="form-group">
                                    <label>Road Network Damage: {roadDamagePct}%</label>
                                    <input type="range" min="0" max="100" step="5" value={roadDamagePct} onChange={(e) => setRoadDamagePct(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Road Blockades / Closures: {roadClosurePct}%</label>
                                    <input type="range" min="0" max="100" step="5" value={roadClosurePct} onChange={(e) => setRoadClosurePct(e.target.value)} />
                                </div>
                                <div className="form-group">
                                    <label>Power Grid Outage: {powerOutagePct}%</label>
                                    <input type="range" min="0" max="100" step="5" value={powerOutagePct} onChange={(e) => setPowerOutagePct(e.target.value)} />
                                </div>
                            </div>
                        )}

                        {/* TAB 7: SIMULATION CLOCK */}
                        {activeSection === "SIMULATION" && (
                            <div className="section-form-fields">
                                <div className="form-row-3">
                                    <div className="form-group">
                                        <label>Duration (Minutes)</label>
                                        <input type="number" min="10" max="720" step="10" value={durationMins} onChange={(e) => setDurationMins(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>Speed Multiplier</label>
                                        <input type="number" min="0.5" max="10" step="0.5" value={speedMultiplier} onChange={(e) => setSpeedMultiplier(e.target.value)} />
                                    </div>
                                    <div className="form-group">
                                        <label>Deterministic Seed</label>
                                        <input type="number" value={randomSeed} onChange={(e) => setRandomSeed(e.target.value)} />
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ACTION BUTTONS ROW */}
                    <div className="designer-actions-bar">
                        <button className="btn-validate" onClick={handleValidate} disabled={loadingAction}>
                            🔍 Validate Blueprint
                        </button>
                        <button className="btn-save-blueprint" onClick={handleSaveScenario} disabled={loadingAction}>
                            💾 Save Blueprint
                        </button>
                        <button className="btn-launch-sim" onClick={handleLaunch} disabled={loadingAction}>
                            🚀 Launch Digital Twin Simulation
                        </button>
                    </div>
                </div>

                {/* RIGHT COLUMN: BASELINE RISK & IMPACT PREVIEW HUD */}
                <div className="designer-preview-card">
                    <div className="preview-card-header">
                        <h3>📊 Baseline Impact & Risk Assessment</h3>
                        {preview && (
                            <span className={`risk-level-badge ${preview.risk_level?.toLowerCase()}`}>
                                {preview.risk_level} RISK ({preview.baseline_risk_score}/100)
                            </span>
                        )}
                    </div>

                    {preview ? (
                        <div className="preview-metrics-grid">
                            <div className="preview-metric-box">
                                <span className="label">AFFECTED POPULATION</span>
                                <strong className="value">{preview.affected_population?.toLocaleString()} <span className="sub">Residents</span></strong>
                            </div>

                            <div className="preview-metric-box">
                                <span className="label">ESTIMATED CASUALTIES</span>
                                <strong className="value text-danger">
                                    {preview.estimated_casualties_low} - {preview.estimated_casualties_high} <span className="sub">Injured</span>
                                </strong>
                            </div>

                            <div className="preview-metric-box">
                                <span className="label">PROJECTED EVACUEES</span>
                                <strong className="value text-warning">{preview.estimated_evacuees?.toLocaleString()} <span className="sub">Citizens</span></strong>
                            </div>

                            <div className="preview-metric-box">
                                <span className="label">HOSPITAL BED DEMAND</span>
                                <strong className="value text-info">{preview.hospital_demand_beds} <span className="sub">Beds</span></strong>
                            </div>

                            <div className="preview-metric-box">
                                <span className="label">SHELTER BED DEMAND</span>
                                <strong className="value">{preview.shelter_demand_beds} <span className="sub">Beds</span></strong>
                            </div>

                            <div className="preview-metric-box">
                                <span className="label">RESOURCE COVERAGE</span>
                                <strong className={`value ${preview.resource_coverage_ratio < 1.0 ? "text-danger" : "text-success"}`}>
                                    {preview.resource_coverage_ratio}x <span className="sub">Ratio</span>
                                </strong>
                            </div>

                            {/* RISK FACTORS & WARNINGS */}
                            <div className="preview-factors-box">
                                <strong>⚠️ Contributing Risk Drivers:</strong>
                                <ul>
                                    {preview.risk_factors?.map((f, i) => (
                                        <li key={i}>{f}</li>
                                    ))}
                                </ul>
                                {preview.warnings?.length > 0 && (
                                    <div className="preview-warning-alert">
                                        {preview.warnings.map((w, i) => (
                                            <p key={i}>🚨 {w}</p>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="preview-placeholder">
                            <div className="spinner" />
                            <p>Calculating multi-factor impact preview...</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default ScenarioDesigner;
