/**
 * AegisAI Prediction Module — Frontend API Client.
 *
 * Provides typed methods for predictive dashboard data, time-horizon forecasts,
 * predictive alerts, and AI decision support.
 */

import api from './api';

const predictionService = {
  /**
   * Fetch consolidated command-center predictive dashboard payload.
   * @param {string} [simulationId]
   * @returns {Promise<{success: boolean, data: object}>}
   */
  async getPredictiveDashboard(simulationId = null) {
    const params = simulationId ? { simulation_id: simulationId } : {};
    const response = await api.get('/predictions/dashboard', { params });
    return response.data;
  },

  /**
   * Fetch dedicated casualty surge forecast (+5m, +15m, +30m, +60m).
   */
  async getCasualtyForecast() {
    const response = await api.get('/predictions/casualties');
    return response.data;
  },

  /**
   * Fetch dedicated hospital load & ICU saturation forecast.
   */
  async getHospitalForecast() {
    const response = await api.get('/predictions/hospitals');
    return response.data;
  },

  /**
   * Fetch dedicated resource demand and fleet shortage forecast.
   */
  async getResourceForecast() {
    const response = await api.get('/predictions/resources');
    return response.data;
  },

  /**
   * Fetch spatial disaster risk and propagation forecast.
   */
  async getDisasterRiskForecast() {
    const response = await api.get('/predictions/disaster-risk');
    return response.data;
  },

  /**
   * Fetch multi-horizon fire spread propagation zones.
   */
  async getFireSpreadForecast() {
    const response = await api.get('/predictions/fire-spread');
    return response.data;
  },

  /**
   * Fetch flood inundation and road closure forecast.
   */
  async getFloodRiskForecast() {
    const response = await api.get('/predictions/flood-risk');
    return response.data;
  },

  /**
   * Fetch prediction history and accuracy records.
   */
  async getPredictionHistory(params = {}) {
    const response = await api.get('/predictions/history', { params });
    return response.data;
  },

  /**
   * Record actual observed outcome against a previous prediction.
   */
  async recordOutcome(recordId, actualValue, errorRate = null) {
    const response = await api.post(`/predictions/history/${recordId}/outcome`, {
      actual_value: actualValue,
      error_rate: errorRate,
    });
    return response.data;
  },

  /**
   * Legacy disaster spread prediction.
   */
  async predictSpread(payload) {
    const response = await api.post('/predictions/spread', payload);
    return response.data;
  },

  /**
   * Resource allocation optimization pass.
   */
  async optimizeResources(payload) {
    const response = await api.post('/predictions/optimize', payload);
    return response.data;
  },

  /**
   * Reinforcement Learning next-best action recommendation.
   */
  async getRLRecommendation(payload) {
    const response = await api.post('/predictions/recommend', payload);
    return response.data;
  },

  /**
   * Explainable AI decision explanation.
   */
  async explainDecision(payload) {
    const response = await api.post('/predictions/explain', payload);
    return response.data;
  },
};

export default predictionService;
