import React, { useState, useEffect } from 'react';
import { Sparkles, ShieldCheck, RefreshCw } from 'lucide-react';
import type { Insight } from '../types';
import { fetchInsights } from '../api';

export const InsightsScreen: React.FC = () => {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchInsights()
      .then(data => {
        setInsights(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 animate-in fade-in">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-bold text-slate-100">Grounded Insights</h1>
          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            Observed Patterns
          </span>
        </div>
        <p className="text-xs text-slate-400 mt-0.5">
          Real statistical patterns derived from your logged shifts and previous outcomes
        </p>
      </div>

      {/* Insights Cards */}
      {loading ? (
        <div className="py-12 text-center space-y-2">
          <RefreshCw className="w-7 h-7 text-emerald-500 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Computing grounded insights...</p>
        </div>
      ) : insights.length === 0 ? (
        <div className="text-center py-12 p-6 rounded-2xl bg-[#13171f] border border-slate-800 space-y-2">
          <Sparkles className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm font-medium text-slate-300">Keep logging for a little longer.</p>
          <p className="text-xs text-slate-500">Rahat will surface useful patterns as more shift outcomes are recorded.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {insights.map((ins) => (
            <div
              key={ins.id}
              className="p-5 rounded-2xl bg-[#13171f] border border-slate-800 hover:border-slate-700 transition-all space-y-3 flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold ${
                    ins.type === 'positive'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : ins.type === 'warning'
                      ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      : 'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                  }`}>
                    {ins.metric}
                  </span>
                  <Sparkles className="w-4 h-4 text-slate-500" />
                </div>

                <h3 className="text-sm font-bold text-slate-100">{ins.title}</h3>
                <p className="text-xs text-slate-300 leading-relaxed">
                  {ins.description}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-800/80 flex items-center gap-1.5 text-[11px] text-slate-500">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                <span>Computed from SQLite records & Hindsight memory</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
