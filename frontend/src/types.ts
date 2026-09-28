export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  pay_frequency: string;
  primary_obligation: string;
  created_at?: string;
}

export interface Goal {
  id: string;
  user_id: string;
  title: string;
  target_amount: number;
  current_amount: number;
  due_date: string;
  category: string;
  status: 'active' | 'completed' | 'missed';
  remaining_amount?: number;
  days_remaining?: number;
  progress_percentage?: number;
}

export interface Transaction {
  id: string;
  user_id: string;
  amount: number;
  type: 'income' | 'expense';
  category: string;
  description: string;
  date: string;
  source: 'manual' | 'voice' | 'ocr' | 'seed';
}

export interface MemoryItem {
  id: string;
  user_id: string;
  type: 'profile_fact' | 'plan' | 'outcome' | 'pattern' | 'preference';
  title: string;
  content: string;
  category: string;
  outcome_status: 'succeeded' | 'failed' | 'learned' | 'observed' | 'active';
  related_goal_id?: string;
  relevance_tags: string[];
  date: string;
}

export interface StructuredAgentResponse {
  text: string;
  facts: string[];
  pattern: string;
  recommendation: string;
  why_this_advice: string[];
  memories_used_count: number;
  primary_memory_influence: string;
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'rahat';
  text: string;
  timestamp: string;
  structuredResponse?: StructuredAgentResponse;
  voiceAudioUrl?: string;
  isConfirmed?: boolean;
}

export interface FinanceSummary {
  total_income_7d: number;
  total_expenses_7d: number;
  net_available: number;
  active_goal: Goal | null;
  goal_progress_percent: number;
  daily_avg_income: number;
  obligations: any[];
}

export interface Insight {
  id: string;
  title: string;
  description: string;
  type: 'positive' | 'neutral' | 'warning';
  metric: string;
}

export type ThinkingState = 
  | 'working' 
  | 'searching' 
  | 'solving' 
  | 'listening' 
  | 'connecting' 
  | 'weaving' 
  | 'composing' 
  | 'breathing' 
  | 'shaping';
