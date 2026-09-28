import { useState, useEffect } from 'react';
import { MessageSquare, Wallet, History, Sparkles, Settings, Play } from 'lucide-react';
import { MentorScreen } from './screens/MentorScreen';
import { MoneyScreen } from './screens/MoneyScreen';
import { MemoryScreen } from './screens/MemoryScreen';
import { InsightsScreen } from './screens/InsightsScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { AuthScreen } from './screens/AuthScreen';
import { LiquidGooeyAction } from './components/LiquidGooeyAction';
import { AddTransactionModal } from './components/AddTransactionModal';
import { ReceiptScanModal } from './components/ReceiptScanModal';
import { DemoStoryWalkthrough } from './components/DemoStoryWalkthrough';
import { BotAvatarWrapper } from './components/BotAvatarWrapper';
import { fetchCurrentUser, resetDemoState } from './api';

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(true);
  const [currentUser, setCurrentUser] = useState<any>({
    id: 'demo_user',
    name: 'Ramesh Kumar',
    email: 'ramesh.demo@rahat.app',
    role: 'Delivery Partner (Zomato/Swiggy)',
    pay_frequency: 'Daily',
    primary_obligation: 'Bike EMI (₹4,500)'
  });
  const [activeTab, setActiveTab] = useState<'mentor' | 'money' | 'memory' | 'insights' | 'settings'>('mentor');
  
  // Modals & walkthrough state
  const [isAddTxOpen, setIsAddTxOpen] = useState(false);
  const [addTxType, setAddTxType] = useState<'income' | 'expense'>('income');
  const [isReceiptScanOpen, setIsReceiptScanOpen] = useState(false);
  const [isDemoWalkthroughOpen, setIsDemoWalkthroughOpen] = useState(false);
  const [presetMessage, setPresetMessage] = useState<string | undefined>(undefined);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  useEffect(() => {
    fetchCurrentUser()
      .then(user => setCurrentUser(user))
      .catch(() => {});
  }, [refreshTrigger]);

  const handleAuthSuccess = (user: any) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
    setActiveTab('mentor');
  };

  const handleStartDemoMode = async () => {
    await resetDemoState();
    setCurrentUser({
      id: 'demo_user',
      name: 'Ramesh Kumar',
      email: 'ramesh.demo@rahat.app',
      role: 'Delivery Partner (Zomato/Swiggy)',
      pay_frequency: 'Daily',
      primary_obligation: 'Bike EMI (₹4,500)'
    });
    setIsAuthenticated(true);
    setActiveTab('mentor');
    setIsDemoWalkthroughOpen(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return (
      <AuthScreen
        onAuthenticated={handleAuthSuccess}
        onStartDemo={handleStartDemoMode}
      />
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0d11] text-slate-100 flex flex-col antialiased selection:bg-emerald-500/30 selection:text-emerald-200">
      
      {/* Top Header Navbar */}
      <header className="sticky top-0 z-30 bg-[#0f1218]/90 backdrop-blur-md border-b border-slate-800/80 px-4 py-3">
        <div className="max-w-5xl mx-auto flex items-center justify-between">
          {/* Logo & Product Identity */}
          <div
            onClick={() => setActiveTab('mentor')}
            className="flex items-center gap-2.5 cursor-pointer"
          >
            <BotAvatarWrapper size={32} state="default" />
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-tight text-slate-100">RAHAT</span>
                <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 text-[10px] font-semibold border border-emerald-500/20">
                  MENTOR
                </span>
              </div>
              <p className="text-[10px] text-slate-400 hidden sm:block">Outcome-Aware Financial Memory</p>
            </div>
          </div>

          {/* Navigation Items (Desktop) */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-900/80 p-1 rounded-2xl border border-slate-800">
            {[
              { id: 'mentor', label: 'Mentor', icon: MessageSquare },
              { id: 'money', label: 'Money', icon: Wallet },
              { id: 'memory', label: 'Memory', icon: History, highlight: true },
              { id: 'insights', label: 'Insights', icon: Sparkles },
              { id: 'settings', label: 'Settings', icon: Settings },
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                  {tab.highlight && (
                    <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-pulse" />
                  )}
                </button>
              );
            })}
          </nav>

          {/* Quick Demo Walkthrough CTA Button */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsDemoWalkthroughOpen(!isDemoWalkthroughOpen)}
              className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600/20 to-teal-600/20 hover:from-emerald-600/30 hover:to-teal-600/30 text-emerald-300 border border-emerald-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs"
            >
              <Play className="w-3 h-3 text-emerald-400 fill-current" />
              <span>60s Demo</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 pb-20 md:pb-6">
        {activeTab === 'mentor' && (
          <MentorScreen
            presetMessage={presetMessage}
            onClearPreset={() => setPresetMessage(undefined)}
          />
        )}
        {activeTab === 'money' && (
          <MoneyScreen
            key={refreshTrigger}
            onOpenAddIncome={() => { setAddTxType('income'); setIsAddTxOpen(true); }}
            onOpenAddExpense={() => { setAddTxType('expense'); setIsAddTxOpen(true); }}
            onOpenScanReceipt={() => setIsReceiptScanOpen(true)}
          />
        )}
        {activeTab === 'memory' && (
          <MemoryScreen key={refreshTrigger} />
        )}
        {activeTab === 'insights' && (
          <InsightsScreen key={refreshTrigger} />
        )}
        {activeTab === 'settings' && (
          <SettingsScreen
            user={currentUser}
            onLogout={handleLogout}
            onResetDemo={() => setRefreshTrigger(prev => prev + 1)}
          />
        )}
      </main>

      {/* Signature Liquid Gooey Quick Action */}
      <LiquidGooeyAction
        onAddIncome={() => { setAddTxType('income'); setIsAddTxOpen(true); }}
        onAddExpense={() => { setAddTxType('expense'); setIsAddTxOpen(true); }}
        onScanReceipt={() => setIsReceiptScanOpen(true)}
        onAskRahat={() => {
          setActiveTab('mentor');
          setPresetMessage("What should I do today to stay on track for my EMI?");
        }}
      />

      {/* Bottom Navigation Bar (Mobile) */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-[#0f1218]/95 backdrop-blur-lg border-t border-slate-800/80 px-2 py-1.5 flex items-center justify-around">
        {[
          { id: 'mentor', label: 'Mentor', icon: MessageSquare },
          { id: 'money', label: 'Money', icon: Wallet },
          { id: 'memory', label: 'Memory', icon: History, highlight: true },
          { id: 'insights', label: 'Insights', icon: Sparkles },
          { id: 'settings', label: 'Settings', icon: Settings },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex flex-col items-center gap-0.5 px-3 py-1 rounded-xl text-[10px] font-medium transition-all ${
                isActive ? 'text-emerald-400 font-semibold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="relative">
                <Icon className="w-5 h-5" />
                {tab.highlight && (
                  <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-sky-400 ring-2 ring-[#0b0d11]" />
                )}
              </div>
              <span>{tab.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Modals & Guides */}
      <AddTransactionModal
        isOpen={isAddTxOpen}
        initialType={addTxType}
        onClose={() => setIsAddTxOpen(false)}
        onSuccess={() => setRefreshTrigger(prev => prev + 1)}
      />

      <ReceiptScanModal
        isOpen={isReceiptScanOpen}
        onClose={() => setIsReceiptScanOpen(false)}
        onSuccess={() => setRefreshTrigger(prev => prev + 1)}
      />

      <DemoStoryWalkthrough
        isOpen={isDemoWalkthroughOpen}
        onClose={() => setIsDemoWalkthroughOpen(false)}
        onNavigateTab={(t: any) => setActiveTab(t)}
        onSendPresetMessage={(msg) => setPresetMessage(msg)}
        onRefreshData={() => setRefreshTrigger(prev => prev + 1)}
      />
    </div>
  );
}

export default App;
