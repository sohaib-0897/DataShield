/**
 * API Request Utilities
 * Consistent patterns for making API calls with error handling and logging
 */

import { logAPIError, validateResponseData } from './errorUtils';

/**
 * Execute an API call with automatic logging and error handling
 *
 * Usage:
 *   const result = await apiRequest(fileActivityAPI.submitDecision, [alertId, 'block'], {
 *     context: 'Submit Decision',
 *     requiredFields: ['decision_id', 'status'],
 *   });
 *
 * @param {Function} apiFunction - API function to call
 * @param {Array} args - Arguments to pass to the function
 * @param {Object} options - Configuration options
 * @returns {Promise} API response or throws error
 */
export const apiRequest = async (
  apiFunction,
  args = [],
  {
    context = 'API Request',
    requiredFields = [],
    throwOnValidationError = true,
  } = {}
) => {
  try {
    // Ensure args is always an array
    const callArgs = Array.isArray(args) ? args : [args];

    // Execute the API call
    const response = await apiFunction(...callArgs);
    const responseData = response?.data || response;

    // Validate response has required fields
    if (requiredFields.length > 0) {
      const validation = validateResponseData(responseData, requiredFields);

      if (!validation.valid) {
        console.warn(
          `[${context}] Response missing fields: ${validation.missingFields.join(', ')}`
        );

        if (throwOnValidationError) {
          throw new Error(
            `Response validation failed. Missing: ${validation.missingFields.join(', ')}`
          );
        }
      }
    }

    console.log(`[${context}] Success`, responseData);
    return responseData;
  } catch (error) {
    const parsed = logAPIError(error, context);
    throw parsed;
  }
};

/**
 * Safely call an API function with fallback/default value
 * Useful when you have mock data as fallback
 *
 * Usage:
 *   const alerts = await apiRequestWithFallback(
 *     fileActivityAPI.getPendingDecisions,
 *     mockAlerts, // fallback/default value
 *     { context: 'Load Pending Alerts' }
 *   );
 *
 * @param {Function} apiFunction - API function to call
 * @param {*} fallbackValue - Value to return if API fails
 * @param {Object} options - Configuration options
 * @returns {Promise} API response or fallback value
 */
export const apiRequestWithFallback = async (
  apiFunction,
  fallbackValue,
  { context = 'API Request', logError = true, throwError = false } = {}
) => {
  try {
    const response = await apiFunction();
    console.log(`[${context}] Success`);
    return response?.data || response;
  } catch (error) {
    if (logError) {
      logAPIError(error, context);
    }

    if (throwError) {
      throw error;
    }

    console.log(`[${context}] Using fallback value`);
    return fallbackValue;
  }
};

/**
 * Create a request interceptor for a specific API call
 * Useful for adding request/response transformation
 *
 * Usage:
 *   const transformedCall = wrapAPICall(api.submitDecision, {
 *     beforeRequest: (args) => console.log('Sending:', args),
 *     afterResponse: (data) => ({ ...data, processed: true }),
 *   });
 *
 * @param {Function} apiFunction - API function to wrap
 * @param {Object} interceptors - Before/after hooks
 * @returns {Function} Wrapped API function
 */
export const wrapAPICall = (apiFunction, { beforeRequest, afterResponse } = {}) => {
  return async (...args) => {
    // Before request hook
    if (beforeRequest) {
      beforeRequest(...args);
    }

    // Execute request
    const response = await apiFunction(...args);
    const responseData = response?.data || response;

    // After response hook
    if (afterResponse) {
      return afterResponse(responseData);
    }

    return responseData;
  };
};

/**
 * Retry an API call with exponential backoff
 *
 * Usage:
 *   const result = await retryAPICall(
 *     () => api.getData(),
 *     { maxRetries: 3, baseDelay: 1000 }
 *   );
 *
 * @param {Function} apiFunction - API function to retry
 * @param {Object} options - Retry options
 * @returns {Promise} API response
 */
export const retryAPICall = async (
  apiFunction,
  { maxRetries = 3, baseDelay = 1000, context = 'API Request' } = {}
) => {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 0) {
        console.log(`[${context}] Retry attempt ${attempt} of ${maxRetries}`);
      }

      return await apiFunction();
    } catch (error) {
      lastError = error;

      // Check if error is retryable
      const isRetryable = !error.response || error.response.status >= 500;

      if (!isRetryable || attempt === maxRetries) {
        logAPIError(error, context);
        throw error;
      }

      // Exponential backoff
      const delay = baseDelay * Math.pow(2, attempt);
      console.log(`[${context}] Retrying after ${delay}ms...`);
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }

  throw lastError;
};

/**
 * Convert an API response to a standardized format
 * Extends apiRequest with custom transformation
 *
 * @param {Function} apiFunction - API function to call
 * @param {Array} args - Arguments for the function
 * @param {Function} transformer - Transform response to desired format
 * @returns {Promise} Transformed response
 */
export const apiRequestWithTransform = async (
  apiFunction,
  args = [],
  transformer = (data) => data
) => {
  const response = await apiRequest(apiFunction, args);
  return transformer(response);
};
