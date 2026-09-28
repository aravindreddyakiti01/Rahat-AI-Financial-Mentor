import React, { useState } from 'react';
import { RotateCcw, Sparkles, ChevronRight, X } from 'lucide-react';
import { resetDemoState } from '../api';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onNavigateTab: (tab: string) => void;
  onSendPresetMessage: (msg: string) => void;
  onRefreshData: () => void;
}

export const DemoStoryWalkthrough: React.FC<Props> = ({
  isOpen,
  onClose,
  onNavigateTab,
  onSendPresetMessage,
  onRefreshData,
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isResetting, setIsResetting] = useState(false);

  if (!isOpen) return null;

  const steps = [
    {
      time: "0–10s",
      title: "1. The Gig Worker's Reality",
      description: "Meet Ramesh Kumar, a delivery partner with irregular daily earnings (₹430 to ₹1,300) and a fixed ₹4,500 bike loan EMI due every month.",
      actionLabel: "View Current Money",
      action: () => {
        onNavigateTab('money');
        setCurrentStep(1);
      }
    },
    {
      time: "10–25s",
      title: "2. The 'What Rahat Remembers' Timeline",
      description: "On Sept 12, Rahat advised saving ₹900/day. On Sept 16, the outcome was recorded: Ramesh missed the target because weekday earnings were lower (~₹500/day). On Sept 17, Rahat learned his weekend earnings are twice as high.",
      actionLabel: "View Hindsight Memory",
      action: () => {
        onNavigateTab('memory');
        setCurrentStep(2);
      }
    },
    {
      time: "25–45s",
      title: "3. Outcome-Aware Next Decision",
      description: "Now Ramesh asks: 'I need ₹4,500 for my EMI in 5 days. What should I do?'. Notice how Rahat DOES NOT repeat the failed ₹900/day advice, but provides an adaptive plan using weekend surge shifts!",
      actionLabel: "Ask Rahat (Run Case Study)",
      action: () => {
        onNavigateTab('mentor');
        onSendPresetMessage("I need ₹4,500 for my upcoming EMI in 5 days. What should I do?");
        setCurrentStep(3);
      }
    },
    {
      time: "45–60s",
      title: "4. The Hindsight Differentiator",
      description: "Click 'Why this advice?' on Rahat's answer to verify that the decision was directly adapted based on the Sept 16 failed outcome and Sept 17 learned surge pattern.",
      actionLabel: "Complete Walkthrough",
      action: () => {
        onClose();
      }
    }
  ];

  const handleReset = async () => {
    setIsResetting(true);
    await resetDemoState();
    onRefreshData();
    setIsResetting(false);
    setCurrentStep(0);
  };

  const step = steps[currentStep];

  return (
    <div className="fixed top-20 right-4 sm:right-8 z-50 w-full max-w-sm bg-[#13171f]/95 border border-emerald-500/30 rounded-2xl shadow-2xl p-4 backdrop-blur-md animate-in slide-in-from-top-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400">60-Second Demo Story</h4>
            <p className="text-[11px] text-slate-400">Outcome-Aware Financial Memory</p>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleReset}
            title="Reset to clean demo scenario"
            disabled={isResetting}
            className="p-1 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 text-xs transition-colors flex items-center gap-1"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isResetting ? 'animate-spin' : ''}`} />
            <span className="text-[10px]">Reset</span>
          </button>
          <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-slate-200">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Progress Dots */}
      <div className="flex items-center gap-1.5 my-3">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`h-1 rounded-full transition-all ${
              i === currentStep
                ? 'w-6 bg-emerald-500'
                : i < currentStep
                ? 'w-3 bg-emerald-700'
                : 'w-3 bg-slate-700'
            }`}
          />
        ))}
      </div>

      {/* Step Content */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="font-semibold text-slate-100">{step.title}</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">{step.time}</span>
        </div>
        <p className="text-xs text-slate-300 leading-relaxed">
          {step.description}
        </p>
      </div>

      {/* Action CTA */}
      <div className="mt-4 flex items-center justify-between">
        <span className="text-[11px] text-slate-400">Step {currentStep + 1} of 4</span>
        <button
          onClick={step.action}
          className="px-3 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1 transition-colors shadow-md shadow-emerald-950"
        >
          <span>{step.actionLabel}</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
