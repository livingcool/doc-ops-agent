import { useEffect, useState } from 'react';

// Read initial theme from OS (sync, no flash)
const getInitialTheme = (): boolean =>
  typeof window !== 'undefined' &&
  window.matchMedia('(prefers-color-scheme: dark)').matches;

export default function DarkModeToggle() {
  const [isDark, setIsDark] = useState(getInitialTheme);

  // Sync with OS theme changes
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => setIsDark(e.matches);

    media.addEventListener('change', handler);
    return () => media.removeEventListener('change', handler);
  }, []);

  // Apply theme instantly (no flash)
  useEffect(() => {
    document.documentElement.classList.toggle('dark-mode', isDark);
  }, [isDark]);

  const toggle = () => setIsDark(prev => !prev);

  return (
    <button
      onClick={toggle}
      className="dark-toggle"
      aria-label="Toggle dark mode"
      title="Toggle dark mode"
      aria-pressed={isDark}
    >
      {isDark ? 'Sun' : 'Moon'}
    </button>
  );
}