import React from 'react';
import { RiskBand } from '../types';

interface RiskBadgeProps {
  band: RiskBand | string;
  score?: number;
  size?: 'sm' | 'md' | 'lg';
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ band, score, size = 'md' }) => {
  const normalized = (band || 'LOW').toUpperCase();

  const styles = {
    LOW: 'bg-emerald-950/70 text-emerald-400 border-emerald-500/30',
    MEDIUM: 'bg-amber-950/70 text-amber-400 border-amber-500/30',
    HIGH: 'bg-orange-950/70 text-orange-400 border-orange-500/30',
    CRITICAL: 'bg-rose-950/70 text-rose-400 border-rose-500/30 animate-pulse',
  }[normalized] || 'bg-slate-800 text-slate-300 border-slate-700';

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1',
    lg: 'text-sm px-3.5 py-1.5 font-semibold',
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-mono ${styles} ${sizeClasses}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {normalized}
      {score !== undefined && <span className="opacity-75 font-sans">({score.toFixed(1)})</span>}
    </span>
  );
};
