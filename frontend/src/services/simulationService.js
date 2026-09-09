/**
 * AegisAI Simulation & Digital Twin Service
 * Handles control commands, city snapshots, agent telemetry, What-If analysis, and replay history.
 */

import api from "./api";

export const simulationService = {
    /**
     * Get Digital Twin engine state & runtime metadata
     * GET /api/v1/simulation/state
     */
    async getSimulationState() {
        const response = await api.get("/simulation/state");
        return response.data?.data || null;
    },

    /**
     * Get complete city snapshot at current tick (buildings, roads, citizens, weather)
     * GET /api/v1/simulation/snapshot
     */
    async getCitySnapshot() {
        const response = await api.get("/simulation/snapshot");
        return response.data?.data || null;
    },

    /**
     * Get recent simulation event log
     * GET /api/v1/simulation/events
     */
    async getSimulationEvents(limit = 50) {
        const response = await api.get("/simulation/events", { params: { limit } });
        return response.data?.data || [];
    },

    /**
     * Get all building states with damage tracking
     * GET /api/v1/simulation/buildings
     */
    async getBuildings(damagedOnly = false) {
        const response = await api.get("/simulation/buildings", {
            params: { damaged_only: damagedOnly }
        });
        return response.data?.data || [];
    },

    /**
     * Get paginated citizen agents state
     * GET /api/v1/simulation/citizens
     */
    async getCitizens(statusFilter = null, page = 1, pageSize = 50) {
        const params = { page, page_size: pageSize };
        if (statusFilter) params.status_filter = statusFilter;
        const response = await api.get("/simulation/citizens", { params });
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Execute simulation engine action: "start" | "stop" | "pause" | "resume" | "tick" | "reset"
     * POST /api/v1/simulation/action
     */
    async performAction(action) {
        const response = await api.post("/simulation/action", { action });
        return response.data?.data || null;
    },

    /**
     * Update simulation engine runtime configuration
     * PUT /api/v1/simulation/config
     */
    async updateConfig(configData) {
        const response = await api.put("/simulation/config", configData);
        return response.data?.data || null;
    },

    /**
     * Inject a simulated incident directly into the digital twin
     * POST /api/v1/simulation/spawn-incident
     */
    async spawnIncident(incidentData) {
        const response = await api.post("/simulation/spawn-incident", incidentData);
        return response.data?.data || null;
    },

    /**
     * Run comparative What-If scenario analysis
     * POST /api/v1/simulation/what-if/compare
     */
    async runWhatIf(scenarioPayload) {
        const response = await api.post("/simulation/what-if/compare", scenarioPayload);
        return response.data?.data || null;
    },

    /**
     * Get historical replay timeline
     * GET /api/v1/simulation/replay/history
     */
    async getReplayHistory(limit = 50) {
        const response = await api.get("/simulation/replay/history", { params: { limit } });
        return response.data?.data || [];
    },

    /**
     * Seek state snapshot at a specific tick
     * GET /api/v1/simulation/replay/tick/{tick}
     */
    async seekReplayTick(tick) {
        const response = await api.get(`/simulation/replay/tick/${tick}`);
        return response.data?.data || null;
    },

    /**
     * Create a named simulation state checkpoint
     * POST /api/v1/simulation/replay/checkpoint
     */
    async createCheckpoint(name) {
        const response = await api.post("/simulation/replay/checkpoint", { name });
        return response.data?.data || null;
    }
};

export default simulationService;
