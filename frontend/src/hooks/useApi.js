/**
 * Custom React Hook for API calls
 * Provides centralized API call handling with error management and loading states
 */
import { useState, useCallback } from "react";
import axios from "axios";
import { API_ENDPOINTS, buildQueryString, API_CONFIG } from "../config/api";
import { logError, formatErrorForDisplay } from "../utils/errorHandler";

/**
 * Custom hook for making API calls
 * Handles loading, error, and success states automatically
 *
 * @returns {Object} Hook utilities {get, post, put, delete, loading, error}
 *
 * @example
 * const { get, loading, error } = useApi();
 *
 * useEffect(() => {
 *   get(API_ENDPOINTS.FILTERS).then(data => {
 *     setFilterOptions(data);
 *   });
 * }, [get]);
 */
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  /**
   * Retry logic for failed requests
   */
  const retryRequest = useCallback(
    async (fn, retryCount = API_CONFIG.RETRY_COUNT) => {
      let lastError;

      for (let attempt = 0; attempt < retryCount; attempt++) {
        try {
          return await fn();
        } catch (err) {
          lastError = err;

          // Check if error is retriable
          if (err.response?.status === 429 || err.response?.status === 503) {
            const delay = API_CONFIG.RETRY_DELAY * (attempt + 1);
            await new Promise((resolve) => setTimeout(resolve, delay));
            continue;
          }

          throw err;
        }
      }

      throw lastError;
    },
    [],
  );

  /**
   * Generic request function
   */
  const request = useCallback(
    async (method, url, data = null) => {
      setLoading(true);
      setError(null);

      try {
        const config = {
          method,
          url,
          timeout: API_CONFIG.TIMEOUT,
        };

        if (data) {
          if (method.toLowerCase() === "get") {
            config.params = data;
          } else {
            config.data = data;
          }
        }

        const response = await retryRequest(() => axios(config));
        setLoading(false);

        return response.data;
      } catch (err) {
        const formattedError = formatErrorForDisplay(err);
        setError(formattedError);
        logError(`API ${method.toUpperCase()} ${url}`, err);

        setLoading(false);
        throw formattedError;
      }
    },
    [retryRequest],
  );

  /**
   * GET request helper
   */
  const get = useCallback(
    (url, params = null) => {
      return request("GET", url, params);
    },
    [request],
  );

  /**
   * POST request helper
   */
  const post = useCallback(
    (url, data) => {
      return request("POST", url, data);
    },
    [request],
  );

  /**
   * PUT request helper
   */
  const put = useCallback(
    (url, data) => {
      return request("PUT", url, data);
    },
    [request],
  );

  /**
   * DELETE request helper
   */
  const deleteRequest = useCallback(
    (url) => {
      return request("DELETE", url);
    },
    [request],
  );

  /**
   * Batch request helper - fetch multiple endpoints in parallel
   */
  const batch = useCallback(async (requests) => {
    setLoading(true);
    setError(null);

    try {
      const results = await Promise.all(
        requests.map((req) =>
          axios({
            method: req.method || "GET",
            url: req.url,
            params: req.params,
            timeout: API_CONFIG.TIMEOUT,
          }),
        ),
      );

      setLoading(false);
      return results.map((r) => r.data);
    } catch (err) {
      const formattedError = formatErrorForDisplay(err);
      setError(formattedError);
      logError("API batch request", err);
      setLoading(false);
      throw formattedError;
    }
  }, []);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Reset loading & error state
   */
  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
  }, []);

  return {
    // Request methods
    get,
    post,
    put,
    delete: deleteRequest,
    batch,
    request,

    // State
    loading,
    error,

    // State management
    clearError,
    reset,
  };
};

export default useApi;
