import { useState, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './App.css';

// Backend URL
const BACKEND_STREAM_URL = "http://localhost:8000/api/stream/logs";

// === Custom Hook: useEventSource ===
function useEventSource(url) {
  const [logs, setLogs] = useState([]);
  const [status, setStatus] = useState('connecting'); // 'connecting' | 'connected' | 'error'

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

    // Event listeners
    const events = ['log-trigger', 'log-step', 'log-skip', 'log-action', 'log-error'];
    events.forEach(event => {
      eventSource.addEventListener(event, (e) => addLog(event, e.data));
    });

    eventSource.onopen = handleOpen;
    eventSource.onerror = handleError;

    return () => {
      eventSource.close();
    };
  }, [url, addLog]);

  return { logs, status };
}

// === Icon Component (with Emojis) ===
const LogIcon = ({ type }) => {
  const icons = {
    'log-trigger': '🚀',
    'log-step': '⚙️',
    'log-skip': '⏭️',
    'log-action': '✅',
    'log-error': '🔥',
  };

  const icon = icons[type] || '💬';
  return <span className="log-card-icon" aria-hidden="true">{icon}</span>;
};

// === Status Badge Component ===
const StatusBadge = ({ status }) => {
  const config = {
    connecting: { text: 'Connecting...', dot: 'connecting' },
    connected: { text: 'Connected', dot: 'connected' },
    error: { text: 'Error', dot: 'error' },
  };

  const { text, dot } = config[status] || config.connecting;

  return (
    <span className={`status-badge ${dot}`} aria-live="polite">
      <span className={`status-dot ${dot}`}></span>
      {text}
    </span>
  );
};

// === NEW: Link-Parsing Component ===
// This finds and links the URL in the "log-action" message
const LinkifiedLog = ({ log }) => {
  if (log.type !== 'log-action') {
    return <>{log.data}</>;
  }

  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const match = log.data.match(urlRegex);

  if (!match) {
    return <>{log.data}</>;
  }

  const url = match[0];
  const parts = log.data.split(url);

  return (
    <>
      {parts[0]}
      <a href={url} target="_blank" rel="noopener noreferrer">
        {url}
      </a>
      {parts[1]}
    </>
  );
};


// === Log Card Component (Now Animated) ===
const LogCard = ({ log }) => {
  return (
    <motion.div
      className={`log-card ${log.type}`}
      role="log"
      aria-label={`${log.type.replace('log-', '')} log`}
      // Animation props from framer-motion
      layout
      initial={{ opacity: 0, y: -20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.8 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
    >
      <LogIcon type={log.type} />
      <div className="log-message">
        <LinkifiedLog log={log} />
      </div>
    </motion.div>
  );
};

// === Main App Component ===
function App() {
  const { logs, status } = useEventSource(BACKEND_STREAM_URL);

  const errorMessage = useMemo(() => {
    if (status !== 'error') return null;
    return (
      <motion.div
        className="log-card log-error"
        role="alert"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <LogIcon type="log-error" />
        <div className="log-message">
          Could not connect to backend at <code>{BACKEND_STREAM_URL}</code>.
          Is the FastAPI server running on port 8000?
        </div>
      </motion.div>
    );
  }, [status]);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Autonomous Doc-Ops Agent</h1>
        <StatusBadge status={status} />
      </header>

      <main className="log-feed-container" aria-live="polite" aria-atomic="false">
        {errorMessage}
        <AnimatePresence>
          {logs.map((log) => (
            <LogCard key={log.timestamp} log={log} />
          ))}
        </AnimatePresence>
      </main>
    </div>
  );
}

export default App;