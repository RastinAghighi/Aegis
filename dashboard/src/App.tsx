import { NavLink, Route, Routes } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';

import Overview from './pages/Overview';
import Findings from './pages/Findings';
import Reports from './pages/Reports';

const nav = [
  { to: '/', label: 'Overview', end: true },
  { to: '/findings', label: 'Findings' },
  { to: '/reports', label: 'Reports' },
];

export default function App() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-6 w-6 text-primary" />
            <span className="font-semibold tracking-tight">Aegis</span>
            <span className="ml-2 text-xs text-muted-foreground">HIPAA Compliance Auditor</span>
          </div>
          <nav className="flex items-center gap-6 text-sm">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) =>
                  isActive
                    ? 'font-medium text-foreground'
                    : 'text-muted-foreground hover:text-foreground'
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main className="container py-8">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/findings" element={<Findings />} />
          <Route path="/reports" element={<Reports />} />
        </Routes>
      </main>
    </div>
  );
}
