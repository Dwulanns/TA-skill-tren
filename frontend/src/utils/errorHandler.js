/**
 * Error handling utilities
 * Provides consistent error handling across the application
 */
import { getErrorMessage } from "../config/api";

/**
 * Error severity levels
 */
export const ERROR_TYPES = {
  NETWORK: "network",
  VALIDATION: "validation",
  SERVER: "server",
  NOT_FOUND: "not_found",
  UNAUTHORIZED: "unauthorized",
  UNKNOWN: "unknown",
};

/**
 * Determine error type based on error object
 * @param {Error} error - Error object
 * @returns {string} - Error type
 */
export const getErrorType = (error) => {
  if (!error) return ERROR_TYPES.UNKNOWN;

  if (error.response) {
    const status = error.response.status;
    if (status === 404) return ERROR_TYPES.NOT_FOUND;
    if (status === 401 || status === 403) return ERROR_TYPES.UNAUTHORIZED;
    if (status >= 500) return ERROR_TYPES.SERVER;
    if (status >= 400) return ERROR_TYPES.VALIDATION;
  }

  if (error.request) return ERROR_TYPES.NETWORK;
  if (error.message) return ERROR_TYPES.VALIDATION;

  return ERROR_TYPES.UNKNOWN;
};

/**
 * Format error for display to user
 * @param {Error} error - Error object
 * @returns {Object} - {type, message, userMessage}
 */
export const formatErrorForDisplay = (error) => {
  const type = getErrorType(error);
  const message = getErrorMessage(error);

  let userMessage = "";

  switch (type) {
    case ERROR_TYPES.NETWORK:
      userMessage = "Network connection error. Please check your internet.";
      break;
    case ERROR_TYPES.SERVER:
      userMessage = "Server error. Please try again later.";
      break;
    case ERROR_TYPES.NOT_FOUND:
      userMessage = "The requested resource was not found.";
      break;
    case ERROR_TYPES.UNAUTHORIZED:
      userMessage = "Unauthorized access. Please log in.";
      break;
    case ERROR_TYPES.VALIDATION:
      userMessage = "Invalid request. Please check your input.";
      break;
    default:
      userMessage = "An unexpected error occurred.";
  }

  return {
    type,
    message,
    userMessage,
  };
};

/**
 * Log error for debugging (only in development)
 * @param {string} context - Where the error occurred
 * @param {Error} error - Error object
 */
export const logError = (context, error) => {
  if (import.meta.env.DEV) {
    console.error(`[${context}]`, error);
  }
};

/**
 * Check if error is retriable
 * @param {Error} error - Error object
 * @returns {boolean} - Whether the error can be retried
 */
export const isRetriableError = (error) => {
  if (!error?.response) return true; // Network errors are retriable

  const status = error.response.status;
  // Retry on 429 (Too Many Requests), 503 (Service Unavailable)
  return status === 429 || status === 503;
};

export default {
  ERROR_TYPES,
  getErrorType,
  formatErrorForDisplay,
  logError,
  isRetriableError,
};
