import React, { useEffect, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  BellRing,
  FolderSearch,
  ShieldCheck,
  BarChart3,
  Cpu,
  ShieldAlert,
  Radio,
  ExternalLink,
  SlidersHorizontal
} from 'lucide-react';
import { apiClient, isOffline, subscribeOffline, isWaking, subscribeWaking } from '../api/client';

export const Layout: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; llm_mode: string; groq_model: string } | null>(null);
  const [offline, setOffline] = useState(isOffline());
  const [waking, setWaking] = useState(isWaking());

  useEffect(() => {
    const unsubscribeWake = subscribeWaking(setWaking);
    const unsubscribe = subscribeOffline(setOffline);
    apiClient.getHealth().then(setHealth).catch(() => setHealth({ status: 'error', llm_mode: 'unknown', groq_model: 'unknown' }));
    return () => { unsubscribe(); unsubscribeWake(); };
  }, []);

  const engineLabel = offline
    ? 'Offline snapshot'
    : !health
      ? 'Connecting…'
      : health.llm_mode === 'live_groq'
        ? 'AI wording: Groq LLaMA-3.3'
        : 'AI wording: templates (no LLM key)';

  const navItems = [
    { to: '/', label: 'Overview', icon: LayoutDashboard },
    { to: '/investigations', label: 'Cases', icon: FolderSearch },
    { to: '/alerts', label: 'Alerts', icon: BellRing },
    { to: '/audit', label: 'Audit trail', icon: ShieldCheck },
    { to: '/evaluation', label: 'Evaluation', icon: BarChart3 },
    { to: '/admin', label: 'Demo controls', icon: SlidersHorizontal },
  ];

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-slate-800 bg-surface/90 backdrop-blur-md px-4 md:px-6 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3.5">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold tracking-tight text-white font-mono">SentinelGraph</span>
              <span className="hidden sm:inline text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-500/30">
                AML Investigation
              </span>
            </div>
            <p className="hidden sm:block text-[11px] text-slate-400">Fact-checked investigations for Indian compliance teams</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Health / LLM Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
            <span className="sm:hidden sr-only">{engineLabel}</span>
            <span className={`h-2 w-2 rounded-full ${!offline && health?.status === 'healthy' ? 'bg-emerald-400' : 'bg-amber-400'}`} />
            <span className="hidden sm:inline text-slate-300">
              <strong className="text-indigo-400">{engineLabel}</strong>
            </span>
          </div>

          <a
            href="https://github.com/hemashreems-1126/sentinelgraph-ai"
            target="_blank"
            rel="noreferrer"
            className="hidden md:flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 transition-colors"
          >
            <span>Source code</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </header>

      {offline && (
        <div className="px-6 py-2 bg-amber-950/70 border-b border-amber-600/40 text-amber-200 text-xs">
          <strong>Offline mode:</strong> the SentinelGraph server cannot be reached, so you are viewing a read-only
          snapshot exported from a real run. Actions (investigate, sign-off, evaluation) are disabled until it is back.
        </div>
      )}
      {(waking || (!health && !offline)) && (
        <div className="px-6 py-2 bg-indigo-950/60 border-b border-indigo-700/40 text-indigo-200 text-xs flex items-center gap-2">
          <span className="h-3 w-3 rounded-full border-2 border-indigo-300 border-t-transparent animate-spin" />
          Waking up the server… free hosting sleeps when idle and can take up to a minute. Live data will appear automatically.
        </div>
      )}

      {/* Mobile navigation */}
      <nav className="md:hidden flex gap-1 overflow-x-auto px-3 py-2 border-b border-slate-800 bg-surface/70">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `whitespace-nowrap px-3 py-1.5 rounded-lg text-xs font-semibold ${isActive ? 'bg-indigo-600/20 text-indigo-300' : 'text-slate-400'}`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* App Body with Sidebar */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar Navigation */}
        <aside className="w-60 border-r border-slate-800 bg-surface/50 p-4 space-y-6 hidden md:block">
          <div>
            <p className="text-[10px] font-mono uppercase tracking-widest text-slate-500 mb-2 px-3">Investigation Ops</p>
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                return (
                  <NavLink
                    key={item.to}
                    to={item.to}
                    end={item.to === '/'}
                    className={({ isActive }) =>
                      `flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/30'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                      }`
                    }
                  >
                    <Icon className="h-4 w-4 shrink-0" />
                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-300">
              <Cpu className="h-4 w-4 text-indigo-400" />
              <span>How it works</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              AI agents investigate each alert. Plain code then checks every fact against the transactions and recommends whether to file an STR. You make the final call.
            </p>
          </div>
        </aside>

        {/* Main Content Area */}
        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
