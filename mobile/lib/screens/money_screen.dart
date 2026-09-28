import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class MoneyScreen extends StatefulWidget {
  const MoneyScreen({super.key});

  @override
  State<MoneyScreen> createState() => _MoneyScreenState();
}

class _MoneyScreenState extends State<MoneyScreen> {
  FinanceSummary? _summary;
  List<TransactionItem> _transactions = [];
  bool _loading = true;
  String? _errorMessage;
  String _selectedRange = '7d';

  static const _accentGreen = Color(0xFF10B981);
  static const _accentAmber = Color(0xFFF59E0B);
  static const _accentBlue = Color(0xFF38BDF8);
  static const _surface = Color(0xFF13171F);
  static const _background = Color(0xFF0B0D11);

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final summary = await ApiService.getFinanceSummary(range: _selectedRange);
      final txs = await ApiService.getTransactions();
      setState(() {
        _summary = summary;
        _transactions = txs;
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _errorMessage = 'Backend error ${e.statusCode}: ${e.message}';
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _errorMessage = 'Could not connect to Rahat server. Is the backend running?';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _background,
      appBar: AppBar(
        backgroundColor: _surface,
        title: const Text(
          'Money & Obligations',
          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white70),
            onPressed: _loadData,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircularProgressIndicator(color: _accentGreen),
            SizedBox(height: 12),
            Text('Loading financial data…', style: TextStyle(color: Colors.white54, fontSize: 13)),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.cloud_off, color: Colors.white30, size: 48),
              const SizedBox(height: 14),
              Text(
                _errorMessage!,
                style: const TextStyle(color: Colors.white54, fontSize: 13),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 20),
              ElevatedButton.icon(
                onPressed: _loadData,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(backgroundColor: _accentGreen),
              ),
            ],
          ),
        ),
      );
    }

    if (_summary == null && _transactions.isEmpty) {
      return Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.account_balance_wallet_outlined, color: Colors.white24, size: 52),
            const SizedBox(height: 14),
            const Text('No financial data yet', style: TextStyle(color: Colors.white54, fontSize: 14)),
            const SizedBox(height: 6),
            const Text('Add income or expense to get started.', style: TextStyle(color: Colors.white30, fontSize: 12)),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _loadData,
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Refresh'),
              style: ElevatedButton.styleFrom(backgroundColor: _accentGreen),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadData,
      color: _accentGreen,
      backgroundColor: _surface,
      child: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          _buildRangeToggle(),
          const SizedBox(height: 14),
          _buildSummaryCards(),
          const SizedBox(height: 16),
          if (_summary?.activeGoal != null) ...[
            _buildGoalCard(_summary!.activeGoal!),
            const SizedBox(height: 16),
          ],
          if (_summary != null && _summary!.obligations.isNotEmpty) ...[
            _buildSectionHeader('Fixed Obligations'),
            const SizedBox(height: 8),
            ..._summary!.obligations.map(_buildObligationRow),
            const SizedBox(height: 16),
          ],
          _buildSectionHeader('Recent Transactions'),
          const SizedBox(height: 8),
          if (_transactions.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 20),
              child: Center(
                child: Text('No transactions found', style: TextStyle(color: Colors.white38, fontSize: 13)),
              ),
            )
          else
            ..._transactions.map(_buildTransactionRow),
        ],
      ),
    );
  }

  // ─── Range Toggle ──────────────────────────────────────────────────────────

  Widget _buildRangeToggle() {
    const ranges = [
      ('today', 'Today'),
      ('7d', '7 Days'),
      ('month', 'Month'),
    ];
    return Row(
      children: ranges.map((r) {
        final selected = _selectedRange == r.$1;
        return Padding(
          padding: const EdgeInsets.only(right: 8),
          child: GestureDetector(
            onTap: () {
              if (_selectedRange != r.$1) {
                setState(() => _selectedRange = r.$1);
                _loadData();
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
              decoration: BoxDecoration(
                color: selected ? _accentGreen.withOpacity(0.2) : _surface,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: selected ? _accentGreen : Colors.white10,
                ),
              ),
              child: Text(
                r.$2,
                style: TextStyle(
                  color: selected ? _accentGreen : Colors.white54,
                  fontSize: 12,
                  fontWeight: selected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  // ─── Summary Cards ─────────────────────────────────────────────────────────

  Widget _buildSummaryCards() {
    final s = _summary;
    if (s == null) return const SizedBox.shrink();
    return Row(
      children: [
        _statCard('Income', '₹${s.totalIncome.toStringAsFixed(0)}', _accentGreen),
        const SizedBox(width: 8),
        _statCard('Expenses', '₹${s.totalExpenses.toStringAsFixed(0)}', _accentAmber),
        const SizedBox(width: 8),
        _statCard('Net', '₹${s.netAvailable.toStringAsFixed(0)}', _accentBlue),
      ],
    );
  }

  Widget _statCard(String title, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: _surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: Colors.white10),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(color: Colors.grey, fontSize: 10)),
            const SizedBox(height: 6),
            Text(value, style: TextStyle(color: color, fontSize: 15, fontWeight: FontWeight.bold)),
          ],
        ),
      ),
    );
  }

  // ─── Goal Card ──────────────────────────────────────────────────────────────

  Widget _buildGoalCard(Goal goal) {
    final pct = goal.progressPercentage.clamp(0.0, 100.0) / 100;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: _accentAmber.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Text(
                  goal.title,
                  style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _accentAmber.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '${goal.daysRemaining}d left',
                  style: const TextStyle(color: _accentAmber, fontSize: 11, fontWeight: FontWeight.bold),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: pct,
              backgroundColor: Colors.white10,
              valueColor: const AlwaysStoppedAnimation<Color>(_accentAmber),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '₹${goal.currentAmount.toStringAsFixed(0)} of ₹${goal.targetAmount.toStringAsFixed(0)} (${goal.progressPercentage.toStringAsFixed(0)}%)',
                style: const TextStyle(color: Colors.white70, fontSize: 11),
              ),
              Text(
                '₹${goal.remainingAmount.toStringAsFixed(0)} to go',
                style: const TextStyle(color: _accentAmber, fontSize: 11, fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ],
      ),
    );
  }

  // ─── Obligation Row ────────────────────────────────────────────────────────

  Widget _buildObligationRow(Obligation obl) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(obl.title, style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500)),
              const SizedBox(height: 2),
              Text(
                'Due: ${obl.nextDueDate ?? 'Day ${obl.dueDay}'} · ${obl.frequency}',
                style: const TextStyle(color: Colors.grey, fontSize: 11),
              ),
            ],
          ),
          Text(
            '₹${obl.amount.toStringAsFixed(0)}',
            style: const TextStyle(color: _accentAmber, fontSize: 14, fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  // ─── Transaction Row ───────────────────────────────────────────────────────

  Widget _buildTransactionRow(TransactionItem tx) {
    final isInc = tx.type == 'income';
    final label = tx.description.isNotEmpty ? tx.description : tx.category;
    final subtitle = [
      tx.date,
      tx.category,
      if (tx.merchant.isNotEmpty) tx.merchant,
    ].join(' · ');

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: Colors.white10),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.w500),
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 3),
                Text(subtitle, style: const TextStyle(color: Colors.grey, fontSize: 11)),
                if (tx.note.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 3),
                    child: Text('📝 ${tx.note}', style: const TextStyle(color: Colors.white38, fontSize: 11)),
                  ),
              ],
            ),
          ),
          const SizedBox(width: 12),
          Text(
            '${isInc ? '+' : '-'}₹${tx.amount.toStringAsFixed(0)}',
            style: TextStyle(
              color: isInc ? _accentGreen : Colors.white,
              fontWeight: FontWeight.bold,
              fontSize: 14,
            ),
          ),
        ],
      ),
    );
  }

  // ─── Section Header ────────────────────────────────────────────────────────

  Widget _buildSectionHeader(String title) {
    return Text(
      title,
      style: const TextStyle(color: Colors.white70, fontWeight: FontWeight.bold, fontSize: 14),
    );
  }
}
