import React from 'react';
import { motion } from 'framer-motion';
import { LogIcon } from './LogIcon';
import { LinkifiedLog } from './LinkifiedLog';

export const LogCard = ({ log }) => (
  <motion.div
    className={`log-card ${log.type}`}
    layout
    initial={{ opacity: 0, y: -20, scale: 0.9 }}
    animate={{ opacity: 1, y: 0, scale: 1 }}
    exit={{ opacity: 0, scale: 0.8 }}
    transition={{ duration: 0.3, ease: 'easeOut' }}
    role="log"
  >
    <LogIcon type={log.type} />
    <div className="log-message">
      <LinkifiedLog log={log} />
    </div>
  </motion.div>
);