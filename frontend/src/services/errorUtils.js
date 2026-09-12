/**
 * API Error Utilities
 * Centralized error handling and standardization for API responses
 */

/**
 * Parse API error response into standardized error object
 *
 * @param {Error} error - Axios error object
 * @returns {Object} Standardized error object with message, code, and details
 */
export const parseAPIError = (error) => {
  // Network error (no connection)
  if (error.message === 'Network Error') {
    return {
      message: 'Network connection error. Please check your internet connection.',
      code: 'NETWORK_ERROR',
      status: null,
      details: error,
    };
  }

  // Request timeout
  if (error.code === 'ECONNABORTED') {
    return {
      message: 'Request timeout. The server took too long to respond.',
      code: 'TIMEOUT_ERROR',
      status: null,
      details: error,
    };
  }

  // HTTP error response
  if (error.response) {
    const { status, data } = error.response;

    // Server validation error (400, 422)
    if (status === 400 || status === 422) {
      return {
        message: data?.message || data?.error || 'Invalid request data.',
        code: 'VALIDATION_ERROR',
        status,
        details: data?.details || data?.errors || null,
      };
    }

    // Unauthorized (401)
    if (status === 401) {
      return {
        message: 'Unauthorized. Please log in again.',
        code: 'UNAUTHORIZED',
        status,
        details: null,
      };
    }

    // Forbidden (403)
    if (status === 403) {
      return {
        message: 'You do not have permission to perform this action.',
        code: 'FORBIDDEN',
        status,
        details: null,
      };
    }

    // Not found (404)
    if (status === 404) {
      return {
        message: 'The requested resource was not found.',
        code: 'NOT_FOUND',
        status,
        details: null,
      };
    }

    // Server error (5xx)
    if (status >= 500) {
      return {
        message: data?.message || 'Server error. Please try again later.',
        code: 'SERVER_ERROR',
        status,
        details: null,
      };
    }
  }

  // Unknown error
  return {
    message: error.message || 'An unknown error occurred.',
    code: 'UNKNOWN_ERROR',
    status: null,
    details: error,
  };
};

/**
 * Get user-friendly error message for display
 *
 * @param {Error|Object} error - Axios error or parsed error object
 * @returns {string} User-friendly error message
 */
export const getErrorMessage = (error) => {
  if (typeof error === 'string') {
    return error;
  }

  // If already parsed (has 'message' property)
  if (error?.message) {
    return error.message;
  }

  // Parse if it's an axios error
  const parsed = parseAPIError(error);
  return parsed.message;
};

/**
 * Format error for logging with context
 *
 * @param {Error} error - Axios error
 * @param {string} context - Context label (e.g., "Investigation Decision")
 * @returns {string} Formatted error log message
 */
export const logAPIError = (error, context = 'API') => {
  const parsed = parseAPIError(error);
  console.error(`[${context}] ${parsed.code}: ${parsed.message}`, {
    status: parsed.status,
    details: parsed.details,
    error,
  });
  return parsed;
};

/**
 * Validate API response data has required fields
 *
 * @param {Object} data - Response data to validate
 * @param {string[]} requiredFields - List of required field names
 * @returns {Object} { valid: boolean, missingFields: string[] }
 */
export const validateResponseData = (data, requiredFields = []) => {
  const missingFields = [];

  for (const field of requiredFields) {
    if (data?.[field] === undefined || data[field] === null) {
      missingFields.push(field);
    }
  }

  return {
    valid: missingFields.length === 0,
    missingFields,
  };
};

/**
 * Create a standardized API response object
 * Useful for consistent handling across components
 *
 * @param {Object} options - Response options
 * @returns {Object} Standardized response object
 */
export const createAPIResponse = ({
  success = true,
  data = null,
  message = '',
  error = null,
  statusCode = 200,
}) => ({
  success,
  data,
  message,
  error,
  statusCode,
  timestamp: new Date().toISOString(),
});
