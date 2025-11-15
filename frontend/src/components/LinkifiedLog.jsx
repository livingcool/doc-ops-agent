import React from 'react';

export const LinkifiedLog = ({ log }) => {
  if (log.type !== 'log-action') return <>{log.data}</>;

  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const match = log.data.match(urlRegex);
  if (!match) return <>{log.data}</>;

  const url = match[0];
  const parts = log.data.split(url);

  return (
    <>
      {parts[0]}
      <a href={url} target="_blank" rel="noopener noreferrer">{url}</a>
      {parts[1]}
    </>
  );
};