import type { User, Goal, Transaction, MemoryItem, FinanceSummary, Insight, StructuredAgentResponse } from './types';

const API_BASE = '/api';

export async function fetchCurrentUser(token?: string): Promise<User> {
  const headers: Record<string, string> = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;
  
  const res = await fetch(`${API_BASE}/auth/me`, { headers });
  if (!res.ok) throw new Error('Failed to fetch profile');
  return res.json();
}

export async function loginUser(email: string, password: string): Promise<{ token: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Login failed');
  }
  return res.json();
}

export async function signupUser(data: {
  name: string;
  email: string;
  password: string;
  role: string;
  pay_frequency: string;
  primary_obligation: string;
}): Promise<{ token: string; user: User }> {
  const res = await fetch(`${API_BASE}/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Signup failed');
  }
  return res.json();
}

export async function fetchFinanceSummary(userId = 'demo_user'): Promise<FinanceSummary> {
  const res = await fetch(`${API_BASE}/finance/summary?user_id=${userId}`);
  if (!res.ok) throw new Error('Failed to load finance summary');
  return res.json();
}

export async function fetchTransactions(userId = 'demo_user'): Promise<Transaction[]> {
  const res = await fetch(`${API_BASE}/finance/transactions?user_id=${userId}`);
  if (!res.ok) throw new Error('Failed to load transactions');
  return res.json();
}

export async function recordIncome(amount: number, category: string, description: string, userId = 'demo_user'): Promise<Transaction> {
  const res = await fetch(`${API_BASE}/finance/income?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, category, description, type: 'income' }),
  });
  if (!res.ok) throw new Error('Failed to record income');
  return res.json();
}

export async function recordExpense(amount: number, category: string, description: string, userId = 'demo_user'): Promise<Transaction> {
  const res = await fetch(`${API_BASE}/finance/expense?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ amount, category, description, type: 'expense' }),
  });
  if (!res.ok) throw new Error('Failed to record expense');
  return res.json();
}

export async function deleteTransaction(txId: string, userId = 'demo_user'): Promise<boolean> {
  const res = await fetch(`${API_BASE}/finance/transactions/${txId}?user_id=${userId}`, {
    method: 'DELETE',
  });
  return res.ok;
}

export async function fetchGoals(userId = 'demo_user'): Promise<Goal[]> {
  const res = await fetch(`${API_BASE}/goals?user_id=${userId}`);
  if (!res.ok) throw new Error('Failed to load goals');
  return res.json();
}

export async function createGoal(title: string, target_amount: number, due_date: string, category = 'emi', userId = 'demo_user'): Promise<Goal> {
  const res = await fetch(`${API_BASE}/goals?user_id=${userId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, target_amount, due_date, category }),
  });
  if (!res.ok) throw new Error('Failed to create goal');
  return res.json();
}

export async function fetchMemoryTimeline(userId = 'demo_user'): Promise<MemoryItem[]> {
  const res = await fetch(`${API_BASE}/memory/timeline?user_id=${userId}`);
  if (!res.ok) throw new Error('Failed to load memory timeline');
  return res.json();
}

export async function deleteMemory(memoryId: string, userId = 'demo_user'): Promise<boolean> {
  const res = await fetch(`${API_BASE}/memory/${memoryId}?user_id=${userId}`, {
    method: 'DELETE',
  });
  return res.ok;
}

export async function clearAllMemories(userId = 'demo_user'): Promise<boolean> {
  const res = await fetch(`${API_BASE}/memory/clear?user_id=${userId}`, {
    method: 'POST',
  });
  return res.ok;
}

export async function sendAgentMessage(message: string, userId = 'demo_user'): Promise<StructuredAgentResponse> {
  const res = await fetch(`${API_BASE}/agent/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, user_id: userId }),
  });
  if (!res.ok) throw new Error('Failed to reach Rahat agent');
  return res.json();
}

export async function sendVoiceTranscript(transcript: string, userId = 'demo_user'): Promise<any> {
  const res = await fetch(`${API_BASE}/agent/voice`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ transcript, user_id: userId }),
  });
  if (!res.ok) throw new Error('Voice processing failed');
  return res.json();
}

export async function scanReceiptOCR(): Promise<any> {
  const res = await fetch(`${API_BASE}/receipt/scan`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('OCR scanning failed');
  return res.json();
}

export async function fetchInsights(userId = 'demo_user'): Promise<Insight[]> {
  const res = await fetch(`${API_BASE}/insights?user_id=${userId}`);
  if (!res.ok) throw new Error('Failed to load insights');
  return res.json();
}

export async function resetDemoState(): Promise<any> {
  const res = await fetch(`${API_BASE}/demo/reset`, {
    method: 'POST',
  });
  return res.json();
}
