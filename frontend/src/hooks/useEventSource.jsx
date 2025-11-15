import { useState, useEffect, useCallback } from 'react';

export function useEventSource(url) {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('connecting'); // connecting | connected | error

  const addLog = useCallback((type, data) => {
    setLogs(prev => [{ type, data, timestamp: Date.now() }, ...prev]);
  }, []);

  useEffect(() => {
    const eventSource = new EventSource(url);

    const handleOpen = () => {
      setStatus('connected');
      addLog('log-step', 'Connected to agent live feed...');
    };

    const handleError = (err) => {
      console.error('EventSource failed:', err);
      setStatus('error');
      eventSource.close();
      addLog('log-error', 'Connection lost. Is the backend running?');
    };

    const events = ['log-trigger', 'log-step', 'log-skip', 'log-action', 'log-error'];
    events.forEach(ev =>
      eventSource.addEventListener(ev, e => addLog(ev, e.data))
    );

    eventSource.onopen = handleOpen;
    eventSource.onerror = handleError;

    return () => eventSource.close();
  }, [url, addLog]);

  return { logs, status };
}