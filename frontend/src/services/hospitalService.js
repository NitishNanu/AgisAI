/**
 * AegisAI Hospital Service
 * Handles hospital directory, capacity telemetry, and emergency bed occupancy.
 */

import api from "./api";

export const hospitalService = {
    /**
     * Get all hospitals with bed and ICU capacity
     * GET /api/v1/hospitals
     */
    async getHospitals(operationalOnly = false) {
        const response = await api.get("/hospitals", {
            params: { operational_only: operationalOnly }
        });
        return response.data?.data?.items || response.data?.data || [];
    },

    /**
     * Get single hospital by ID
     * GET /api/v1/hospitals/{id}
     */
    async getHospital(id) {
        const response = await api.get(`/hospitals/${id}`);
        return response.data?.data || null;
    },

    /**
     * Update hospital capacity
     * PATCH /api/v1/hospitals/{id}/capacity
     */
    async updateCapacity(id, capacityData) {
        const response = await api.patch(`/hospitals/${id}/capacity`, capacityData);
        return response.data?.data || null;
    }
};

export default hospitalService;
