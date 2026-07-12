/**
 * API Service Configuration
 * Centralized API endpoint configuration and helper functions
 */

// ============================================================================
// API BASE URL
// ============================================================================
// Development  : menggunakan proxy Vite (/api)
// Production   : menggunakan URL backend dari Vercel
// ============================================================================

const API_BASE_URL = import.meta.env.DEV
  ? "/api"
  : import.meta.env.VITE_API_URL || "";

// ============================================================================
// API ENDPOINTS
// ============================================================================

export const API_ENDPOINTS = {
  // --------------------------------------------------------------------------
  // General
  // --------------------------------------------------------------------------
  FILTERS: `${API_BASE_URL}/filters`,
  STATISTICS: `${API_BASE_URL}/stats`,
  EMPLOYEE_SIZES: `${API_BASE_URL}/employee-sizes`,

  // --------------------------------------------------------------------------
  // Jobs
  // --------------------------------------------------------------------------
  JOBS: `${API_BASE_URL}/jobs`,

  // --------------------------------------------------------------------------
  // Skills
  // --------------------------------------------------------------------------
  TOP_SKILLS: `${API_BASE_URL}/skills/top`,

  // --------------------------------------------------------------------------
  // Authentication
  // --------------------------------------------------------------------------
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    PROFILE: `${API_BASE_URL}/auth/profile`,
  },

  // --------------------------------------------------------------------------
  // Dashboard
  // --------------------------------------------------------------------------
  DASHBOARD: {
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

    // Data dari JOB_ANALYSIS
    TOP_SKILLS_BY_TYPE_FROM_ANALYSIS: `${API_BASE_URL}/dashboard/top-skills-by-type-from-analysis`,
    SKILLS_DISTRIBUTION_FROM_ANALYSIS: `${API_BASE_URL}/dashboard/skills-distribution-from-analysis`,
    TREND_BY_MONTH_FROM_ANALYSIS: `${API_BASE_URL}/dashboard/trend-by-month-from-analysis`,
  },

  // --------------------------------------------------------------------------
  // Admin
  // --------------------------------------------------------------------------
  ADMIN: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    LOGOUT: `${API_BASE_URL}/admin/logout`,
    PROFILE: `${API_BASE_URL}/admin/profile`,

    SCRAPE: `${API_BASE_URL}/admin/scrape`,
    SCRAPING_OVERVIEW: `${API_BASE_URL}/admin/scraping-overview`,
    EXTRACT_SKILLS: `${API_BASE_URL}/admin/extract-skills`,

    KEYWORDS: `${API_BASE_URL}/admin/keywords`,
  },

  // --------------------------------------------------------------------------
  // Job Analysis
  // --------------------------------------------------------------------------
  JOB_ANALYSIS: `${API_BASE_URL}/job-analysis`,
  JOB_ANALYSIS_LOCATIONS: `${API_BASE_URL}/job-analysis/locations`,
};

// ============================================================================
// QUERY STRING HELPER
// ============================================================================

export const buildQueryString = (params) => {
  const urlParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== "" && value !== null && value !== undefined) {
      urlParams.append(key, value);
    }
  });

  return urlParams.toString();
};

// ============================================================================
// ERROR HELPER
// ============================================================================

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

// ============================================================================
// API CONFIG
// ============================================================================

export const API_CONFIG = {
  TIMEOUT: 15000,
  RETRY_COUNT: 3,
  RETRY_DELAY: 1000,
};

// ============================================================================

export default {
  API_BASE_URL,
  API_ENDPOINTS,
  API_CONFIG,
  buildQueryString,
  getErrorMessage,
};
