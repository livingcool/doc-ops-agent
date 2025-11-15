import { useState, useLayoutEffect, useEffect } from 'react';

// This function can be outside the component
const getInitialTheme = () => {
  return window.matchMedia('(prefers-color-scheme: dark)').matches;
};

export default function DarkModeToggle() {
  // Your app's CSS is dark by default, so 'isDark' should start true.
  const [isDark, setIsDark] = useState(true);

  // Effect for listening to OS-level theme changes
  useEffect(() => {
    const media = window.matchMedia('(prefers-color-scheme: dark)');
    
    // --- FIX: Removed the TypeScript ': MediaQueryListEvent' ---
    const handler = (e) => {
      setIsDark(e.matches);
    };

    media.addEventListener('change', handler);
    return () => media.removeEventListener('change', handler);
  }, []);

  // LayoutEffect for applying the class to the DOM
  useLayoutEffect(() => {
    // We will just toggle a class. Your index.css and App.css
    // are already dark-themed, so we'll just add 'light-mode'
    document.documentElement.classList.toggle('light-mode', !isDark);
  }, [isDark]);

  const toggle = () => {
    setIsDark(prevIsDark => !prevIsDark);
  };

  return (
    <button
      onClick={toggle}
      className="dark-toggle"
      aria-label="Toggle theme"
      title="Toggle theme"
    >
      {isDark ? '☀️' : '🌙'}
    </button>
  );
}