import React, { useState } from 'react';
import { AgentStep } from '../types';
import {
  Bot,
  BrainCircuit,
  FileSearch,
  Network,
  Activity,
  FileText,
  Globe2,
  FolderArchive,
  Calculator,
  ShieldCheck,
  FileSpreadsheet,
  ChevronDown,
  ChevronUp,
  Clock
} from 'lucide-react';

interface AgentTrailCardProps {
  step: AgentStep;
  stepIndex: number;
}

export const AgentTrailCard: React.FC<AgentTrailCardProps> = ({ step, stepIndex }) => {
  const [expanded, setExpanded] = useState(false);

  const getAgentIcon = (name: string) => {
    if (name.includes('Supervisor')) return Bot;
    if (name.includes('Planner')) return BrainCircuit;
    if (name.includes('Hypothesis')) return BrainCircuit;
    if (name.includes('Evidence')) return FileSearch;
    if (name.includes('Graph')) return Network;
    if (name.includes('Behavior')) return Activity;
    if (name.includes('Document')) return FileText;
    if (name.includes('Intelligence')) return Globe2;
    if (name.includes('Assembly')) return FolderArchive;
    if (name.includes('Reasoning')) return BrainCircuit;
    if (name.includes('RiskAssignment')) return Calculator;
    if (name.includes('Auditing')) return ShieldCheck;
    if (name.includes('ReportSAR')) return FileSpreadsheet;
    return Bot;
  };

  const Icon = getAgentIcon(step.agent_name);

  return (
    <div className="border border-slate-800 bg-surface rounded-xl overflow-hidden hover:border-slate-700 transition-all duration-200 shadow-sm">
      <div
        onClick={() => setExpanded(!expanded)}
        className="p-4 flex items-center justify-between cursor-pointer hover:bg-surface-light/40 transition-colors"
      >
        <div className="flex items-center gap-3.5">
          <div className="h-9 w-9 rounded-lg bg-indigo-950/60 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
            <Icon className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-medium text-slate-400">#{stepIndex + 1}</span>
              <h4 className="text-sm font-semibold text-slate-100">{step.agent_name}</h4>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700/60">
                {step.action}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl">{step.summary}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-400">
            <Clock className="h-3.5 w-3.5" />
            <span>{step.duration_ms}ms</span>
          </div>
          <button className="text-slate-400 hover:text-slate-200">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="p-4 bg-background/80 border-t border-slate-800/80 font-mono text-xs text-slate-300">
          <div className="mb-2 flex items-center justify-between text-slate-400">
            <span>Execution Timestamp: {step.timestamp}</span>
            <span>Status: <strong className="text-emerald-400">{step.status}</strong></span>
          </div>
          <pre className="p-3 bg-surface rounded-lg border border-slate-800 overflow-x-auto text-[11px] text-indigo-300 leading-relaxed">
            {JSON.stringify(step.details, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};
