/**
 * Centralized API Service Layer
 * Handles all communication with the DataShield backend
 *
 * Configuration:
 * - Base URL: process.env.REACT_APP_API_URL or http://localhost:5000
 * - API Key: process.env.REACT_APP_API_KEY (optional)
 */

import axios from 'axios';

// ============================================================================
// Configuration
// ============================================================================

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const API_KEY = process.env.REACT_APP_API_KEY;

// ============================================================================
// Axios Client Setup
// ============================================================================

/**
 * Primary API client for all HTTP requests
 * Includes request/response interceptors for auth and error handling
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Add API key to headers if provided
if (API_KEY) {
  apiClient.defaults.headers.common['X-API-KEY'] = API_KEY;
}

// Request interceptor - add auth tokens if needed
apiClient.interceptors.request.use(
  (config) => {
    // Add custom headers or tokens here
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle common error scenarios
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle specific HTTP status codes
    if (error.response?.status === 401) {
      // Unauthorized - could redirect to login
      console.error('[API] Unauthorized access (401)');
    } else if (error.response?.status === 500) {
      console.error('[API] Server error (500):', error.response.data?.message);
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Alerts API (Real Backend Endpoints)
// ============================================================================

/**
 * Alerts Management APIs
 * These are the real, implemented backend endpoints for alert retrieval
 */
export const alertsAPI = {
  /**
   * Get all pending alerts (both upload and file activity)
   *
   * @returns {Promise} Array of alert objects with combined upload and file activity alerts
   * @throws {Error} Network errors
   *
   * Endpoint: GET /alerts
   * Success: Returns array of alerts with all fields
   * Response Format: [
   *   {
   *     id, type, user, timestamp, channel, riskScore, severity,
   *     status, activity, file, fileSize, isSensitive, sensitiveMatches
   *   },
   *   ...
   * ]
   */
  getAll: () => apiClient.get('/alerts'),

  /**
   * Get individual alert details by ID
   *
   * @param {number} id - The alert ID
   * @returns {Promise} Single alert object
   * @throws {Error} Network or validation errors
   *
   * Endpoint: GET /alerts/<id>
   * Success: Returns alert details
   */
  getById: (id) => apiClient.get(`/alerts/${id}`),
};

// ============================================================================
// File Activity & Decision API (Real Backend Endpoints)
// ============================================================================

/**
 * File Activity and Decision Management APIs
 * These are the real, implemented backend endpoints
 *
 * Reference: These endpoints are actively used by the DataShield backend
 * for tracking file activity and managing analyst decisions on alerts
 */
export const fileActivityAPI = {
  /**
   * Submit an analyst decision on a detected file activity alert
   *
   * @param {number} alertId - The alert ID to make a decision on
   * @param {string} action - Decision action: 'allow' or 'block'
   * @returns {Promise} API response with decision confirmation
   * @throws {Error} Network or validation errors
   *
   * Endpoint: POST /upload_decision
   * Success: Returns decision confirmation and ID for tracking
   * Errors: Validation errors if alert doesn't exist or decision is invalid
   */
  submitDecision: (alertId, action) =>
    apiClient.post('/upload_decision', {
      alert_id: parseInt(alertId),
      decision: action,
    }),

  /**
   * Check if a decision was previously made for a specific file upload
   *
   * @param {number} uploadId - The upload ID to check
   * @returns {Promise} API response with decision status or undefined if no decision
   * @throws {Error} Network errors
   *
   * Endpoint: GET /check_decision/<uploadId>
   * Success: Returns decision info if one exists
   */
  checkDecision: (uploadId) =>
    apiClient.get(`/check_decision/${uploadId}`),

  /**
   * Retrieve all file activities that are pending analyst review
   *
   * @returns {Promise} Array of pending decision objects
   * @throws {Error} Network errors
   *
   * Endpoint: GET /pending_decisions
   * Success: Returns array of pending file activities
   */
  getPendingDecisions: () =>
    apiClient.get('/pending_decisions'),

  /**
   * Mark a specific file activity alert as dismissed
   * Prevents it from appearing in alert lists while keeping record
   *
   * @param {number} alertId - The alert ID to dismiss
   * @returns {Promise} API response with dismissal confirmation
   * @throws {Error} Network or validation errors
   *
   * Endpoint: POST /dismiss_file_activity
   * Success: Returns dismissal confirmation
   */
  dismissFileActivity: (alertId) =>
    apiClient.post('/dismiss_file_activity', {
      alert_id: parseInt(alertId),
    }),

  /**
   * Clear all file activity alerts from the system
   * WARNING: This is a destructive operation
   *
   * @returns {Promise} API response with count of cleared activities
   * @throws {Error} Network errors
   *
   * Endpoint: POST /clear_all_file_activities
   * Success: Returns count of cleared activities
   */
  clearAllFileActivities: () =>
    apiClient.post('/clear_all_file_activities'),
};

// ============================================================================
// User Activity API
// ============================================================================

/**
 * User Activity Management APIs
 * Used by the UserActivity page to retrieve user analytics and risk data
 */
export const usersAPI = {
  /**
   * Get user activity data including risk scores, trends, and anomalies
   *
   * @returns {Promise} User activity data with trends and anomalies
   * @throws {Error} Network errors
   *
   * Endpoint: GET /api/users/activity
   * Success: Returns user list, risk trends, and detected anomalies
   * Response Format: {
   *   users: [{ id, email, riskScore, status, lastActivity, alertCount, activities }],
   *   userRiskTrend: [{ week, userScores... }],
   *   anomalies: [{ id, user, anomaly, severity, timestamp }]
   * }
   */
  getActivity: () => apiClient.get('/api/users/activity'),
};

// ============================================================================
// Reports API
// ============================================================================

/**
 * Reports Management APIs
 * Used by the Reports page to retrieve various report data
 */
export const reportsAPI = {
  /**
   * Get report summary statistics
   *
   * @returns {Promise} Summary statistics
   * @throws {Error} Network errors
   *
   * Endpoint: GET /api/reports/summary
   * Success: Returns key metrics and incident counts
   * Response Format: {
   *   totalIncidents, incidentsBlocked, investigated, avgResponseTime
   * }
   */
  getSummary: () => apiClient.get('/api/reports/summary'),

  /**
   * Get alert trends data for chart visualization
   *
   * @returns {Promise} Alert trends over time
   * @throws {Error} Network errors
   *
   * Endpoint: GET /api/reports/alerts
   * Success: Returns daily alert and blocked counts
   * Response Format: [{ date, alerts, blocked }, ...]
   */
  getAlertTrends: () => apiClient.get('/api/reports/alerts'),

  /**
   * Get threat analysis and classification data
   *
   * @returns {Promise} Threat analysis data
   * @throws {Error} Network errors
   *
   * Endpoint: GET /api/reports/threats
   * Success: Returns top threats with classifications
   * Response Format: [{ name, count, percentage, severity }, ...]
   */
  getThreatAnalysis: () => apiClient.get('/api/reports/threats'),

  /**
   * Get user risk report data including department analysis
   *
   * @returns {Promise} User risk report data
   * @throws {Error} Network errors
   *
   * Endpoint: GET /api/reports/users
   * Success: Returns department risk data and top users
   * Response Format: {
   *   departmentRisk: [{ department, risk, users, incidents }],
   *   topUsers: [{ id, email, department, riskScore, incidents, severity }]
   * }
   */
  getUserReports: () => apiClient.get('/api/reports/users'),
};

// Legacy alias for backward compatibility with Investigation page
export const decisionsAPI = fileActivityAPI;

export default apiClient;
