/**
 * AegisAI Mission & Dispatch Service
 * Handles rescue team dispatching, assignment status transitions, and mission tracking HUD.
 */

import api from "./api";

export const missionService = {
    /**
     * Get all missions / active missions
     * GET /api/v1/missions
     */
    async getMissions(activeOnly = false) {
        const response = await api.get("/missions", {
            params: { active_only: activeOnly }
        });
        const missions = response.data?.data || [];
        return {
            success: true,
            data: missions
        };
    },

    /**
     * Dispatch a rescue team to an incident (create assignment)
     * POST /api/v1/assignments
     */
    async createAssignment(incidentId, teamId, options = {}) {
        const payload = {
            incident_id: incidentId,
            team_id: teamId,
            ...options
        };
        const response = await api.post("/assignments", payload);
        return response.data?.data || null;
    },

    /**
     * List all resource assignments
     * GET /api/v1/assignments
     */
    async getAssignments(params = {}) {
        const response = await api.get("/assignments", { params });
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Get single assignment by ID
     * GET /api/v1/assignments/{id}
     */
    async getAssignment(id) {
        const response = await api.get(`/assignments/${id}`);
        return response.data?.data || null;
    },

    /**
     * Advance assignment lifecycle status
     * PUT /api/v1/assignments/{id}/status
     * Statuses: ASSIGNED | DISPATCHED | EN_ROUTE | ARRIVED | COMPLETED | CANCELLED
     */
    async updateAssignmentStatus(assignmentId, newStatus) {
        const response = await api.put(`/assignments/${assignmentId}/status`, {
            status: newStatus
        });
        return response.data?.data || null;
    },

    /**
     * Update assignment details
     * PUT /api/v1/assignments/{id}
     */
    async updateAssignment(assignmentId, updateData) {
        const response = await api.put(`/assignments/${assignmentId}`, updateData);
        return response.data?.data || null;
    }
};

export default missionService;
