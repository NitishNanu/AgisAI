/**
 * AegisAI Scenario Service
 * Handles scenario configuration blueprints, validation, baseline risk previews,
 * cloning, and simulation execution.
 */

import api from "./api";

export const scenarioService = {
    /**
     * Get built-in standardized scenario presets
     * GET /api/v1/scenarios/presets
     */
    async getPresets() {
        const response = await api.get("/scenarios/presets");
        return response.data?.data || [];
    },

    /**
     * Validate scenario parameters without saving
     * POST /api/v1/scenarios/validate
     */
    async validateScenario(payload) {
        const response = await api.post("/scenarios/validate", payload);
        return response.data?.data || { is_valid: false, errors: [] };
    },

    /**
     * Compute baseline casualty ranges, hospital/shelter demand & risk preview
     * POST /api/v1/scenarios/preview
     */
    async previewScenario(payload) {
        const response = await api.post("/scenarios/preview", payload);
        return response.data?.data || null;
    },

    /**
     * Create and persist a new scenario blueprint
     * POST /api/v1/scenarios
     */
    async createScenario(payload) {
        const response = await api.post("/scenarios", payload);
        return response.data?.data || null;
    },

    /**
     * List saved scenarios with search and filters
     * GET /api/v1/scenarios
     */
    async listScenarios(params = {}) {
        const response = await api.get("/scenarios", { params });
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Get single scenario configuration by ID
     * GET /api/v1/scenarios/{id}
     */
    async getScenario(id) {
        const response = await api.get(`/scenarios/${id}`);
        return response.data?.data || null;
    },

    /**
     * Update scenario configuration
     * PATCH /api/v1/scenarios/{id}
     */
    async updateScenario(id, payload) {
        const response = await api.patch(`/scenarios/${id}`, payload);
        return response.data?.data || null;
    },

    /**
     * Soft-delete / archive scenario
     * DELETE /api/v1/scenarios/{id}
     */
    async archiveScenario(id) {
        const response = await api.delete(`/scenarios/${id}`);
        return response.data?.data || null;
    },

    /**
     * Clone an existing scenario with a new UUID for parameter branching
     * POST /api/v1/scenarios/{id}/clone
     */
    async cloneScenario(id, newName = null) {
        const response = await api.post(`/scenarios/${id}/clone`, { new_name: newName });
        return response.data?.data || null;
    },

    /**
     * Launch scenario in Digital Twin simulation engine
     * POST /api/v1/scenarios/{id}/launch
     */
    async launchScenario(id) {
        const response = await api.post(`/scenarios/${id}/launch`);
        return response.data?.data || null;
    },

    /**
     * Get historical execution runs for a scenario
     * GET /api/v1/scenarios/{id}/runs
     */
    async getScenarioRuns(id) {
        const response = await api.get(`/scenarios/${id}/runs`);
        return response.data?.data || [];
    },

    /**
     * Get initial state snapshot recorded at launch
     * GET /api/v1/scenarios/{id}/snapshot
     */
    async getScenarioSnapshot(id) {
        const response = await api.get(`/scenarios/${id}/snapshot`);
        return response.data?.data || {};
    }
};

export default scenarioService;
