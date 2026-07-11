/**
 * API Service Configuration
 * Centralized API endpoint configuration and helper functions
 */

// API Base URL - use relative path for development (Vite proxy), absolute for production
const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV ? "/api" : "http://localhost:8000/api");

/**
 * API endpoint constants
 */
export const API_ENDPOINTS = {
  // ✅ Filters & metadata - SUDAH BENAR
  FILTERS: `${API_BASE_URL}/filters`,
  STATISTICS: `${API_BASE_URL}/stats`,
  EMPLOYEE_SIZES: `${API_BASE_URL}/employee-sizes`,

  // ✅ Dashboard data - SEMUA HARUS TANPA /api tambahan
  DASHBOARD: {
    // Endpoint dari JOBS table (lama)
    TOP_SKILLS_BY_TYPE: `${API_BASE_URL}/dashboard/top-skills-by-type`,
    ALL_SKILLS_BY_TYPE: `${API_BASE_URL}/dashboard/all-skills-by-type`,
    SKILL_TREND: `${API_BASE_URL}/dashboard/skill-trend`,
    SKILL_TRENDS: `${API_BASE_URL}/dashboard/trend-by-month`,
    SKILL_DISTRIBUTION: `${API_BASE_URL}/dashboard/skills-distribution`,
    SKILLS_TREND_TIMELINE: `${API_BASE_URL}/dashboard/skills-trend-timeline`,
    TREND_BY_MONTH: `${API_BASE_URL}/dashboard/trend-by-month`,
    SKILLS_BY_TYPE: `${API_BASE_URL}/dashboard/skill-types`,
    SKILL_JOBS: `${API_BASE_URL}/dashboard/top-skills-ranked`,
    SKILL_ALTERNATIVES: `${API_BASE_URL}/dashboard/skill-alternatives`,
    ANALYSIS: `${API_BASE_URL}/dashboard/analysis`,
    TOP_COMPANIES_BY_SKILL: `${API_BASE_URL}/dashboard/top-companies-by-skill`,
    
    // ✅ Endpoint dari JOB_ANALYSIS table (baru) - TANPA /api tambahan!
    TOP_SKILLS_BY_TYPE_FROM_ANALYSIS: `${API_BASE_URL}/dashboard/top-skills-by-type-from-analysis`,
    SKILLS_DISTRIBUTION_FROM_ANALYSIS: `${API_BASE_URL}/dashboard/skills-distribution-from-analysis`,
    TREND_BY_MONTH_FROM_ANALYSIS: `${API_BASE_URL}/dashboard/trend-by-month-from-analysis`,
  },

  // ✅ Admin endpoints
  ADMIN: {
    SCRAPE: `${API_BASE_URL}/admin/scrape`,
    EXTRACT_SKILLS: `${API_BASE_URL}/admin/extract-skills`,
    SCRAPING_OVERVIEW: `${API_BASE_URL}/admin/scraping-overview`,
    LOGIN: `${API_BASE_URL}/admin/login`,
    LOGOUT: `${API_BASE_URL}/admin/logout`,
    PROFILE: `${API_BASE_URL}/admin/profile`,
  },

  // ✅ Job Analysis endpoints
  JOB_ANALYSIS: `${API_BASE_URL}/job-analysis`,
  JOB_ANALYSIS_LOCATIONS: `${API_BASE_URL}/job-analysis/locations`,
};

/**
 * Query parameter builder helper
 */
export const buildQueryString = (params) => {
  const urlParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      urlParams.append(key, value);
    }
  });

  return urlParams.toString();
};

/**
 * Get error message from API response
 */
export const getErrorMessage = (error) => {
  if (!error) return "Unknown error occurred";

  if (error.response) {
    return (
      error.response.data?.detail ||
      error.response.data?.message ||
      error.response.statusText ||
      "Server error occurred"
    );
  }

  if (error.request) {
    return "No response from server. Check your connection.";
  }

  return error.message || "Network error occurred";
};

/**
 * API configuration constants
 */
export const API_CONFIG = {
  TIMEOUT: 15000,      // 15 seconds request timeout
  RETRY_COUNT: 3,      // Number of retries on retriable errors
  RETRY_DELAY: 1000,   // Base retry delay in milliseconds
};

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  API_CONFIG,
  buildQueryString,
  getErrorMessage,
};