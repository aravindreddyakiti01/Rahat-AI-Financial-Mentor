import React, { useState } from 'react';
import { X, ArrowDownLeft, ArrowUpRight, Loader2 } from 'lucide-react';
import { recordIncome, recordExpense } from '../api';

interface Props {
  isOpen: boolean;
  initialType?: 'income' | 'expense';
  onClose: () => void;
  onSuccess: (tx: any) => void;
}

export const AddTransactionModal: React.FC<Props> = ({
  isOpen,
  initialType = 'income',
  onClose,
  onSuccess,
}) => {
  const [type, setType] = useState<'income' | 'expense'>(initialType);
  const [amount, setAmount] = useState<string>('');
  const [category, setCategory] = useState<string>(initialType === 'income' ? 'Delivery Earnings' : 'Fuel');
  const [description, setDescription] = useState<string>('');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const numAmount = parseFloat(amount);
    if (isNaN(numAmount) || numAmount <= 0) return;

    setLoading(true);
    try {
      let res;
      if (type === 'income') {
        res = await recordIncome(numAmount, category, description || 'Shift earnings');
      } else {
        res = await recordExpense(numAmount, category, description || 'Expense');
      }
      setLoading(false);
      onSuccess(res);
      onClose();
    } catch (e) {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-md bg-[#13171f] border border-slate-800 rounded-2xl shadow-2xl p-6">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="text-base font-semibold text-slate-100">Log Transaction</h3>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Type Toggle */}
        <div className="mt-4 grid grid-cols-2 gap-2 p-1 bg-slate-900 rounded-xl border border-slate-800">
          <button
            type="button"
            onClick={() => { setType('income'); setCategory('Delivery Earnings'); }}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
              type === 'income'
                ? 'bg-emerald-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ArrowDownLeft className="w-3.5 h-3.5" />
            <span>Income</span>
          </button>
          <button
            type="button"
            onClick={() => { setType('expense'); setCategory('Fuel'); }}
            className={`flex items-center justify-center gap-1.5 py-2 rounded-lg text-xs font-medium transition-all ${
              type === 'expense'
                ? 'bg-amber-600 text-white shadow-md'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ArrowUpRight className="w-3.5 h-3.5" />
            <span>Expense</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-4 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Amount (₹)</label>
            <input
              type="number"
              required
              placeholder="e.g. 750"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
            >
              {type === 'income' ? (
                <>
                  <option value="Delivery Earnings">Delivery Earnings (Zomato/Swiggy)</option>
                  <option value="Ride-Share Payout">Ride-Share Payout (Uber/Ola)</option>
                  <option value="Incentive & Bonus">Platform Incentive / Bonus</option>
                  <option value="Tips & Other">Tips & Cash</option>
                </>
              ) : (
                <>
                  <option value="Fuel">Fuel (Petrol/Diesel)</option>
                  <option value="Maintenance">Vehicle Maintenance / Service</option>
                  <option value="Food & Chai">Shift Food & Chai</option>
                  <option value="EMI & Loan">Bike / Personal Loan</option>
                  <option value="Personal">Personal & Family</option>
                </>
              )}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
            <input
              type="text"
              placeholder="e.g. Dinner rush 12 orders"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 text-sm focus:outline-none focus:border-emerald-500"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-colors flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Save Record'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
