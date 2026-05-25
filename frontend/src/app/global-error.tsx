'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
     
    console.error('Global error boundary caught:', error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          fontFamily: 'ui-sans-serif, system-ui',
          background: '#efece4',
          color: '#1a1814',
          minHeight: '100vh',
          margin: 0,
          padding: '48px',
        }}
      >
        <p style={{ textTransform: 'uppercase', letterSpacing: '0.18em', fontSize: 12 }}>
          Fatal error
        </p>
        <h1 style={{ fontFamily: 'ui-serif, Georgia, serif', fontSize: 56, marginTop: 12 }}>
          Something went very sideways.
        </h1>
        <p style={{ maxWidth: 540, marginTop: 12 }}>
          The application could not render at all. Reloading may help.
        </p>
        <button
          type="button"
          onClick={reset}
          style={{
            marginTop: 32,
            background: '#1a1814',
            color: '#efece4',
            border: 0,
            borderRadius: 999,
            padding: '12px 24px',
            cursor: 'pointer',
          }}
        >
          Try again
        </button>
      </body>
    </html>
  );
}
