/**
 * AegisAI Resource Service
 * Manages Rescue Teams, Shelters, and Equipment inventories.
 */

import api from "./api";

export const resourceService = {
    /**
     * Get all rescue teams
     * GET /api/v1/resources/teams
     */
    async getRescueTeams(statusFilter = null) {
        const params = statusFilter ? { status: statusFilter } : {};
        const response = await api.get("/resources/teams", { params });
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Get single rescue team by ID
     * GET /api/v1/resources/teams/{id}
     */
    async getRescueTeam(id) {
        const response = await api.get(`/resources/teams/${id}`);
        return response.data?.data || null;
    },

    /**
     * Update rescue team status or location
     * PUT /api/v1/resources/teams/{id}
     */
    async updateRescueTeam(id, updateData) {
        const response = await api.put(`/resources/teams/${id}`, updateData);
        return response.data?.data || null;
    },

    /**
     * Get all evacuation shelters
     * GET /api/v1/resources/shelters
     */
    async getShelters() {
        const response = await api.get("/resources/shelters");
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Get single shelter by ID
     * GET /api/v1/resources/shelters/{id}
     */
    async getShelter(id) {
        const response = await api.get(`/resources/shelters/${id}`);
        return response.data?.data || null;
    }
};

export default resourceService;
