import React from 'react';

export const LogIcon = ({ type }) => {
  const icons = {
    'log-trigger': '🚀',
    'log-step': '⚙️',
    'log-skip': '⏭️',
    'log-action': '✅',
    'log-error': '🔥',
  };
  return (
    <span className="log-card-icon" aria-hidden="true">
      {icons[type] || '💬'}
    </span>
  );
};