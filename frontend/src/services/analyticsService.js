/**
 * AegisAI Analytics & Telemetry Service
 * Queries dashboard KPIs, metrics snapshots, and incident reports.
 */

import api from "./api";

export const analyticsService = {
    /**
     * Get consolidated dashboard telemetry & system health metrics
     * GET /api/v1/analytics/dashboard
     */
    async getDashboardMetrics() {
        const response = await api.get("/analytics/dashboard");
        return response.data?.data || null;
    },

    /**
     * Get incident classification statistics
     * GET /api/v1/analytics/incidents/summary
     */
    async getIncidentSummary() {
        const response = await api.get("/analytics/incidents/summary");
        return response.data?.data || null;
    },

    /**
     * Generate an incident situation report
     * POST /api/v1/analytics/reports/generate
     */
    async generateReport(title = "Emergency Operations Report") {
        const response = await api.post("/analytics/reports/generate", { title });
        return response.data?.data || null;
    }
};

export default analyticsService;
