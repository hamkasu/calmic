/**
 * Copyright (c) 2025 Calmic Sdn Bhd. All rights reserved.
 */

import React, { createContext, useContext, useState, useCallback, useRef } from 'react';

const LoadingContext = createContext();

export const LoadingProvider = ({ children }) => {
  const [loadingOperations, setLoadingOperations] = useState([]);
  const nextIdRef = useRef(0);

  const startLoading = useCallback((message = 'Loading...') => {
    const id = nextIdRef.current++;
    setLoadingOperations(prev => [...prev, { id, message }]);
    
    // Return the ID so callers can stop the specific operation
    return id;
  }, []);

  const stopLoading = useCallback((operationId) => {
    setLoadingOperations(prev => {
      // If no ID provided, remove the most recent operation (LIFO)
      if (operationId === undefined) {
        return prev.slice(0, -1);
      }
      // Remove specific operation by ID
      return prev.filter(op => op.id !== operationId);
    });
  }, []);

  const isLoading = loadingOperations.length > 0;
  const loadingCount = loadingOperations.length;
  const currentMessage = loadingOperations[loadingOperations.length - 1]?.message || 'Loading...';

  return (
    <LoadingContext.Provider
      value={{
        isLoading,
        loadingCount,
        currentMessage,
        startLoading,
        stopLoading,
      }}
    >
      {children}
    </LoadingContext.Provider>
  );
};

export const useLoading = () => {
  const context = useContext(LoadingContext);
  if (!context) {
    throw new Error('useLoading must be used within a LoadingProvider');
  }
  return context;
};
