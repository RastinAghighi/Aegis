import { useEffect, useRef, useState } from 'react';
import { NavLink, Route, Routes } from 'react-router-dom';

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

export default function App() {
  const { waking } = useColdStartProbe();

  return (
    <div className="flex min-h-screen flex-col bg-slate-950 text-slate-50">
      {waking && <ColdStartOverlay />}

      <header className="sticky top-0 z-40 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="container flex h-16 items-center justify-between">
          <div className="flex items-baseline gap-3">
            <span className="text-xl font-bold uppercase tracking-[0.35em] text-slate-50">
              Aegis
            </span>
            <span className="hidden text-xs uppercase tracking-widest text-slate-400 sm:inline">
              HIPAA Technical Safeguards
            </span>
          </div>
          <nav className="flex items-center gap-1 text-sm sm:gap-2">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  cn(
                    'rounded-md px-3 py-1.5 transition-colors',
                    isActive
                      ? 'bg-slate-800 text-slate-50'
                      : 'text-slate-400 hover:bg-slate-900 hover:text-slate-100',
                  )
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="container flex-1 py-8">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/flow-graph" element={<FlowGraph />} />
          <Route path="/rules" element={<Rules />} />
        </Routes>
      </main>

      <footer className="border-t border-slate-800 bg-slate-950">
        <div className="container flex h-14 items-center justify-center text-xs text-slate-500 sm:justify-between">
          <span>
            Aegis &middot; Powered by IBM Bob &middot;{' '}
            <a
              href="https://github.com/RastinAghighi/Aegis"
              target="_blank"
              rel="noreferrer noopener"
              className="text-slate-400 underline-offset-4 hover:text-slate-200 hover:underline"
            >
              github.com/RastinAghighi/Aegis
            </a>
          </span>
          <span className="hidden text-slate-600 sm:inline">
            HIPAA Technical Safeguards · 45 CFR § 164.312
          </span>
        </div>
      </footer>
    </div>
  );
}
