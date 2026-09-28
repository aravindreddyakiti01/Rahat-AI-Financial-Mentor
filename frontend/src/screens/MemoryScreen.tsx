import React, { useState, useEffect } from 'react';
import { History, Brain, Target, CheckCircle, AlertTriangle, Sparkles, Search, Trash2, Calendar, RefreshCw } from 'lucide-react';
import type { MemoryItem } from '../types';
import { fetchMemoryTimeline, deleteMemory } from '../api';

interface Props {
  onRefreshTrigger?: () => void;
}

export const MemoryScreen: React.FC<Props> = () => {
  const [timeline, setTimeline] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  const loadMemories = async () => {
    setLoading(true);
    try {
      const data = await fetchMemoryTimeline();
      setTimeline(data);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMemories();
  }, []);

  const handleDelete = async (id: string) => {
    await deleteMemory(id);
    loadMemories();
  };

  const filteredMemories = timeline.filter(m => {
    if (filterType !== 'all' && m.type !== filterType) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return m.title.toLowerCase().includes(q) || m.content.toLowerCase().includes(q);
    }
    return true;
  });

  const getTypeBadge = (type: string, status: string) => {
    switch (type) {
      case 'plan':
        return {
          bg: 'bg-indigo-500/10 text-indigo-300 border-indigo-500/20',
          icon: Target,
          label: 'Financial Plan'
        };
      case 'outcome':
        return {
          bg: status === 'failed' ? 'bg-amber-500/10 text-amber-300 border-amber-500/20' : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
          icon: status === 'failed' ? AlertTriangle : CheckCircle,
          label: status === 'failed' ? 'Observed Outcome (Missed)' : 'Observed Outcome (Success)'
        };
      case 'pattern':
        return {
          bg: 'bg-teal-500/10 text-teal-300 border-teal-500/20',
          icon: Sparkles,
          label: 'Learned Pattern'
        };
      case 'preference':
        return {
          bg: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
          icon: Brain,
          label: 'Adaptive Preference'
        };
      default:
        return {
          bg: 'bg-slate-800 text-slate-300 border-slate-700',
          icon: History,
          label: 'Profile Fact'
        };
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 animate-in fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-100">What Rahat Remembers</h1>
            <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Hindsight Engine
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Useful experiences and real-world outcomes that help your mentor make better decisions
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={loadMemories}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition-colors"
            title="Refresh memory timeline"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Narrative Concept Card */}
      <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/30 via-slate-900 to-sky-950/30 border border-slate-800 flex items-start gap-3">
        <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 shrink-0 mt-0.5 border border-emerald-500/20">
          <Brain className="w-5 h-5" />
        </div>
        <div className="space-y-1 text-xs">
          <h4 className="font-semibold text-slate-200">The Outcome-Aware Learning Loop</h4>
          <p className="text-slate-400 leading-relaxed">
            Rahat doesn't just store chat messages. It records <span className="text-indigo-400 font-medium">what was planned</span>, what <span className="text-amber-400 font-medium">actually happened</span>, and extracts <span className="text-teal-400 font-medium">patterns</span> to recommend realistic next steps.
          </p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        {/* Search */}
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search learned patterns, plans, or outcomes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-[#13171f] border border-slate-800 rounded-xl text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
          />
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
          {[
            { id: 'all', label: 'All' },
            { id: 'outcome', label: 'Outcomes' },
            { id: 'pattern', label: 'Patterns' },
            { id: 'plan', label: 'Plans' },
            { id: 'profile_fact', label: 'Facts' },
          ].map(f => (
            <button
              key={f.id}
              onClick={() => setFilterType(f.id)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-colors shrink-0 ${
                filterType === f.id
                  ? 'bg-emerald-600 text-white'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chronological Timeline */}
      {loading ? (
        <div className="py-12 text-center space-y-2">
          <RefreshCw className="w-7 h-7 text-emerald-500 animate-spin mx-auto" />
          <p className="text-xs text-slate-400">Loading Hindsight memory timeline...</p>
        </div>
      ) : filteredMemories.length === 0 ? (
        <div className="text-center py-12 p-6 rounded-2xl bg-[#13171f] border border-slate-800 space-y-2">
          <History className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-sm font-medium text-slate-300">Rahat hasn't learned much about you yet.</p>
          <p className="text-xs text-slate-500">As you log shifts and complete plans, meaningful experiences will appear here.</p>
        </div>
      ) : (
        <div className="relative pl-6 sm:pl-8 space-y-6 before:absolute before:left-2 sm:before:left-3 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
          {filteredMemories.map((mem) => {
            const badge = getTypeBadge(mem.type, mem.outcome_status);
            const BadgeIcon = badge.icon;

            return (
              <div
                key={mem.id}
                className="relative group animate-in fade-in slide-in-from-left-2 duration-200"
              >
                {/* Timeline node icon */}
                <div
                  className={`absolute -left-6 sm:-left-8 top-1.5 w-5 h-5 rounded-full flex items-center justify-center ring-4 ring-[#0b0d11] ${badge.bg}`}
                >
                  <div className="w-2 h-2 rounded-full bg-current" />
                </div>

                {/* Memory Card */}
                <div className="p-4 sm:p-5 rounded-2xl bg-[#13171f] border border-slate-800/80 hover:border-slate-700 transition-all space-y-2.5">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium border ${badge.bg}`}>
                        <BadgeIcon className="w-3 h-3" />
                        <span>{badge.label}</span>
                      </span>
                      <span className="flex items-center gap-1 text-xs text-slate-500">
                        <Calendar className="w-3 h-3" />
                        <span>{mem.date}</span>
                      </span>
                    </div>

                    <button
                      onClick={() => handleDelete(mem.id)}
                      title="Delete memory"
                      className="opacity-0 group-hover:opacity-100 p-1 rounded text-slate-500 hover:text-red-400 transition-all"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  <h3 className="text-sm font-semibold text-slate-100">{mem.title}</h3>

                  <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-line">
                    {mem.content}
                  </p>

                  {/* Relevance Tags */}
                  {mem.relevance_tags && mem.relevance_tags.length > 0 && (
                    <div className="flex items-center gap-1.5 pt-1 overflow-x-auto">
                      {mem.relevance_tags.map((tag, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 rounded-md bg-slate-900 text-[10px] text-slate-400 border border-slate-800"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
