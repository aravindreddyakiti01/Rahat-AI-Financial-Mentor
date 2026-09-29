// ─── Goal ─────────────────────────────────────────────────────────────────────
class Goal {
  final String id;
  final String title;
  final double targetAmount;
  final double currentAmount;
  final String dueDate;
  final String category;
  final String status;
  final double remainingAmount;
  final int daysRemaining;
  final double progressPercentage;

  const Goal({
    required this.id,
    required this.title,
    required this.targetAmount,
    required this.currentAmount,
    required this.dueDate,
    required this.category,
    required this.status,
    required this.remainingAmount,
    required this.daysRemaining,
    required this.progressPercentage,
  });

  factory Goal.fromJson(Map<String, dynamic> json) {
    return Goal(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      targetAmount: (json['target_amount'] ?? 0).toDouble(),
      currentAmount: (json['current_amount'] ?? 0).toDouble(),
      dueDate: json['due_date'] ?? '',
      category: json['category'] ?? 'emi',
      status: json['status'] ?? 'active',
      remainingAmount: (json['remaining_amount'] ?? 0).toDouble(),
      daysRemaining: json['days_remaining'] ?? 0,
      progressPercentage: (json['progress_percentage'] ?? 0).toDouble(),
    );
  }
}

// ─── Obligation ───────────────────────────────────────────────────────────────
class Obligation {
  final String id;
  final String title;
  final double amount;
  final String frequency;
  final int dueDay;
  final String? nextDueDate;
  final String status;

  const Obligation({
    required this.id,
    required this.title,
    required this.amount,
    required this.frequency,
    required this.dueDay,
    this.nextDueDate,
    required this.status,
  });

  factory Obligation.fromJson(Map<String, dynamic> json) {
    return Obligation(
      id: json['id'] ?? '',
      title: json['title'] ?? '',
      amount: (json['amount'] ?? 0).toDouble(),
      frequency: json['frequency'] ?? 'monthly',
      dueDay: json['due_day'] ?? 10,
      nextDueDate: json['next_due_date'],
      status: json['status'] ?? 'active',
    );
  }
}

// ─── TransactionItem ──────────────────────────────────────────────────────────
class TransactionItem {
  final String id;
  final double amount;
  final String type; // 'income' or 'expense'
  final String category;
  final String description;
  final String note;
  final String merchant;
  final String date;
  final String source;

  const TransactionItem({
    required this.id,
    required this.amount,
    required this.type,
    required this.category,
    required this.description,
    required this.note,
    required this.merchant,
    required this.date,
    required this.source,
  });

  factory TransactionItem.fromJson(Map<String, dynamic> json) {
    return TransactionItem(
      id: json['id'] ?? '',
      amount: (json['amount'] ?? 0).toDouble(),
      type: json['type'] ?? 'income',
      category: json['category'] ?? '',
      description: json['description'] ?? '',
      note: json['note'] ?? '',
      merchant: json['merchant'] ?? '',
      date: json['date'] ?? '',
      source: json['source'] ?? 'manual',
    );
  }
}

// ─── FinanceSummary ───────────────────────────────────────────────────────────
class FinanceSummary {
  final String range;
  final double totalIncome;
  final double totalExpenses;
  final double netCashFlow;
  final double netAvailable;
  final double dailyAvgIncome;
  final Goal? activeGoal;
  final double goalProgressPercent;
  final List<Obligation> obligations;

  const FinanceSummary({
    required this.range,
    required this.totalIncome,
    required this.totalExpenses,
    required this.netCashFlow,
    required this.netAvailable,
    required this.dailyAvgIncome,
    this.activeGoal,
    required this.goalProgressPercent,
    required this.obligations,
  });

  factory FinanceSummary.fromJson(Map<String, dynamic> json) {
    return FinanceSummary(
      range: json['range'] ?? '7d',
      totalIncome: (json['total_income'] ?? 0).toDouble(),
      totalExpenses: (json['total_expenses'] ?? 0).toDouble(),
      netCashFlow: (json['net_cash_flow'] ?? 0).toDouble(),
      netAvailable: (json['net_available'] ?? 0).toDouble(),
      dailyAvgIncome: (json['daily_avg_income'] ?? 0).toDouble(),
      activeGoal: json['active_goal'] != null
          ? Goal.fromJson(json['active_goal'])
          : null,
      goalProgressPercent: (json['goal_progress_percent'] ?? 0).toDouble(),
      obligations: (json['obligations'] as List? ?? [])
          .map((o) => Obligation.fromJson(o))
          .toList(),
    );
  }
}

// ─── MemoryItem ───────────────────────────────────────────────────────────────
class MemoryItem {
  final String id;
  final String type;
  final String title;
  final String content;
  final String category;
  final String outcomeStatus;
  final String date;
  final List<String> tags;
  final String? relatedGoalId;
  final String? relatedPlanId;
  final double importance;
  final String source;

  const MemoryItem({
    required this.id,
    required this.type,
    required this.title,
    required this.content,
    required this.category,
    required this.outcomeStatus,
    required this.date,
    required this.tags,
    this.relatedGoalId,
    this.relatedPlanId,
    this.importance = 1.0,
    this.source = 'system',
  });

  factory MemoryItem.fromJson(Map<String, dynamic> json) {
    return MemoryItem(
      id: json['id'] ?? '',
      type: json['type'] ?? '',
      title: json['title'] ?? '',
      content: json['content'] ?? '',
      category: json['category'] ?? '',
      outcomeStatus: json['outcome_status'] ?? 'observed',
      date: json['date'] ?? '',
      tags: List<String>.from(json['relevance_tags'] ?? []),
      relatedGoalId: json['related_goal_id'],
      relatedPlanId: json['related_plan_id'],
      importance: (json['importance'] ?? 1.0).toDouble(),
      source: json['source'] ?? 'system',
    );
  }
}

// ─── StructuredAgentResponse ──────────────────────────────────────────────────
class StructuredAgentResponse {
  final String text;
  final List<String> facts;
  final String pattern;
  final String recommendation;
  final List<String> whyThisAdvice;
  final int memoriesUsedCount;
  final String primaryMemoryInfluence;

  const StructuredAgentResponse({
    required this.text,
    required this.facts,
    required this.pattern,
    required this.recommendation,
    required this.whyThisAdvice,
    required this.memoriesUsedCount,
    required this.primaryMemoryInfluence,
  });

  factory StructuredAgentResponse.fromJson(Map<String, dynamic> json) {
    return StructuredAgentResponse(
      text: json['text'] ?? '',
      facts: List<String>.from(json['facts'] ?? []),
      pattern: json['pattern'] ?? '',
      recommendation: json['recommendation'] ?? '',
      whyThisAdvice: List<String>.from(json['why_this_advice'] ?? []),
      memoriesUsedCount: json['memories_used_count'] ?? 0,
      primaryMemoryInfluence: json['primary_memory_influence'] ?? '',
    );
  }
}
