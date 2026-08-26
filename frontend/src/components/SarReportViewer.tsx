import React, { useState } from 'react';
import { FileText, Copy, Check, Download, AlertTriangle } from 'lucide-react';

interface SarReportViewerProps {
  reportText?: string;
  sarJson?: Record<string, any>;
  caseId: string;
}

export const SarReportViewer: React.FC<SarReportViewerProps> = ({ reportText, sarJson, caseId }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (reportText) {
      navigator.clipboard.writeText(reportText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (reportText) {
      const element = document.createElement('a');
      const file = new Blob([reportText], { type: 'text/markdown' });
      element.href = URL.createObjectURL(file);
      element.download = `SAR_${caseId}_DRAFT.md`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
    }
  };

  if (!reportText) {
    return (
      <div className="p-8 text-center text-slate-500 border border-dashed border-slate-800 rounded-xl">
        No SAR draft generated for this case.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Compliance Disclaimer Banner */}
      <div className="p-3.5 bg-amber-950/40 border border-amber-500/40 rounded-xl flex items-start gap-3 text-amber-200 text-xs">
        <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
        <div>
          <span className="font-semibold text-amber-300">REGULATORY COMPLIANCE DRAFT: </span>
          This narrative is generated automatically by SentinelGraph's Report Drafting Agent. Statutory SAR/STR filings require formal authorization and sign-off by a designated AML Compliance Officer.
        </div>
      </div>

      {/* Report Actions Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-indigo-400" />
          <h4 className="text-sm font-semibold text-slate-200">FinCEN / FIU Standard Narrative Report</h4>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopy}
            className="px-3 py-1.5 rounded-lg bg-surface border border-slate-700 hover:border-slate-600 text-slate-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
            {copied ? 'Copied' : 'Copy Narrative'}
          </button>
          <button
            onClick={handleDownload}
            className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Download className="h-3.5 w-3.5" />
            Download SAR (.md)
          </button>
        </div>
      </div>

      {/* Rendered Document Box */}
      <div className="p-6 bg-surface rounded-xl border border-slate-800 text-slate-200 font-mono text-xs leading-relaxed overflow-x-auto whitespace-pre-wrap">
        {reportText}
      </div>
    </div>
  );
};
