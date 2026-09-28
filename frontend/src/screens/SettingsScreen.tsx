import React, { useState } from 'react';
import { User, Shield, Bell, FileText, Trash2, RotateCcw, Check, LogOut, ChevronRight } from 'lucide-react';
import { clearAllMemories, resetDemoState } from '../api';

interface Props {
  user: any;
  onLogout: () => void;
  onResetDemo: () => void;
}

export const SettingsScreen: React.FC<Props> = ({ user, onLogout, onResetDemo }) => {
  const [activeModal, setActiveModal] = useState<'privacy' | 'terms' | 'disclaimer' | null>(null);
  const [notificationEnabled, setNotificationEnabled] = useState(true);
  const [voiceVoiceFeedback, setVoiceFeedback] = useState(true);
  const [message, setMessage] = useState<string | null>(null);

  const handleClearMemory = async () => {
    if (window.confirm("Are you sure you want to clear all experiential memories from Hindsight?")) {
      await clearAllMemories();
      setMessage("All learned memories have been cleared.");
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const handleResetDemoData = async () => {
    await resetDemoState();
    onResetDemo();
    setMessage("Demo case study reset to initial state.");
    setTimeout(() => setMessage(null), 3000);
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-6 space-y-6 animate-in fade-in">
      <div>
        <h1 className="text-xl font-bold text-slate-100">Settings & Controls</h1>
        <p className="text-xs text-slate-400 mt-0.5">Manage your profile, memory privacy, and app preferences</p>
      </div>

      {message && (
        <div className="p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-xs text-emerald-300 flex items-center gap-2">
          <Check className="w-4 h-4" />
          <span>{message}</span>
        </div>
      )}

      {/* Account Profile Card */}
      <div className="p-5 rounded-2xl bg-[#13171f] border border-slate-800 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <User className="w-4 h-4 text-emerald-400" />
          <span>Profile Details</span>
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-500">Name</span>
            <p className="text-slate-200 font-medium mt-0.5">{user?.name || 'Ramesh Kumar'}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-500">Email</span>
            <p className="text-slate-200 font-medium mt-0.5">{user?.email || 'ramesh.demo@rahat.app'}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-500">Work Role</span>
            <p className="text-slate-200 font-medium mt-0.5">{user?.role || 'Delivery Partner (Zomato/Swiggy)'}</p>
          </div>
          <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
            <span className="text-slate-500">Payout Frequency</span>
            <p className="text-slate-200 font-medium mt-0.5">{user?.pay_frequency || 'Daily Payouts'}</p>
          </div>
        </div>
      </div>

      {/* Preferences */}
      <div className="p-5 rounded-2xl bg-[#13171f] border border-slate-800 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Bell className="w-4 h-4 text-sky-400" />
          <span>App Preferences</span>
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-xs font-medium text-slate-200">Goal & EMI Reminders</p>
              <p className="text-[11px] text-slate-400">Gentle reminders for upcoming obligations</p>
            </div>
            <input
              type="checkbox"
              checked={notificationEnabled}
              onChange={(e) => setNotificationEnabled(e.target.checked)}
              className="w-4 h-4 accent-emerald-500 cursor-pointer"
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-xs font-medium text-slate-200">Voice Audio Feedback</p>
              <p className="text-[11px] text-slate-400">Audio tone when microphone starts listening</p>
            </div>
            <input
              type="checkbox"
              checked={voiceVoiceFeedback}
              onChange={(e) => setVoiceFeedback(e.target.checked)}
              className="w-4 h-4 accent-emerald-500 cursor-pointer"
            />
          </div>
        </div>
      </div>

      {/* Memory & Data Agency */}
      <div className="p-5 rounded-2xl bg-[#13171f] border border-slate-800 space-y-4">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Shield className="w-4 h-4 text-amber-400" />
          <span>Hindsight Memory & Data Agency</span>
        </h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-xs font-medium text-slate-200">Reset Demo Case Study</p>
              <p className="text-[11px] text-slate-400">Restore the deterministic ₹4,500 EMI scenario & memories</p>
            </div>
            <button
              onClick={handleResetDemoData}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset Demo</span>
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-xl bg-slate-900 border border-slate-800">
            <div>
              <p className="text-xs font-medium text-red-300">Clear Learned Memories</p>
              <p className="text-[11px] text-slate-400">Deletes all Hindsight experiential outcomes and patterns</p>
            </div>
            <button
              onClick={handleClearMemory}
              className="px-3 py-1.5 rounded-xl bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-500/30 text-xs font-medium flex items-center gap-1.5 transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear Memories</span>
            </button>
          </div>
        </div>
      </div>

      {/* Trust, Legal & Disclaimer */}
      <div className="p-5 rounded-2xl bg-[#13171f] border border-slate-800 space-y-3">
        <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <FileText className="w-4 h-4 text-teal-400" />
          <span>Trust & Legal Information</span>
        </h3>

        <div className="space-y-1 divide-y divide-slate-800">
          <button
            onClick={() => setActiveModal('disclaimer')}
            className="w-full py-2.5 flex items-center justify-between text-xs text-slate-300 hover:text-emerald-400 transition-colors"
          >
            <span>Financial Disclaimer</span>
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => setActiveModal('privacy')}
            className="w-full py-2.5 flex items-center justify-between text-xs text-slate-300 hover:text-emerald-400 transition-colors"
          >
            <span>Privacy Policy & Data Security</span>
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => setActiveModal('terms')}
            className="w-full py-2.5 flex items-center justify-between text-xs text-slate-300 hover:text-emerald-400 transition-colors"
          >
            <span>Terms of Service</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Logout */}
      <div className="pt-2 flex justify-end">
        <button
          onClick={onLogout}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium flex items-center gap-2 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out</span>
        </button>
      </div>

      {/* Legal Modals */}
      {activeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
          <div className="relative w-full max-w-lg bg-[#13171f] border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4 max-h-[80vh] overflow-y-auto">
            <h3 className="text-base font-bold text-slate-100">
              {activeModal === 'disclaimer' && 'Financial Disclaimer'}
              {activeModal === 'privacy' && 'Privacy Policy & Data Rights'}
              {activeModal === 'terms' && 'Terms of Service'}
            </h3>

            <div className="text-xs text-slate-300 leading-relaxed space-y-3">
              {activeModal === 'disclaimer' && (
                <>
                  <p className="font-semibold text-amber-400">
                    "Rahat provides financial planning and decision support, not regulated financial advice. It does not guarantee income, savings or financial outcomes."
                  </p>
                  <p>
                    Rahat is designed to assist gig workers and freelancers in organizing irregular daily cashflow against fixed obligations like EMIs and rent. All projections and suggestions are based solely on your past logged transactions and outcome history.
                  </p>
                </>
              )}

              {activeModal === 'privacy' && (
                <>
                  <p>
                    <strong>Financial Data:</strong> Your income, expense, and transaction records are stored securely in your private SQLite database.
                  </p>
                  <p>
                    <strong>Outcome-Aware Memory:</strong> Hindsight stores selective financial plans, real-world outcomes, and behavioral patterns. You retain full agency to view, filter, or delete any memory at any time.
                  </p>
                  <p>
                    <strong>Voice & Receipts:</strong> Microphone and Camera permissions are strictly on-demand. Audio is processed transiently and never stored continuously. Receipts require user confirmation before any record is created.
                  </p>
                </>
              )}

              {activeModal === 'terms' && (
                <>
                  <p>
                    By using Rahat, you acknowledge that the application is a personal financial companion designed for decision support.
                  </p>
                  <p>
                    You agree to provide accurate shift records for meaningful mentorship. You may export or reset your demo and financial data at any time.
                  </p>
                </>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800">
              <button
                onClick={() => setActiveModal(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
