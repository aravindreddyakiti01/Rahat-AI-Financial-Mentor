import React from 'react';
import { Mic, ShieldCheck } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onAllow: () => void;
  onDeny: () => void;
  errorMessage?: string | null;
}

export const MicrophonePermissionModal: React.FC<Props> = ({
  isOpen,
  onAllow,
  onDeny,
  errorMessage,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-in fade-in">
      <div className="relative w-full max-w-md bg-[#13171f] border border-slate-800 rounded-2xl shadow-2xl p-6 text-center">
        {/* Icon */}
        <div className="mx-auto w-14 h-14 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-4">
          <Mic className="w-7 h-7" />
        </div>

        {/* Title */}
        <h3 className="text-lg font-semibold text-slate-100">
          Enable Voice Guidance
        </h3>

        {/* Description */}
        <p className="mt-2 text-sm text-slate-300 leading-relaxed">
          Rahat can listen to your voice so you can log income, expenses, and ask questions hands-free after a shift without typing.
        </p>

        {/* Privacy reassurance */}
        <div className="mt-4 p-3 rounded-xl bg-slate-900/60 border border-slate-800 flex items-center gap-2.5 text-left text-xs text-slate-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Your microphone is only activated when you tap the mic button. No continuous audio is recorded.</span>
        </div>

        {/* Error message if blocked */}
        {errorMessage && (
          <div className="mt-3 p-2.5 rounded-lg bg-red-950/40 border border-red-500/30 text-xs text-red-300">
            {errorMessage}
          </div>
        )}

        {/* Action Buttons */}
        <div className="mt-6 flex items-center justify-center gap-3">
          <button
            onClick={onDeny}
            className="flex-1 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition-colors"
          >
            Not now
          </button>
          <button
            onClick={onAllow}
            className="flex-1 px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-medium transition-colors shadow-lg shadow-emerald-900/40"
          >
            Allow microphone
          </button>
        </div>
      </div>
    </div>
  );
};
