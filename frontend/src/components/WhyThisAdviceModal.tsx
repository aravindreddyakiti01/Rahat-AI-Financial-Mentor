import React from 'react';
import { X, CheckCircle2, History, Database, Sparkles, Brain } from 'lucide-react';
import type { StructuredAgentResponse } from '../types';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  response?: StructuredAgentResponse;
}

export const WhyThisAdviceModal: React.FC<Props> = ({ isOpen, onClose, response }) => {
  if (!isOpen || !response) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-lg bg-[#13171f] border border-slate-700/60 rounded-2xl shadow-2xl p-6 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <Brain className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-semibold text-slate-100">Why Rahat Gave This Advice</h3>
              <p className="text-xs text-slate-400">Grounded in your actual records and experiential outcomes</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Evidence List */}
        <div className="mt-4 space-y-4 max-h-[60vh] overflow-y-auto pr-1">
          {/* Factual SQLite Records */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-emerald-400">
              <Database className="w-3.5 h-3.5" />
              <span>Current Financial Facts (SQLite)</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {response.facts.map((fact, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                  <span>{fact}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Hindsight Experiential Memory */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold uppercase tracking-wider text-sky-400">
              <History className="w-3.5 h-3.5" />
              <span>Experiential Memory & Outcomes (Hindsight)</span>
            </div>
            <ul className="space-y-1.5 text-xs text-slate-300">
              {response.why_this_advice.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* How This Changed The Recommendation */}
          {response.pattern && (
            <div className="p-3.5 rounded-xl bg-emerald-950/30 border border-emerald-500/20">
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
                Outcome-Aware Adaptation
              </h4>
              <p className="text-xs text-slate-300 leading-relaxed">
                {response.pattern}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-5 pt-3 border-t border-slate-800 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
