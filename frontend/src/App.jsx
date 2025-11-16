// src/App.jsx
import { useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// --- FIX: Changed import from .tsx to .jsx ---
import DarkModeToggle from './components/DarkModeToggle.jsx';
import { useEventSource } from './hooks/useEventSource.jsx';
import { StatusBadge } from './components/StatusBadge.jsx';
import { LogCard } from './components/LogCard.jsx';
import { LogIcon } from './components/LogIcon.jsx';

import './App.css'; // Your component styles

const BACKEND_STREAM_URL = "http://localhost:8000/api/stream/logs";

export default function App() {
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
        <h1>DocSmith</h1>
        <div className="header-controls">
          <StatusBadge status={status} />
          <DarkModeToggle />
        </div>
      </header>

      <main className="log-feed-container" aria-live="polite">
        {errorMessage}
        <AnimatePresence>
          {logs.map(log => (
            <LogCard key={log.timestamp} log={log} />
          ))}
        </AnimatePresence>
      </main>
    </div>
  );
}