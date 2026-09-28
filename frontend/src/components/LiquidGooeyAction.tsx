import React, { useState } from 'react';
import { Plus, ArrowUpRight, ArrowDownLeft, Camera, Sparkles, X } from 'lucide-react';

interface Props {
  onAddIncome: () => void;
  onAddExpense: () => void;
  onScanReceipt: () => void;
  onAskRahat: () => void;
}

export const LiquidGooeyAction: React.FC<Props> = ({
  onAddIncome,
  onAddExpense,
  onScanReceipt,
  onAskRahat,
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggle = () => setIsOpen(!isOpen);

  return (
    <div className="fixed bottom-20 right-5 sm:bottom-8 sm:right-8 z-40">
      {/* Backdrop when open */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/40 backdrop-blur-xs -z-10 transition-opacity"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Action Items Cluster */}
      <div className="relative flex items-center justify-center">
        {isOpen && (
          <div className="absolute bottom-16 right-0 flex flex-col items-end gap-3 pointer-events-auto transition-all animate-in fade-in slide-in-from-bottom-4 duration-200">
            {/* Action 1: Add Income */}
            <button
              onClick={() => { setIsOpen(false); onAddIncome(); }}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#1a202c] hover:bg-[#222938] text-emerald-400 border border-emerald-500/20 shadow-lg font-medium text-sm transition-all hover:scale-105"
            >
              <ArrowDownLeft className="w-4 h-4" />
              <span>Add Daily Income</span>
            </button>

            {/* Action 2: Add Expense */}
            <button
              onClick={() => { setIsOpen(false); onAddExpense(); }}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#1a202c] hover:bg-[#222938] text-amber-400 border border-amber-500/20 shadow-lg font-medium text-sm transition-all hover:scale-105"
            >
              <ArrowUpRight className="w-4 h-4" />
              <span>Add Fuel / Expense</span>
            </button>

            {/* Action 3: Scan Receipt */}
            <button
              onClick={() => { setIsOpen(false); onScanReceipt(); }}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#1a202c] hover:bg-[#222938] text-sky-400 border border-sky-500/20 shadow-lg font-medium text-sm transition-all hover:scale-105"
            >
              <Camera className="w-4 h-4" />
              <span>Scan Receipt (OCR)</span>
            </button>

            {/* Action 4: Ask Rahat */}
            <button
              onClick={() => { setIsOpen(false); onAskRahat(); }}
              className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-[#1a202c] hover:bg-[#222938] text-teal-300 border border-teal-500/20 shadow-lg font-medium text-sm transition-all hover:scale-105"
            >
              <Sparkles className="w-4 h-4" />
              <span>Ask Mentor</span>
            </button>
          </div>
        )}

        {/* Primary Trigger Button */}
        <button
          onClick={toggle}
          aria-label="Quick Actions"
          className={`w-13 h-13 rounded-full flex items-center justify-center text-white shadow-xl transition-all duration-300 ${
            isOpen
              ? 'bg-zinc-700 rotate-90 scale-95 ring-2 ring-zinc-500'
              : 'bg-gradient-to-tr from-emerald-600 to-teal-500 hover:from-emerald-500 hover:to-teal-400 hover:scale-105 ring-4 ring-emerald-500/20'
          }`}
        >
          {isOpen ? <X className="w-6 h-6" /> : <Plus className="w-6 h-6" />}
        </button>
      </div>
    </div>
  );
};
