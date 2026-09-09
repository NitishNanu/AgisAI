/**
 * AegisAI — AI Decision Engine Frontend Client Service.
 *
 * Provides typed methods for interfacing with the backend AI Decision Intelligence endpoints.
 */

import api from './api';

export const aiDecisionService = {
  /**
   * Trigger AI decision generation across active incidents.
   * @param {Object} options - { policy_type, incident_ids, simulation_id, execution_mode, custom_weights, generate_llm_explanation }
   */
  async generateDecisions(options = {}) {
    const response = await api.post('/ai/decisions/generate', {
      policy_type: options.policy_type || 'OPTIMIZED',
      incident_ids: options.incident_ids || null,
      simulation_id: options.simulation_id || null,
      execution_mode: options.execution_mode || 'LIVE',
      custom_weights: options.custom_weights || null,
      generate_llm_explanation: options.generate_llm_explanation ?? true,
    });
    return response.data;
  },

  /**
   * List and filter AI decisions with pagination.
   * @param {Object} params - { status, decision_type, incident_id, simulation_id, page, page_size }
   */
  async listDecisions(params = {}) {
    const response = await api.get('/ai/decisions', { params });
    return response.data;
  },

  /**
   * Get single decision details by ID or UUID.
   * @param {string|number} decisionId
   */
  async getDecision(decisionId) {
    const response = await api.get(`/ai/decisions/${decisionId}`);
    return response.data;
  },

  /**
   * Approve an AI decision recommendation.
   * @param {string|number} decisionId
   * @param {Object} payload - { notes, auto_execute }
   */
  async approveDecision(decisionId, payload = { auto_execute: true }) {
    const response = await api.post(`/ai/decisions/${decisionId}/approve`, payload);
    return response.data;
  },

  /**
   * Reject an AI decision recommendation with reason.
   * @param {string|number} decisionId
   * @param {string} rejectionReason
   */
  async rejectDecision(decisionId, rejectionReason) {
    const response = await api.post(`/ai/decisions/${decisionId}/reject`, {
      rejection_reason: rejectionReason,
    });
    return response.data;
  },

  /**
   * Modify an AI decision before approval.
   * @param {string|number} decisionId
   * @param {Object} payload - { override_resource_id, override_hospital_id, modification_notes, auto_execute }
   */
  async modifyDecision(decisionId, payload) {
    const response = await api.post(`/ai/decisions/${decisionId}/modify`, payload);
    return response.data;
  },

  /**
   * Execute an approved AI decision into a live mission.
   * @param {string|number} decisionId
   */
  async executeDecision(decisionId) {
    const response = await api.post(`/ai/decisions/${decisionId}/execute`);
    return response.data;
  },

  /**
   * Retrieve LLM tactical briefing & explainability for a decision.
   * @param {string|number} decisionId
   */
  async getExplanation(decisionId) {
    const response = await api.get(`/ai/decisions/${decisionId}/explanation`);
    return response.data;
  },

  /**
   * Run comparative policy benchmarking (Baseline vs Heuristic vs Optimization vs ML).
   * @param {Object} payload - { policies_to_compare, incident_ids }
   */
  async benchmarkPolicies(payload = {}) {
    const response = await api.post('/ai/decisions/benchmark', payload);
    return response.data;
  },

  /**
   * Simulate what-if hypothetical disaster conditions.
   * @param {Object} payload - { simulation_id, hypothetical_blocked_roads, hypothetical_disabled_hospitals, hypothetical_severe_weather, policy_type }
   */
  async runWhatIf(payload) {
    const response = await api.post('/ai/decisions/what-if', payload);
    return response.data;
  },

  /**
   * Submit commander feedback or recorded outcome telemetry.
   * @param {string|number} decisionId
   * @param {Object} payload - { feedback_type, actual_outcome, comments }
   */
  async submitFeedback(decisionId, payload) {
    const response = await api.post(`/ai/decisions/${decisionId}/feedback`, payload);
    return response.data;
  },
};

export default aiDecisionService;
