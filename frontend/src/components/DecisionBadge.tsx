import React from 'react';
import { DecisionPolicy } from '../types';
import { CheckCircle2, AlertTriangle, ShieldAlert } from 'lucide-react';

interface DecisionBadgeProps {
  decision: DecisionPolicy | string;
  size?: 'sm' | 'md' | 'lg';
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({ decision, size = 'md' }) => {
  const normalized = (decision || 'ALLOW').toUpperCase();

  const config = {
    ALLOW: {
      style: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
      icon: CheckCircle2,
      label: 'ALLOW',
    },
    REVIEW: {
      style: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
      icon: AlertTriangle,
      label: 'MANUAL REVIEW',
    },
    BLOCK: {
      style: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
      icon: ShieldAlert,
      label: 'BLOCK / FREEZE',
    },
  }[normalized] || {
    style: 'bg-slate-800 text-slate-300 border-slate-700',
    icon: CheckCircle2,
    label: normalized,
  };

  const Icon = config.icon;

  const sizeClasses = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-3 py-1',
    lg: 'text-sm px-4 py-2 font-semibold',
  }[size];

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-lg border font-semibold tracking-wider ${config.style} ${sizeClasses}`}>
      <Icon className="h-4 w-4 shrink-0" />
      {config.label}
    </span>
  );
};
