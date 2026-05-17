import { useEffect, useRef, useState } from 'react';
import { NavLink, Route, Routes, useLocation } from 'react-router-dom';

import Overview from './pages/Overview';
import Findings from './pages/Findings';
import FlowGraph from './pages/FlowGraph';
import Rules from './pages/Rules';
import ColdStartOverlay from './components/ColdStartOverlay';
import { cn } from './lib/utils';
import { getHealth } from './lib/api';

const nav = [
  { to: '/', label: 'Overview', end: true },
  { to: '/findings', label: 'Findings' },
  { to: '/flow-graph', label: 'Flow Graph' },
  { to: '/rules', label: 'Rules' },
];

function useColdStartProbe() {
  const [waking, setWaking] = useState(false);
  const [ready, setReady] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      if (!cancelled && !ready) setWaking(true);
    }, 3000);

    const probe = async () => {
      try {
        await getHealth(controller.signal);
        if (cancelled) return;
        setReady(true);
        setWaking(false);
        if (pollRef.current !== null) {
          window.clearInterval(pollRef.current);
          pollRef.current = null;
        }
      } catch {
        if (cancelled) return;
        setWaking(true);
        if (pollRef.current === null) {
          pollRef.current = window.setInterval(probe, 5000);
        }
      }
    };

    probe();

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeout);
      if (pollRef.current !== null) window.clearInterval(pollRef.current);
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { waking: waking && !ready, ready };
}

function PageFade({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  return (
    <div key={location.pathname} className="animate-fade-only">
      {children}
    </div>
  );
}

export default function App() {
  const { waking } = useColdStartProbe();

  return (
    <div className="flex min-h-screen flex-col text-ink-primary">
      {waking && <ColdStartOverlay />}

      <header className="sticky top-0 z-40 border-b border-white/5 bg-slate-950/60 backdrop-blur-xl">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-baseline gap-4">
            <span className="text-sm font-medium uppercase tracking-[0.32em] text-ink-primary">
              Aegis
            </span>
            <span className="hidden text-[0.625rem] uppercase tracking-[0.2em] text-ink-tertiary sm:inline">
              Compliance auditor
            </span>
          </div>
          <nav className="flex items-center gap-6 text-[0.8125rem] sm:gap-8">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  cn(
                    'group relative py-1 transition-colors duration-200',
                    isActive
                      ? 'text-ink-primary'
                      : 'text-ink-secondary hover:text-ink-primary',
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <span>{n.label}</span>
                    <span
                      className={cn(
                        'absolute -bottom-[1px] left-0 h-px w-full origin-left bg-gradient-to-r from-ink-primary/80 via-ink-primary/50 to-transparent transition-transform duration-300 ease-smooth',
                        isActive
                          ? 'scale-x-100'
                          : 'scale-x-0 group-hover:scale-x-100',
                      )}
                    />
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="container flex-1 py-12">
        <PageFade>
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/findings" element={<Findings />} />
            <Route path="/flow-graph" element={<FlowGraph />} />
            <Route path="/rules" element={<Rules />} />
          </Routes>
        </PageFade>
      </main>

      <footer className="border-t border-white/5">
        <div className="container flex h-12 items-center justify-center text-[0.6875rem] text-ink-tertiary sm:justify-between">
          <span className="tracking-wide">
            Aegis ·{' '}
            <a
              href="https://github.com/RastinAghighi/Aegis"
              target="_blank"
              rel="noreferrer noopener"
              className="text-ink-secondary underline-offset-4 transition-colors hover:text-ink-primary hover:underline"
            >
              github.com/RastinAghighi/Aegis
            </a>
          </span>
          <span className="hidden uppercase tracking-[0.18em] text-ink-tertiary/70 sm:inline">
            45 CFR § 164.312
          </span>
        </div>
      </footer>
    </div>
  );
}
