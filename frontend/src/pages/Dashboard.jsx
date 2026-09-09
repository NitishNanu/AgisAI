import React, {
    useCallback,
    useEffect,
    useState
} from "react";

import Navbar from "../components/Layout/Navbar";
import AuthModal from "../components/Auth/AuthModal";
import DisasterMap from "../components/Map/DisasterMap";
import MissionControl from "../components/MissionControl";
import SimulationControls from "../components/Simulation/SimulationControls";
import SimulationKPIs from "../components/Simulation/SimulationKPIs";
import SimulationTimeline from "../components/Simulation/SimulationTimeline";
import LiveEventsFeed from "../components/Simulation/LiveEventsFeed";
import WhatIfModal from "../components/Simulation/WhatIfModal";
import SpawnIncidentModal from "../components/Simulation/SpawnIncidentModal";
import ScenarioDesigner from "../components/Scenario/ScenarioDesigner";
import ScenarioListModal from "../components/Scenario/ScenarioListModal";
import PredictiveDashboard from "../components/Prediction/PredictiveDashboard";

import { useAuth } from "../context/AuthContext";
import wsManager from "../services/websocketManager";
import simulationService from "../services/simulationService";
import scenarioService from "../services/scenarioService";
import predictionService from "../services/predictionService";

import {
    getDisasters,
    getHospitals,
    getShelters,
    getRescueTeams,
    getRecommendedRescueTeams,
    getAssignments,
    createAssignment,
    getMissions,
    updateAssignmentStatus
} from "../services/disasterService";

function Dashboard() {
    const { token, isAuthenticated, user, hasRole } = useAuth();

    // =========================================================
    // MODAL STATES
    // =========================================================
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
    const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
    const [isSpawnModalOpen, setIsSpawnModalOpen] = useState(false);
    const [isLibraryOpen, setIsLibraryOpen] = useState(false);

    // =========================================================
    // CORE EMERGENCY DATA STATES
    // =========================================================
    const [disasters, setDisasters] = useState([]);
    const [hospitals, setHospitals] = useState([]);
    const [shelters, setShelters] = useState([]);
    const [rescueTeams, setRescueTeams] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [missions, setMissions] = useState([]);
    const [forecastData, setForecastData] = useState(null);

    // =========================================================
    // DIGITAL TWIN SIMULATION STATES
    // =========================================================
    const [simulationState, setSimulationState] = useState(null);
    const [cityState, setCityState] = useState(null);
    const [simulationEvents, setSimulationEvents] = useState([]);
    const [loadingSimAction, setLoadingSimAction] = useState(false);

    // =========================================================
    // NAVIGATION & SELECTION
    // =========================================================
    const [activeTab, setActiveTab] = useState("INCIDENTS"); // "INCIDENTS" | "SCENARIO" | "SIMULATION" | "MISSIONS"
    const [selectedDisaster, setSelectedDisaster] = useState(null);
    const [selectedMission, setSelectedMission] = useState(null);

    // =========================================================
    // SMART TEAM RANKING & ROUTE
    // =========================================================
    const [recommendedTeams, setRecommendedTeams] = useState([]);
    const [recommendedTeam, setRecommendedTeam] = useState(null);
    const [activeRoute, setActiveRoute] = useState(null);

    // =========================================================
    // UI STATES
    // =========================================================
    const [loading, setLoading] = useState(true);
    const [routeLoading, setRouteLoading] = useState(false);
    const [dispatchLoading, setDispatchLoading] = useState(false);
    const [error, setError] = useState(null);

    // =========================================================
    // LOAD DASHBOARD & SIMULATION DATA
    // =========================================================
    const fetchMissionsData = useCallback(async () => {
        try {
            const missionsRes = await getMissions();
            if (missionsRes && missionsRes.data) {
                setMissions(missionsRes.data);
            }
        } catch (err) {
            console.error("Failed to load active missions:", err);
        }
    }, []);

    const fetchSimulationData = useCallback(async () => {
        try {
            const [simState, snapshot, events] = await Promise.all([
                simulationService.getSimulationState(),
                simulationService.getCitySnapshot(),
                simulationService.getSimulationEvents(30)
            ]);
            setSimulationState(simState);
            setCityState(snapshot);
            setSimulationEvents(events);
        } catch (simErr) {
            console.warn("Simulation telemetry load note:", simErr);
        }
    }, []);

    const loadDashboard = useCallback(async () => {
        try {
            setError(null);

            const [
                disastersData,
                hospitalsData,
                sheltersData,
                teamsData
            ] = await Promise.all([
                getDisasters().catch((e) => {
                    console.warn("Disaster telemetry fetch note:", e?.message);
                    return [];
                }),
                getHospitals().catch((e) => {
                    console.warn("Hospital telemetry fetch note:", e?.message);
                    return [];
                }),
                getShelters().catch((e) => {
                    console.warn("Shelter telemetry fetch note:", e?.message);
                    return [];
                }),
                getRescueTeams().catch((e) => {
                    console.warn("Fleet telemetry fetch note:", e?.message);
                    return [];
                })
            ]);

            setDisasters(disastersData || []);
            setHospitals(hospitalsData || []);
            setShelters(sheltersData || []);
            setRescueTeams(teamsData || []);

            await Promise.all([
                fetchMissionsData().catch(() => {}),
                fetchSimulationData().catch(() => {})
            ]);

            if (token) {
                try {
                    const assignmentData = await getAssignments(token);
                    setAssignments(assignmentData || []);
                } catch (assignmentError) {
                    console.warn("Assignment loading note:", assignmentError);
                }
            }

            predictionService.getPredictiveDashboard().then((res) => {
                if (res && res.data) setForecastData(res.data);
            }).catch((e) => {
                console.warn("Forecast telemetry fetch note:", e?.message);
            });

            if (disastersData.length === 0 && hospitalsData.length === 0) {
                setError("Backend API is reconnecting or server is starting up. Check terminal for uvicorn status.");
            }
        } catch (err) {
            console.error("Dashboard data load error:", err);
            setError("Unable to connect to backend server at http://127.0.0.1:8000.");
        } finally {
            setLoading(false);
        }
    }, [token, fetchMissionsData, fetchSimulationData]);

    // Initial Data Hydration
    useEffect(() => {
        let ignore = false;
        async function run() {
            if (!ignore) {
                await loadDashboard();
            }
        }
        run();
        return () => {
            ignore = true;
        };
    }, [loadDashboard]);

    // =========================================================
    // WEBSOCKET REAL-TIME STREAM SUBSCRIPTIONS
    // =========================================================
    useEffect(() => {
        wsManager.connect(token);

        // 1. Live Incident Created
        const unsubIncidentCreated = wsManager.subscribe("INCIDENT_CREATED", (newIncident) => {
            if (!newIncident) return;
            setDisasters((prev) => {
                const exists = prev.some((d) => d.id === newIncident.id);
                if (exists) return prev;
                return [newIncident, ...prev];
            });
        });

        // 2. Live Incident Updated
        const unsubIncidentUpdated = wsManager.subscribe("INCIDENT_UPDATED", (updatedIncident) => {
            if (!updatedIncident) return;
            setDisasters((prev) =>
                prev.map((d) => (d.id === updatedIncident.id ? { ...d, ...updatedIncident } : d))
            );
            if (selectedDisaster?.id === updatedIncident.id) {
                setSelectedDisaster((prev) => ({ ...prev, ...updatedIncident }));
            }
        });

        // 3. Live Mission Created / Dispatched
        const unsubMissionCreated = wsManager.subscribe("MISSION_CREATED", () => {
            fetchMissionsData();
            getRescueTeams().then(setRescueTeams);
        });

        // 4. Live Mission Status Updated
        const unsubMissionUpdated = wsManager.subscribe("MISSION_UPDATED", () => {
            fetchMissionsData();
            getRescueTeams().then(setRescueTeams);
        });

        // 5. Digital Twin Simulation Tick
        const unsubSimTick = wsManager.subscribe("SIMULATION_TICK", (tickData) => {
            if (!tickData) return;
            setSimulationState((prev) => ({
                ...(prev || {}),
                current_tick: tickData.tick,
                is_running: true,
                active_incidents: tickData.disasters_count
            }));

            setCityState((prev) => ({
                ...(prev || {}),
                tick_count: tickData.tick,
                safe_citizens: tickData.safe_citizens,
                endangered_citizens: tickData.endangered_citizens,
                evacuating_citizens: tickData.evacuating_citizens,
                injured_citizens: tickData.injured_citizens,
                rescued_citizens: tickData.rescued_citizens,
                weather: tickData.weather || prev?.weather,
                traffic: tickData.traffic || prev?.traffic
            }));

            if (tickData.recent_events && tickData.recent_events.length > 0) {
                setSimulationEvents((prev) => {
                    const combined = [...tickData.recent_events, ...prev];
                    const seen = new Set();
                    return combined.filter((ev) => {
                        const key = `${ev.tick}-${ev.event_type}-${ev.description}`;
                        if (seen.has(key)) return false;
                        seen.add(key);
                        return true;
                    }).slice(0, 50);
                });
            }
        });

        // 6. Scenario Launched Live Stream
        const unsubScenarioLaunched = wsManager.subscribe("SCENARIO_LAUNCHED", () => {
            loadDashboard();
        });

        // 7. Predictive Intelligence Live Updates
        const unsubPredUpdated = wsManager.subscribe("prediction.updated", (predData) => {
            if (predData) {
                setForecastData(predData);
            }
        });

        return () => {
            unsubIncidentCreated();
            unsubIncidentUpdated();
            unsubMissionCreated();
            unsubMissionUpdated();
            unsubSimTick();
            unsubScenarioLaunched();
        };
    }, [token, fetchMissionsData, selectedDisaster, loadDashboard]);

    // =========================================================
    // SIMULATION CONTROL ACTION DISPATCHER
    // =========================================================
    const handleSimulationAction = async (action) => {
        if (!isAuthenticated) {
            setIsAuthModalOpen(true);
            return;
        }

        setLoadingSimAction(true);
        try {
            const newState = await simulationService.performAction(action);
            if (newState) {
                setSimulationState(newState);
            }

            if (action === "tick" || action === "reset") {
                const snapshot = await simulationService.getCitySnapshot();
                setCityState(snapshot);
                const freshDisasters = await getDisasters();
                setDisasters(freshDisasters);
            }
        } catch (simErr) {
            console.error("Simulation action failed:", simErr);
            const msg = simErr?.response?.data?.message || simErr?.message || "Failed to execute simulation action.";
            alert(msg);
        } finally {
            setLoadingSimAction(false);
        }
    };

    // =========================================================
    // SELECT DISASTER
    // =========================================================
    async function selectDisaster(disaster) {
        setSelectedDisaster(disaster);
        setSelectedMission(null);
        setRecommendedTeams([]);
        setRecommendedTeam(null);
        setActiveRoute(null);

        try {
            setRouteLoading(true);
            const result = await getRecommendedRescueTeams(disaster.id);

            if (result.success && result.teams) {
                setRecommendedTeams(result.teams);

                if (result.recommended_team) {
                    const best = result.recommended_team;
                    setRecommendedTeam(best);
                    setActiveRoute({
                        distance_km: best.distance_km,
                        duration_minutes: best.eta_minutes,
                        geometry: best.route_geometry
                    });
                }
            }
        } catch (error) {
            console.error("Smart dispatch recommendation failed:", error);
            setRecommendedTeams([]);
            setRecommendedTeam(null);
            setActiveRoute(null);
        } finally {
            setRouteLoading(false);
        }
    }

    // =========================================================
    // SELECT MISSION (FOCUS ON MAP)
    // =========================================================
    function handleSelectMission(mission) {
        setSelectedMission(mission);
        if (mission && mission.route_geometry) {
            setActiveRoute({
                distance_km: mission.distance_km,
                duration_minutes: mission.eta_minutes,
                geometry: mission.route_geometry
            });
        }
    }

    // =========================================================
    // UPDATE MISSION STATUS
    // =========================================================
    async function handleUpdateMissionStatus(assignmentId, newStatus) {
        if (!isAuthenticated) {
            setIsAuthModalOpen(true);
            return;
        }

        try {
            await updateAssignmentStatus(assignmentId, newStatus, token);
            
            const updatedTeams = await getRescueTeams();
            setRescueTeams(updatedTeams);
            await fetchMissionsData();

            if (token) {
                const updatedAssignments = await getAssignments(token);
                setAssignments(updatedAssignments);
            }

            if (newStatus === "COMPLETED") {
                alert("🎉 Mission completed successfully! Response unit returned to AVAILABLE status.");
            }
        } catch (err) {
            console.error("Failed to update mission status:", err);
            const msg = err?.response?.data?.message || err?.response?.data?.detail || "Failed to update mission status.";
            alert(msg);
        }
    }

    // =========================================================
    // DISPATCH TEAM
    // =========================================================
    async function dispatchTeam() {
        if (!selectedDisaster || !recommendedTeam) return;

        if (!isAuthenticated) {
            setIsAuthModalOpen(true);
            return;
        }

        if (!hasRole(["ADMIN", "COMMANDER", "DISPATCHER"])) {
            alert(`⚠️ Dispatch Clearance Required:\nOnly COMMANDER, DISPATCHER, or ADMIN roles have tactical dispatch authority.\nYour current role is: ${user?.role || "CITIZEN"}.\n\nPlease switch to a Commander or Dispatcher account via the Identity modal.`);
            setIsAuthModalOpen(true);
            return;
        }

        try {
            setDispatchLoading(true);

            const assignment = await createAssignment(
                selectedDisaster.id,
                recommendedTeam.team_id,
                token
            );

            if (assignment) {
                setAssignments((prev) => [...prev, assignment]);
            }

            const updatedTeams = await getRescueTeams();
            setRescueTeams(updatedTeams);

            await fetchMissionsData();

            setRecommendedTeams((prev) =>
                prev.map((team) =>
                    team.team_id === recommendedTeam.team_id
                        ? { ...team, status: "DISPATCHED" }
                        : team
                )
            );

            setRecommendedTeam((prev) =>
                prev ? { ...prev, status: "DISPATCHED" } : prev
            );

            if (assignment) {
                setActiveRoute({
                    distance_km: assignment.distance_km || recommendedTeam.distance_km,
                    duration_minutes: assignment.estimated_arrival_minutes || recommendedTeam.eta_minutes,
                    geometry: assignment.route_geometry || recommendedTeam.route_geometry
                });
            }

            setActiveTab("MISSIONS");
        } catch (error) {
            console.error("Dispatch failed:", error);
            if (error?.response?.status === 403) {
                alert(`⚠️ Dispatch Authority Denied (403 Forbidden):\nOnly COMMANDER, DISPATCHER, or ADMIN roles can dispatch rescue units.\nYour current clearance is: ${user?.role || "CITIZEN"}.\n\nPlease switch to Commander or Dispatcher.`);
                setIsAuthModalOpen(true);
            } else {
                const message = error?.response?.data?.message || error?.response?.data?.detail || "Failed to dispatch rescue team.";
                alert(message);
            }
        } finally {
            setDispatchLoading(false);
        }
    }

    // =========================================================
    // INITIAL LOADING SCREEN
    // =========================================================
    if (loading) {
        return (
            <div className="loading-screen">
                <div className="spinner" />
                <p>Initializing AegisAI Digital Twin & Telemetry Stream...</p>
            </div>
        );
    }

    const availableTeamsCount = rescueTeams.filter((t) => t.status === "AVAILABLE").length;

    // =========================================================
    // MAIN UI
    // =========================================================
    return (
        <div className="dashboard">
            {/* TOP NAVIGATION BAR WITH TELEMETRY & AUTH */}
            <Navbar onOpenAuthModal={() => setIsAuthModalOpen(true)} />

            {/* SIMULATION TELEMETRY KPI RIBBON */}
            <SimulationKPIs
                disastersCount={disasters.length}
                missionsCount={missions.length}
                availableTeamsCount={availableTeamsCount}
                totalTeamsCount={rescueTeams.length}
                hospitals={hospitals}
                cityState={cityState}
            />

            {/* AUTHENTICATION, SCENARIO & WHAT-IF MODALS */}
            <AuthModal
                isOpen={isAuthModalOpen}
                onClose={() => setIsAuthModalOpen(false)}
            />

            <WhatIfModal
                isOpen={isWhatIfOpen}
                onClose={() => setIsWhatIfOpen(false)}
            />

            <ScenarioListModal
                isOpen={isLibraryOpen}
                onClose={() => setIsLibraryOpen(false)}
                onLaunchScenario={async () => {
                    await loadDashboard();
                    setActiveTab("SIMULATION");
                }}
            />

            <SpawnIncidentModal
                isOpen={isSpawnModalOpen}
                onClose={() => setIsSpawnModalOpen(false)}
                onIncidentSpawned={async () => {
                    const freshDisasters = await getDisasters();
                    setDisasters(freshDisasters);
                    fetchSimulationData();
                }}
            />

            {/* MAIN DASHBOARD CONTENT */}
            <main className="dashboard-content">
                {/* INTERACTIVE DIGITAL TWIN MAP SECTION */}
                <section className="map-section">
                    {error && (
                        <div className="error">
                            <span>⚠️ {error}</span>
                            <button
                                className="action-btn focus-btn"
                                style={{ marginLeft: 12, padding: "4px 8px" }}
                                onClick={loadDashboard}
                            >
                                🔄 Retry
                            </button>
                        </div>
                    )}

                    <DisasterMap
                        disasters={disasters}
                        hospitals={hospitals}
                        shelters={shelters}
                        rescueTeams={rescueTeams}
                        assignments={assignments}
                        activeRoute={activeRoute}
                        buildings={cityState?.buildings || []}
                        roads={cityState?.roads || []}
                        citizens={cityState?.citizens || []}
                        forecastData={forecastData}
                        onSelectIncident={selectDisaster}
                    />
                </section>

                {/* SIDEBAR COMMAND CENTER */}
                <aside className="disaster-panel">
                    {/* DASHBOARD TABS */}
                    <div className="dashboard-tabs">
                        <button
                            className={`tab-btn ${activeTab === "INCIDENTS" ? "active" : ""}`}
                            onClick={() => setActiveTab("INCIDENTS")}
                        >
                            🚨 Incidents ({disasters.length})
                        </button>
                        <button
                            className={`tab-btn ${activeTab === "SCENARIO" ? "active" : ""}`}
                            onClick={() => setActiveTab("SCENARIO")}
                        >
                            🛠️ Scenario Studio
                        </button>
                        <button
                            className={`tab-btn ${activeTab === "SIMULATION" ? "active" : ""}`}
                            onClick={() => setActiveTab("SIMULATION")}
                        >
                            🌐 Digital Twin
                        </button>
                        <button
                            className={`tab-btn ${activeTab === "MISSIONS" ? "active" : ""}`}
                            onClick={() => setActiveTab("MISSIONS")}
                        >
                            📡 Missions ({missions.length})
                        </button>
                        <button
                            className={`tab-btn ${activeTab === "PREDICTIONS" ? "active" : ""}`}
                            onClick={() => setActiveTab("PREDICTIONS")}
                        >
                            🔮 Predictive AI
                        </button>
                    </div>

                    {/* TAB 1: INCIDENTS & SMART DISPATCH */}
                    {activeTab === "INCIDENTS" && (
                        <>
                            <h2>Active Disasters</h2>

                            {disasters.length === 0 ? (
                                <div className="no-missions" style={{ marginTop: 20 }}>
                                    <p>No active incidents reported.</p>
                                    <span className="sub-text">The response network is clear. Use Scenario Studio to design and launch a custom simulation.</span>
                                </div>
                            ) : (
                                disasters.map((disaster) => (
                                    <div
                                        key={disaster.id}
                                        className={`disaster-card ${selectedDisaster?.id === disaster.id ? "selected" : ""}`}
                                        onClick={() => selectDisaster(disaster)}
                                    >
                                        <div>
                                            <h3>🚨 {disaster.title}</h3>
                                            <p>{disaster.disaster_type}</p>
                                        </div>
                                        <span className={`severity-badge ${disaster.severity?.toLowerCase()}`}>
                                            {disaster.severity}
                                        </span>
                                    </div>
                                ))
                            )}

                            {/* SELECTED DISASTER PANEL */}
                            {selectedDisaster && (
                                <div className="rescue-details">
                                    <div className="section-title">
                                        <span>🚨</span>
                                        <h2>Selected Incident Details</h2>
                                    </div>

                                    <h3>{selectedDisaster.title}</h3>

                                    <div className="detail-row">
                                        <span>Type</span>
                                        <strong>{selectedDisaster.disaster_type}</strong>
                                    </div>

                                    <div className="detail-row">
                                        <span>Severity</span>
                                        <strong>{selectedDisaster.severity}</strong>
                                    </div>

                                    <div className="detail-row">
                                        <span>Status</span>
                                        <strong>{selectedDisaster.status}</strong>
                                    </div>

                                    {selectedDisaster.affected_radius_meters && (
                                        <div className="detail-row">
                                            <span>Affected Radius</span>
                                            <strong>{(selectedDisaster.affected_radius_meters / 1000).toFixed(1)} km</strong>
                                        </div>
                                    )}

                                    <hr />

                                    {routeLoading && (
                                        <div className="route-loading">
                                            <div className="spinner" />
                                            Evaluating candidate units & calculating OSRM road routes...
                                        </div>
                                    )}

                                    {/* TEAM RANKING */}
                                    {!routeLoading && recommendedTeams.length > 0 && (
                                        <div className="team-ranking">
                                            <h3>🚑 Smart Candidate Ranking</h3>
                                            {recommendedTeams.map((team) => (
                                                <div
                                                    key={team.team_id}
                                                    className={`team-ranking-card ${team.rank === 1 ? "best-team" : ""}`}
                                                >
                                                    <div className="team-rank">#{team.rank}</div>
                                                    <div className="team-info">
                                                        <strong>{team.team_name}</strong>
                                                        <span>{team.vehicle_type}</span>
                                                        <span>
                                                            🚗 {team.distance_km} km • ⏱ {team.eta_minutes} min
                                                        </span>
                                                        <span>Status: {team.status}</span>
                                                    </div>
                                                    <div className="team-score">{team.score}</div>
                                                </div>
                                            ))}
                                        </div>
                                    )}

                                    {/* RECOMMENDED TEAM */}
                                    {!routeLoading && recommendedTeam && (
                                        <div className="recommended-team">
                                            <div className="recommended-title">
                                                🏆 Recommended Response Unit
                                            </div>
                                            <h3>{recommendedTeam.team_name}</h3>
                                            <p>{recommendedTeam.vehicle_type} • {recommendedTeam.members} members</p>

                                            <div className="route-box">
                                                <div>
                                                    <strong>🚗 Road Distance</strong>
                                                    <span>{recommendedTeam.distance_km} km</span>
                                                </div>
                                                <div>
                                                    <strong>⏱ ETA</strong>
                                                    <span>{recommendedTeam.eta_minutes} min</span>
                                                </div>
                                            </div>

                                            <div className="response-score">
                                                Response Score: <strong>{recommendedTeam.score}/100</strong>
                                            </div>

                                            {recommendedTeam.status === "AVAILABLE" && (
                                                <button
                                                    className="dispatch-button"
                                                    onClick={dispatchTeam}
                                                    disabled={dispatchLoading}
                                                >
                                                    {dispatchLoading ? "Dispatching..." : "🚑 DISPATCH UNIT"}
                                                </button>
                                            )}

                                            {recommendedTeam.status === "DISPATCHED" && (
                                                <div className="dispatched-message">
                                                    🚑 Unit Dispatched & En Route
                                                </div>
                                            )}
                                        </div>
                                    )}

                                    {!routeLoading && !recommendedTeam && recommendedTeams.length === 0 && (
                                        <div className="no-team">
                                            No available rescue units found within operational radius.
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}

                    {/* TAB 2: SCENARIO DESIGNER STUDIO */}
                    {activeTab === "SCENARIO" && (
                        <ScenarioDesigner
                            onScenarioLaunched={async () => {
                                await loadDashboard();
                                setActiveTab("SIMULATION");
                            }}
                            onOpenLibrary={() => setIsLibraryOpen(true)}
                        />
                    )}

                    {/* TAB 3: DIGITAL TWIN SIMULATION COMMAND HUD */}
                    {activeTab === "SIMULATION" && (
                        <>
                            <SimulationControls
                                simulationState={simulationState}
                                cityState={cityState}
                                onAction={handleSimulationAction}
                                onOpenWhatIf={() => setIsWhatIfOpen(true)}
                                onOpenSpawnModal={() => setIsSpawnModalOpen(true)}
                                loadingAction={loadingSimAction}
                            />

                            <SimulationTimeline
                                currentTick={simulationState?.current_tick || 0}
                                isRunning={simulationState?.is_running || false}
                            />

                            <LiveEventsFeed events={simulationEvents} />
                        </>
                    )}

                    {/* TAB 4: ACTIVE MISSIONS HUD */}
                    {activeTab === "MISSIONS" && (
                        <MissionControl
                            missions={missions}
                            onUpdateStatus={handleUpdateMissionStatus}
                            onSelectMission={handleSelectMission}
                            selectedMissionId={selectedMission?.assignment_id}
                        />
                    )}

                    {/* TAB 5: PREDICTIVE AI FORECASTING INTELLIGENCE */}
                    {activeTab === "PREDICTIONS" && (
                        <PredictiveDashboard
                            onSelectIncident={selectDisaster}
                            simulationId={simulationState?.simulation_id}
                        />
                    )}
                </aside>
            </main>
        </div>
    );
}

export default Dashboard;