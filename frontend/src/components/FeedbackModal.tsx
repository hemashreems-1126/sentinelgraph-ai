import React, { useState } from 'react';
import { X, Send, UserCheck, ShieldAlert } from 'lucide-react';
import { apiClient } from '../api/client';
import { DecisionPolicy } from '../types';

interface FeedbackModalProps {
  caseId: string;
  currentDecision: DecisionPolicy;
  isOpen: boolean;
  onClose: () => void;
  onSubmitted: () => void;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({
  caseId,
  currentDecision,
  isOpen,
  onClose,
  onSubmitted
}) => {
  const [feedbackType, setFeedbackType] = useState('AGREE');
  const [adjustedDecision, setAdjustedDecision] = useState<string>(currentDecision);
  const [notes, setNotes] = useState('');
  const [investigatorId, setInvestigatorId] = useState('analyst_lead');
  const [submitting, setSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) return;

    setSubmitting(true);
    try {
      await apiClient.submitFeedback(caseId, {
        feedback_type: feedbackType,
        notes,
        adjusted_decision: feedbackType === 'OVERRIDE' ? adjustedDecision : undefined,
        investigator_id: investigatorId
      });
      onSubmitted();
      onClose();
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-surface border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-950/80 text-indigo-400 border border-indigo-500/30">
              <UserCheck className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Investigator Decision & Feedback</h3>
              <p className="text-xs text-slate-400 font-mono">Case: {caseId}</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              Investigator ID / Compliance Officer
            </label>
            <input
              type="text"
              value={investigatorId}
              onChange={(e) => setInvestigatorId(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              Feedback Classification
            </label>
            <select
              value={feedbackType}
              onChange={(e) => setFeedbackType(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
            >
              <option value="AGREE">Agree with Automated Risk Assessment</option>
              <option value="OVERRIDE">Override Decision (Human Compliance Sign-Off)</option>
              <option value="FALSE_POSITIVE">Flag as False Positive (Tuning Feedback)</option>
              <option value="POLICY_ADJUSTMENT">Recommend Rule Threshold Adjustment</option>
            </select>
          </div>

          {feedbackType === 'OVERRIDE' && (
            <div className="p-3 bg-amber-950/30 border border-amber-500/40 rounded-xl space-y-2">
              <label className="block text-xs font-semibold text-amber-300">
                Select Overridden Decision:
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['ALLOW', 'REVIEW', 'BLOCK'] as DecisionPolicy[]).map((d) => (
                  <button
                    key={d}
                    type="button"
                    onClick={() => setAdjustedDecision(d)}
                    className={`py-2 px-3 rounded-lg border text-xs font-semibold tracking-wider transition-all ${
                      adjustedDecision === d
                        ? 'bg-indigo-600 text-white border-indigo-400'
                        : 'bg-surface border-slate-700 text-slate-300 hover:border-slate-500'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-mono uppercase tracking-wider text-slate-400 mb-1.5">
              Forensic Rationale & Audit Justification
            </label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Detail reasons for decision confirmation or override for permanent audit trail..."
              className="w-full px-3 py-2 bg-background border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-surface border border-slate-700 hover:bg-surface-light text-slate-300 text-xs font-medium"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !notes.trim()}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors"
            >
              <Send className="h-3.5 w-3.5" />
              {submitting ? 'Recording...' : 'Submit to Audit Trail'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
