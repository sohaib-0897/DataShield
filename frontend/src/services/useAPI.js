/**
 * Custom React Hooks for API Calls
 * Provides loading, error, and data state management
 */

import React, { useState, useCallback } from 'react';
import { parseAPIError } from './errorUtils';

/**
 * Hook for making async API calls with loading and error states
 *
 * Usage:
 *   const { data, loading, error, execute } = useAsync(myApiCall);
 *
 *   // Later:
 *   await execute(arg1, arg2);
 *
 * @param {Function} asyncFunction - Async function to execute (API call)
 * @returns {Object} { data, loading, error, execute, reset }
 */
export const useAsync = (asyncFunction) => {
  const [state, setState] = useState({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...args) => {
      setState({ data: null, loading: true, error: null });

      try {
        const result = await asyncFunction(...args);
        const responseData = result?.data || result;

        setState({
          data: responseData,
          loading: false,
          error: null,
        });

        return responseData;
      } catch (err) {
        const parsedError = parseAPIError(err);

        setState({
          data: null,
          loading: false,
          error: parsedError,
        });

        throw parsedError;
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
};

/**
 * Hook for fetching data on component mount
 *
 * Usage:
 *   const { data, loading, error, refetch } = useFetch(() => api.getData());
 *
 * @param {Function} fetchFunction - Function that returns a Promise
 * @param {Array} dependencies - Dependencies array (optional)
 * @returns {Object} { data, loading, error, refetch }
 */
export const useFetch = (fetchFunction, dependencies = []) => {
  const [state, setState] = useState({
    data: null,
    loading: true,
    error: null,
  });

  const refetch = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));

    try {
      const result = await fetchFunction();
      const responseData = result?.data || result;

      setState({
        data: responseData,
        loading: false,
        error: null,
      });

      return responseData;
    } catch (err) {
      const parsedError = parseAPIError(err);

      setState({
        data: null,
        loading: false,
        error: parsedError,
      });

      return null;
    }
  }, [fetchFunction]);

  // Trigger fetch on mount or when dependencies change
  React.useEffect(() => {
    refetch();
  }, dependencies); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    ...state,
    refetch,
  };
};

/**
 * Hook for mutations (POST, PUT, DELETE)
 * Different from fetch - doesn't execute on mount
 *
 * Usage:
 *   const { execute: submitData, loading, error } = useMutation(api.submit);
 *
 *   const handleSubmit = async () => {
 *     await submitData(formData);
 *   };
 *
 * @param {Function} mutationFunction - Async function for the mutation
 * @returns {Object} { execute, loading, error, data, reset }
 */
export const useMutation = (mutationFunction) => {
  const { execute, loading, error, data, reset } = useAsync(mutationFunction);

  return {
    execute,
    loading,
    error,
    data,
    reset,
  };
};

/**
 * Hook for managing API call with automatic retry on failure
 *
 * Usage:
 *   const { data, loading, error } = useAsyncWithRetry(
 *     () => api.getData(),
 *     { maxRetries: 3, retryDelay: 1000 }
 *   );
 *
 * @param {Function} asyncFunction - Async function to execute
 * @param {Object} options - Retry options
 * @returns {Object} { data, loading, error, retry }
 */
export const useAsyncWithRetry = (
  asyncFunction,
  { maxRetries = 3, retryDelay = 1000 } = {}
) => {
  const [state, setState] = useState({
    data: null,
    loading: true,
    error: null,
    retryCount: 0,
  });

  const execute = useCallback(async () => {
    let lastError;

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        setState((prev) => ({
          ...prev,
          loading: true,
          error: null,
          retryCount: attempt,
        }));

        const result = await asyncFunction();
        const responseData = result?.data || result;

        setState({
          data: responseData,
          loading: false,
          error: null,
          retryCount: 0,
        });

        return responseData;
      } catch (err) {
        lastError = err;

        // Don't retry if it's not a retryable error (e.g., 401, 403, 422)
        const isRetryable =
          !err.response || err.response.status >= 500 || err.code === 'ECONNABORTED';

        if (!isRetryable || attempt === maxRetries) {
          const parsedError = parseAPIError(err);

          setState({
            data: null,
            loading: false,
            error: parsedError,
            retryCount: attempt,
          });

          throw parsedError;
        }

        // Wait before retrying
        if (attempt < maxRetries) {
          await new Promise((resolve) =>
            setTimeout(resolve, retryDelay * Math.pow(2, attempt))
          );
        }
      }
    }

    throw lastError;
  }, [asyncFunction, maxRetries, retryDelay]);

  const reset = useCallback(() => {
    setState({
      data: null,
      loading: false,
      error: null,
      retryCount: 0,
    });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
};
