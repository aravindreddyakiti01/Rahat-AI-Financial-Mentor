import React, { useState } from 'react';
import { ArrowRight, Sparkles, Check, Eye, EyeOff, Brain } from 'lucide-react';
import { BotAvatarWrapper } from '../components/BotAvatarWrapper';
import { ThinkingOrbWrapper } from '../components/ThinkingOrbWrapper';
import { signupUser, loginUser } from '../api';

interface Props {
  onAuthenticated: (user: any, token: string) => void;
  onStartDemo: () => void;
}

export const AuthScreen: React.FC<Props> = ({ onAuthenticated, onStartDemo }) => {
  const [view, setView] = useState<'welcome' | 'login' | 'signup' | 'onboarding'>('welcome');
  
  // Form State
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 6-step Onboarding State
  const [onboardingStep, setOnboardingStep] = useState(1);
  const [role, setRole] = useState('Delivery');
  const [payFrequency, setPayFrequency] = useState('Daily');
  const [primaryGoal, setPrimaryGoal] = useState('EMI');
  const [targetAmount, setTargetAmount] = useState('4500');
  const [dueDate, setDueDate] = useState('2026-10-05');
  const [recurringObligation, setRecurringObligation] = useState('Bike EMI');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await loginUser(email, password);
      setLoading(false);
      onAuthenticated(res.user, res.token);
    } catch (err: any) {
      setLoading(false);
      setError(err.message || 'Login failed');
    }
  };

  const handleSignupSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!agreedToTerms) {
      setError("Please agree to the Terms of Service and Privacy Policy");
      return;
    }
    setView('onboarding');
  };

  const handleCompleteOnboarding = async () => {
    setLoading(true);
    try {
      const res = await signupUser({
        name,
        email,
        password,
        role,
        pay_frequency: payFrequency,
        primary_obligation: `${recurringObligation} (₹${targetAmount})`
      });
      setLoading(false);
      onAuthenticated(res.user, res.token);
    } catch (err: any) {
      setLoading(false);
      setError(err.message || 'Signup failed');
      setView('signup');
    }
  };

  return (
    <div className="min-h-screen haikei-bg flex flex-col justify-center items-center px-4 py-8 relative">
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-md bg-[#13171f]/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-xl">
        
        {/* VIEW 1: WELCOME SCREEN */}
        {view === 'welcome' && (
          <div className="text-center space-y-6 animate-in fade-in">
            <div className="flex flex-col items-center justify-center space-y-3">
              <div className="relative">
                <BotAvatarWrapper size={68} state="default" />
                <div className="absolute -bottom-1 -right-1">
                  <ThinkingOrbWrapper state="breathing" size={24} />
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-slate-100 tracking-tight">RAHAT</h1>
                <p className="text-xs text-emerald-400 font-semibold uppercase tracking-wider">
                  Personal Financial Mentor for Gig Workers
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-lg font-semibold text-slate-100 leading-snug">
                Your money changes every day.<br />
                <span className="text-emerald-400">Your mentor learns with you.</span>
              </h2>
              <p className="text-xs text-slate-400 leading-relaxed max-w-sm mx-auto">
                Rahat remembers your goals, plans and outcomes so financial guidance becomes more personal over time.
              </p>
            </div>

            <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800 flex items-center gap-3 text-left">
              <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 shrink-0">
                <Brain className="w-5 h-5" />
              </div>
              <div className="text-[11px] text-slate-300">
                <span className="font-semibold text-slate-100 block">Outcome-Aware Financial Memory</span>
                Adapts advice based on what actually happened in your previous plans.
              </div>
            </div>

            <div className="space-y-3 pt-2">
              <button
                onClick={() => setView('signup')}
                className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold transition-all shadow-lg shadow-emerald-950 flex items-center justify-center gap-2"
              >
                <span>Continue</span>
                <ArrowRight className="w-4 h-4" />
              </button>

              <button
                onClick={onStartDemo}
                className="w-full py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-200 text-sm font-medium border border-slate-700 transition-all flex items-center justify-center gap-2"
              >
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>Try Demo (Ramesh's EMI Case Study)</span>
              </button>
            </div>

            <div className="pt-2 text-xs text-slate-400">
              Already have an account?{' '}
              <button
                onClick={() => setView('login')}
                className="text-emerald-400 hover:underline font-medium"
              >
                Sign In
              </button>
            </div>
          </div>
        )}

        {/* VIEW 2: SIGN UP */}
        {view === 'signup' && (
          <div className="space-y-5 animate-in fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-lg font-bold text-slate-100">Create Mentor Account</h2>
              <button onClick={() => setView('welcome')} className="text-xs text-slate-400 hover:text-slate-200">
                Back
              </button>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/30 text-xs text-red-300">
                {error}
              </div>
            )}

            <form onSubmit={handleSignupSubmit} className="space-y-3.5">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="ramesh@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password (At least 8 chars)</label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500 pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Confirm Password</label>
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Terms Checkbox */}
              <div className="flex items-start gap-2 pt-1">
                <input
                  type="checkbox"
                  id="terms"
                  checked={agreedToTerms}
                  onChange={(e) => setAgreedToTerms(e.target.checked)}
                  className="mt-0.5 w-4 h-4 accent-emerald-500 rounded cursor-pointer"
                />
                <label htmlFor="terms" className="text-[11px] text-slate-400 cursor-pointer">
                  I agree to the Terms of Service and Privacy Policy. I understand Rahat provides financial planning support, not regulated financial advice.
                </label>
              </div>

              <button
                type="submit"
                className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow-md shadow-emerald-950 flex items-center justify-center gap-2 mt-2"
              >
                <span>Continue to Profile Setup</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </form>

            <div className="text-center text-xs text-slate-400">
              Already have an account?{' '}
              <button onClick={() => setView('login')} className="text-emerald-400 hover:underline">
                Sign In
              </button>
            </div>
          </div>
        )}

        {/* VIEW 3: LOGIN */}
        {view === 'login' && (
          <div className="space-y-5 animate-in fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h2 className="text-lg font-bold text-slate-100">Welcome Back</h2>
              <button onClick={() => setView('welcome')} className="text-xs text-slate-400 hover:text-slate-200">
                Back
              </button>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/30 text-xs text-red-300">
                {error}
              </div>
            )}

            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Email</label>
                <input
                  type="email"
                  required
                  placeholder="ramesh@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Password</label>
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition-all shadow-md shadow-emerald-950"
              >
                {loading ? "Signing in..." : "Sign In"}
              </button>
            </form>

            <div className="text-center text-xs text-slate-400 pt-2">
              Don't have an account?{' '}
              <button onClick={() => setView('signup')} className="text-emerald-400 hover:underline">
                Create Account
              </button>
            </div>
          </div>
        )}

        {/* VIEW 4: ONBOARDING (6 STEPS) */}
        {view === 'onboarding' && (
          <div className="space-y-5 animate-in fade-in">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">
                  Step {onboardingStep} of 6
                </span>
                <h2 className="text-base font-bold text-slate-100">Setup Your Financial Context</h2>
              </div>
              <div className="flex items-center gap-1">
                {[1, 2, 3, 4, 5, 6].map(i => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-full ${
                      i <= onboardingStep ? 'bg-emerald-500' : 'bg-slate-700'
                    }`}
                  />
                ))}
              </div>
            </div>

            {/* Step 1: Work Type */}
            {onboardingStep === 1 && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 font-medium">What kind of work do you do?</p>
                <div className="grid grid-cols-2 gap-2">
                  {['Delivery', 'Ride-share', 'Freelance', 'Other'].map(r => (
                    <button
                      key={r}
                      type="button"
                      onClick={() => setRole(r)}
                      className={`p-3 rounded-xl text-xs font-medium border transition-all ${
                        role === r
                          ? 'bg-emerald-950/40 border-emerald-500 text-emerald-300'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 2: Pay Frequency */}
            {onboardingStep === 2 && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 font-medium">How often do you get paid?</p>
                <div className="grid grid-cols-3 gap-2">
                  {['Daily', 'Weekly', 'Irregular'].map(f => (
                    <button
                      key={f}
                      type="button"
                      onClick={() => setPayFrequency(f)}
                      className={`p-3 rounded-xl text-xs font-medium border transition-all ${
                        payFrequency === f
                          ? 'bg-emerald-950/40 border-emerald-500 text-emerald-300'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {f}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Priority Goal */}
            {onboardingStep === 3 && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 font-medium">What financial goal matters most right now?</p>
                <div className="grid grid-cols-2 gap-2">
                  {['EMI', 'Rent', 'Savings', 'Emergency fund'].map(g => (
                    <button
                      key={g}
                      type="button"
                      onClick={() => setPrimaryGoal(g)}
                      className={`p-3 rounded-xl text-xs font-medium border transition-all ${
                        primaryGoal === g
                          ? 'bg-emerald-950/40 border-emerald-500 text-emerald-300'
                          : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {g}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Step 4: Target Amount */}
            {onboardingStep === 4 && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 font-medium">What is your target amount?</p>
                <div className="relative">
                  <span className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500 text-sm">₹</span>
                  <input
                    type="number"
                    value={targetAmount}
                    onChange={(e) => setTargetAmount(e.target.value)}
                    className="w-full pl-8 pr-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-emerald-500"
                    placeholder="4500"
                  />
                </div>
              </div>
            )}

            {/* Step 5: Due Date */}
            {onboardingStep === 5 && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 font-medium">When is this target due?</p>
                <input
                  type="date"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}

            {/* Step 6: Recurring Obligation */}
            {onboardingStep === 6 && (
              <div className="space-y-3">
                <p className="text-xs text-slate-300 font-medium">Any optional recurring obligation?</p>
                <input
                  type="text"
                  value={recurringObligation}
                  onChange={(e) => setRecurringObligation(e.target.value)}
                  placeholder="e.g. Hero Splendor Bike Loan"
                  className="w-full px-3.5 py-2.5 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 text-xs focus:outline-none focus:border-emerald-500"
                />
              </div>
            )}

            {/* Navigation Buttons */}
            <div className="flex items-center justify-between pt-3">
              {onboardingStep > 1 ? (
                <button
                  type="button"
                  onClick={() => setOnboardingStep(onboardingStep - 1)}
                  className="px-3.5 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-medium"
                >
                  Back
                </button>
              ) : <div />}

              {onboardingStep < 6 ? (
                <button
                  type="button"
                  onClick={() => setOnboardingStep(onboardingStep + 1)}
                  className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5"
                >
                  <span>Next</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleCompleteOnboarding}
                  disabled={loading}
                  className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-emerald-950"
                >
                  <span>{loading ? "Creating Mentor..." : "Finish & Start"}</span>
                  <Check className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
