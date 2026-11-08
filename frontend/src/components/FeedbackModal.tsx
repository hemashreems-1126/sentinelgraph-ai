import React, { useState } from 'react';
import { X, Send, UserX } from 'lucide-react';
import { apiClient } from '../api/client';

interface FeedbackModalProps {
  caseId: string;
  /** The system's recommendation: FILE_STR or NO_FILE. */
  filingDecision?: string | null;
  isOpen: boolean;
  onClose: () => void;
  onSubmitted: () => void;
}

type Choice = 'REVERSE' | 'FACT_ERROR';

/** The analyst disagrees with the recommendation. Every choice is written to the hash-chained audit trail. */
export const FeedbackModal: React.FC<FeedbackModalProps> = ({ caseId, filingDecision, isOpen, onClose, onSubmitted }) => {
  const [choice, setChoice] = useState<Choice>('REVERSE');
  const [notes, setNotes] = useState('');
  const [name, setName] = useState('analyst');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const isStr = filingDecision === 'FILE_STR';
  const reverseLabel = isStr ? 'This should NOT be filed' : 'This SHOULD be filed as an STR';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!notes.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await apiClient.submitFeedback(caseId, {
        feedback_type: choice === 'REVERSE' ? 'OVERRIDE' : 'DISAGREE',
        adjusted_decision: choice === 'REVERSE' ? (isStr ? 'NO_FILE' : 'FILE_STR') : undefined,
        notes,
        investigator_id: name,
      });
      onSubmitted();
      onClose();
    } catch (err) {
      // Never pretend a sign-off succeeded — show the server's reason.
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  };

  const option = (value: Choice, title: string, hint: string) => (
    <label className={`flex gap-3 p-3 rounded-xl border cursor-pointer ${choice === value ? 'border-indigo-500 bg-indigo-950/40' : 'border-slate-800 hover:border-slate-600'}`}>
      <input type="radio" name="choice" checked={choice === value} onChange={() => setChoice(value)} className="mt-1" />
      <span>
        <span className="block text-sm font-semibold text-slate-100">{title}</span>
        <span className="block text-xs text-slate-400">{hint}</span>
      </span>
    </label>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
      <div className="bg-surface border border-slate-700 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-amber-950/80 text-amber-300 border border-amber-500/30">
              <UserX className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">Disagree with the recommendation</h3>
              <p className="text-xs text-slate-400">Your reason is saved permanently in the audit trail.</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200" aria-label="Close">
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 rounded-lg border border-rose-500/50 bg-rose-950/40 text-rose-200 text-xs">
              <span className="font-semibold">Not saved. </span>{error}
            </div>
          )}

          <div className="space-y-2">
            {option('REVERSE', reverseLabel, 'Changes the case outcome to your decision.')}
            {option('FACT_ERROR', 'A fact in the report is wrong or missing', 'Keeps the outcome open and records what needs fixing.')}
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Why?</label>
            <textarea
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. The customer is a registered merchant; these are normal shop payments."
              className="w-full px-3 py-2 bg-background border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Your name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-background border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
              required
            />
          </div>

          <div className="flex items-center justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 rounded-lg bg-surface border border-slate-700 text-slate-300 text-xs font-medium">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !notes.trim()}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold flex items-center gap-1.5"
            >
              <Send className="h-3.5 w-3.5" />
              {submitting ? 'Saving…' : 'Save my decision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
