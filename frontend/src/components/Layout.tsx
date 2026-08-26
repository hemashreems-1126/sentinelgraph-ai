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
  ExternalLink
} from 'lucide-react';
import { apiClient } from '../api/client';

export const Layout: React.FC = () => {
  const [health, setHealth] = useState<{ status: string; llm_mode: string; groq_model: string } | null>(null);

  useEffect(() => {
    apiClient.getHealth().then(setHealth).catch(() => setHealth({ status: 'offline', llm_mode: 'unknown', groq_model: 'unknown' }));
  }, []);

  const navItems = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/alerts', label: 'Alerts Queue', icon: BellRing },
    { to: '/investigations', label: 'Investigations', icon: FolderSearch },
    { to: '/audit', label: 'Audit Trail', icon: ShieldCheck },
    { to: '/evaluation', label: 'Model Evaluation', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-background text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-slate-800 bg-surface/90 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3.5">
          <div className="h-9 w-9 rounded-xl bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <ShieldAlert className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-extrabold tracking-tight text-white font-mono">SentinelGraph</span>
              <span className="text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-950 text-indigo-400 border border-indigo-500/30">
                AI Risk Manager
              </span>
            </div>
            <p className="text-[11px] text-slate-400">Razorpay AI Buildathon 2026</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Health / LLM Status Badge */}
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-xs font-mono">
            <span className={`h-2 w-2 rounded-full ${health?.status === 'healthy' ? 'bg-emerald-400 animate-ping' : 'bg-amber-400'}`} />
            <span className="text-slate-300">
              Engine: <strong className="text-indigo-400">{health?.llm_mode === 'live_groq' ? 'Live Groq (LLaMA-3.3)' : 'Deterministic Mock'}</strong>
            </span>
          </div>

          <a
            href="https://razorpay.com/buildathon/"
            target="_blank"
            rel="noreferrer"
            className="hidden md:flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 transition-colors"
          >
            <span>Razorpay Track</span>
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        </div>
      </header>

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
              <span>Multi-Agent Stack</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              11-Stage LangGraph architecture with deterministic Python risk scoring & FinCEN SAR drafting.
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
