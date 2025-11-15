import React from 'react';

// NOTE: The 'export const' structure is required for named imports { StatusBadge }
export const StatusBadge = ({ status }) => { 
  const cfg = {
    connecting: { text: 'Connecting...', dot: 'connecting' },
    connected:  { text: 'Connected',   dot: 'connected' },
    error:      { text: 'Error',       dot: 'error' },
  };
  const { text, dot } = cfg[status] || cfg.connecting;

  return (
    <span className={`status-badge ${dot}`} aria-live="polite">
      <span className={`status-dot ${dot}`}></span>
      {text}
    </span>
  );
};