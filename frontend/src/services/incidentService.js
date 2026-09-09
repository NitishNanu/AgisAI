/**
 * AegisAI Incident & Disaster Service
 * Handles listing, reporting, updating, and smart recommendation queries.
 */

import api from "./api";

export const incidentService = {
    /**
     * Get paginated incidents list
     * GET /api/v1/incidents
     */
    async getIncidents(params = {}) {
        const response = await api.get("/incidents", { params });
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Get single incident by ID
     * GET /api/v1/incidents/{id}
     */
    async getIncident(id) {
        const response = await api.get(`/incidents/${id}`);
        return response.data?.data || null;
    },

    /**
     * Report a new incident
     * POST /api/v1/incidents
     */
    async createIncident(incidentData) {
        const response = await api.post("/incidents", incidentData);
        return response.data?.data || null;
    },

    /**
     * Update an incident (status, severity, coordinates)
     * PUT /api/v1/incidents/{id}
     */
    async updateIncident(id, updateData) {
        const response = await api.put(`/incidents/${id}`, updateData);
        return response.data?.data || null;
    },

    /**
     * Delete an incident (ADMIN / COMMANDER)
     * DELETE /api/v1/incidents/{id}
     */
    async deleteIncident(id) {
        const response = await api.delete(`/incidents/${id}`);
        return response.data;
    },

    /**
     * Get nearest available rescue team (PostGIS)
     * GET /api/v1/incidents/{id}/nearest-rescue-team
     */
    async getNearestRescueTeam(disasterId) {
        const response = await api.get(`/incidents/${disasterId}/nearest-rescue-team`);
        return response.data?.data || null;
    },

    /**
     * Get AI-ranked recommended rescue teams
     * GET /api/v1/incidents/{id}/recommended-teams
     */
    async getRecommendedRescueTeams(disasterId, limit = 5) {
        const response = await api.get(`/incidents/${disasterId}/recommended-teams`, {
            params: { limit }
        });
        const resData = response.data?.data || {};
        return {
            success: true,
            teams: resData.all_teams || [],
            recommended_team: resData.recommended || null,
            reason: resData.reason || ""
        };
    },

    /**
     * Get OSRM road route between disaster and rescue team
     * GET /api/v1/disasters/{id}/route-to-rescue-team/{team_id}
     */
    async getRouteToRescueTeam(disasterId, teamId) {
        const response = await api.get(`/disasters/${disasterId}/route-to-rescue-team/${teamId}`);
        return response.data?.data || null;
    },

    /**
     * Get nearby hospitals within radius
     * GET /api/v1/incidents/{id}/nearby-hospitals
     */
    async getNearbyHospitals(disasterId, radiusKm = 15.0) {
        const response = await api.get(`/incidents/${disasterId}/nearby-hospitals`, {
            params: { radius_km: radiusKm }
        });
        return response.data?.data || [];
    },

    /**
     * Get nearby shelters within radius
     * GET /api/v1/incidents/{id}/nearby-shelters
     */
    async getNearbyShelters(disasterId, radiusKm = 15.0) {
        const response = await api.get(`/incidents/${disasterId}/nearby-shelters`, {
            params: { radius_km: radiusKm }
        });
        return response.data?.data || [];
    }
};

export default incidentService;
