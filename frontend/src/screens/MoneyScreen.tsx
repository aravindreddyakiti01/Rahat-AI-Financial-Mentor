import React, { useState, useEffect } from 'react';
import { ArrowDownLeft, ArrowUpRight, Plus, Camera, Target, Calendar, TrendingUp, RefreshCw, Trash2 } from 'lucide-react';
import type { FinanceSummary, Transaction } from '../types';
import { fetchFinanceSummary, fetchTransactions, deleteTransaction } from '../api';

interface Props {
  onOpenAddIncome: () => void;
  onOpenAddExpense: () => void;
  onOpenScanReceipt: () => void;
}

export const MoneyScreen: React.FC<Props> = ({
  onOpenAddIncome,
  onOpenAddExpense,
  onOpenScanReceipt,
}) => {
  const [summary, setSummary] = useState<FinanceSummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sum, txs] = await Promise.all([
        fetchFinanceSummary(),
        fetchTransactions()
      ]);
      setSummary(sum);
      setTransactions(txs);
      setLoading(false);
    } catch {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleDelete = async (id: string) => {
    await deleteTransaction(id);
    loadData();
  };

  if (loading && !summary) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-3">
        <RefreshCw className="w-8 h-8 text-emerald-500 animate-spin" />
        <p className="text-sm text-slate-400">Loading structured financial facts...</p>
      </div>
    );
  }

  const activeGoal = summary?.active_goal;

  return (
    <div className="max-w-4xl mx-auto px-4 py-6 space-y-6 animate-in fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-100">Money & Obligations</h1>
          <p className="text-xs text-slate-400">Current factual record from SQLite</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onOpenScanReceipt}
            className="px-3 py-2 rounded-xl bg-sky-950/40 hover:bg-sky-900/60 text-sky-400 border border-sky-500/30 text-xs font-semibold flex items-center gap-1.5 transition-colors"
          >
            <Camera className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Scan Receipt</span>
          </button>
          <button
            onClick={onOpenAddIncome}
            className="px-3 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-emerald-950"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Income</span>
          </button>
          <button
            onClick={onOpenAddExpense}
            className="px-3 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-amber-950"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Add Expense</span>
          </button>
        </div>
      </div>

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Income Card */}
        <div className="p-4 rounded-2xl bg-[#13171f] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>7-Day Income</span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <ArrowDownLeft className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-emerald-400">
            ₹{summary?.total_income_7d.toLocaleString() || '0'}
          </p>
          <p className="text-[11px] text-slate-500">
            Avg ₹{summary?.daily_avg_income.toFixed(0)}/day across shifts
          </p>
        </div>

        {/* Expense Card */}
        <div className="p-4 rounded-2xl bg-[#13171f] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>7-Day Expenses</span>
            <div className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400">
              <ArrowUpRight className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-amber-400">
            ₹{summary?.total_expenses_7d.toLocaleString() || '0'}
          </p>
          <p className="text-[11px] text-slate-500">
            Includes fuel, maintenance & food
          </p>
        </div>

        {/* Net Available Cash */}
        <div className="p-4 rounded-2xl bg-[#13171f] border border-slate-800 space-y-1">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Net Available</span>
            <div className="p-1.5 rounded-lg bg-sky-500/10 text-sky-400">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-sky-400">
            ₹{summary?.net_available.toLocaleString() || '0'}
          </p>
          <p className="text-[11px] text-slate-500">
            Cash in hand after running expenses
          </p>
        </div>
      </div>

      {/* Active Goal Progress Card */}
      {activeGoal && (
        <div className="p-5 rounded-2xl bg-gradient-to-br from-[#13171f] to-[#1a202c] border border-slate-800 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <Target className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-100">{activeGoal.title}</h3>
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-500" />
                    Due {activeGoal.due_date}
                  </span>
                  <span>•</span>
                  <span className="text-emerald-400 font-medium">
                    {activeGoal.days_remaining} days left
                  </span>
                </div>
              </div>
            </div>

            <div className="text-right">
              <span className="text-lg font-bold text-emerald-400">
                ₹{activeGoal.current_amount.toLocaleString()}
              </span>
              <span className="text-xs text-slate-500"> / ₹{activeGoal.target_amount.toLocaleString()}</span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-1.5">
            <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden p-0.5">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(activeGoal.progress_percentage || 0, 100)}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-400">
              <span>{activeGoal.progress_percentage}% completed</span>
              <span className="text-amber-400 font-medium">
                ₹{activeGoal.remaining_amount?.toLocaleString()} needed
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Recent Transactions List */}
      <div className="p-5 rounded-2xl bg-[#13171f] border border-slate-800 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-200">Recent Transactions</h2>
          <span className="text-xs text-slate-500">{transactions.length} entries</span>
        </div>

        {transactions.length === 0 ? (
          <div className="text-center py-8 space-y-2">
            <p className="text-sm text-slate-400">Your money history starts here.</p>
            <p className="text-xs text-slate-500">Log your first shift earnings or expense above.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-800/80">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="py-3 flex items-center justify-between gap-4 hover:bg-slate-900/40 px-2 rounded-xl transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                      tx.type === 'income'
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    }`}
                  >
                    {tx.type === 'income' ? (
                      <ArrowDownLeft className="w-4 h-4" />
                    ) : (
                      <ArrowUpRight className="w-4 h-4" />
                    )}
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-slate-200">{tx.description || tx.category}</p>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span>{tx.date}</span>
                      <span>•</span>
                      <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 text-[10px]">
                        {tx.category}
                      </span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`text-sm font-bold ${
                      tx.type === 'income' ? 'text-emerald-400' : 'text-slate-300'
                    }`}
                  >
                    {tx.type === 'income' ? '+' : '-'}₹{tx.amount.toLocaleString()}
                  </span>
                  <button
                    onClick={() => handleDelete(tx.id)}
                    title="Delete transaction"
                    className="p-1 rounded text-slate-600 hover:text-red-400 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
