import 'package:flutter/material.dart';
import '../services/api_service.dart';

class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  Map<String, dynamic>? _insights;
  bool _loading = true;
  String? _errorMessage;

  static const _accentGreen = Color(0xFF10B981);
  static const _accentAmber = Color(0xFFF59E0B);
  static const _accentBlue = Color(0xFF38BDF8);
  static const _accentPurple = Color(0xFFA78BFA);
  static const _surface = Color(0xFF13171F);
  static const _background = Color(0xFF0B0D11);

  @override
  void initState() {
    super.initState();
    _loadInsights();
  }

  Future<void> _loadInsights() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final data = await ApiService.getInsights();
      setState(() {
        _insights = data;
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
          'Grounded Insights',
          style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white70),
            onPressed: _loadInsights,
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
            Text('Calculating insights…', style: TextStyle(color: Colors.white54, fontSize: 13)),
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
                onPressed: _loadInsights,
                icon: const Icon(Icons.refresh, size: 16),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(backgroundColor: _accentGreen),
              ),
            ],
          ),
        ),
      );
    }

    if (_insights == null || _insights!.isEmpty) {
      return const Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.insights_outlined, color: Colors.white24, size: 52),
            SizedBox(height: 14),
            Text('No insights available yet', style: TextStyle(color: Colors.white54, fontSize: 14)),
            SizedBox(height: 6),
            Text('Add transactions to see your patterns.', style: TextStyle(color: Colors.white30, fontSize: 12)),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadInsights,
      color: _accentGreen,
      backgroundColor: _surface,
      child: ListView(
        padding: const EdgeInsets.all(14),
        children: [
          _buildInsightFromData(),
        ],
      ),
    );
  }

  Widget _buildInsightFromData() {
    final data = _insights!;

    final List<Widget> cards = [];

    // Weekend surge insight
    final weekendIncome = (data['weekend_income_7d'] ?? 0).toDouble();
    final totalIncome = (data['total_income_7d'] ?? 0).toDouble();
    if (totalIncome > 0 && weekendIncome > 0) {
      final pct = ((weekendIncome / totalIncome) * 100).round();
      cards.add(_insightCard(
        title: 'Weekend Surge Advantage',
        description:
            'Weekend earnings contributed $pct% of your 7-day total income. '
            'Saturday and Sunday shifts generate higher returns per hour.',
        metric: '₹${weekendIncome.toStringAsFixed(0)} on Sat-Sun',
        color: _accentGreen,
        icon: Icons.trending_up,
      ));
      cards.add(const SizedBox(height: 12));
    }

    // Fuel efficiency / biggest expense category
    final categoryBreakdown = data['expense_category_breakdown_7d'] as Map<String, dynamic>? ?? {};
    if (categoryBreakdown.isNotEmpty) {
      final topCat = categoryBreakdown.entries.reduce((a, b) => a.value > b.value ? a : b);
      final topCatAmount = (topCat.value as num).toDouble();
      final totalExpenses = (data['total_expenses_7d'] ?? 0).toDouble();
      final expPct = totalExpenses > 0 ? ((topCatAmount / totalExpenses) * 100).round() : 0;
      cards.add(_insightCard(
        title: '${topCat.key} Spend Track',
        description:
            '${topCat.key} represents ₹${topCatAmount.toStringAsFixed(0)} ($expPct%) '
            'of your operating costs over the last 7 days.',
        metric: '₹${topCatAmount.toStringAsFixed(0)} ${topCat.key}',
        color: _accentBlue,
        icon: Icons.local_gas_station_outlined,
      ));
      cards.add(const SizedBox(height: 12));
    }

    // Goal progress
    final goalRemaining = (data['goal_remaining_amount'] ?? 0).toDouble();
    final goalDaysLeft = data['goal_days_remaining'] ?? 0;
    final goalTitle = data['active_goal_title'] as String? ?? '';
    if (goalRemaining > 0 && goalTitle.isNotEmpty) {
      cards.add(_insightCard(
        title: '$goalTitle Pace',
        description:
            'You are ₹${goalRemaining.toStringAsFixed(0)} away from your target '
            'with $goalDaysLeft days remaining.',
        metric: '₹${goalRemaining.toStringAsFixed(0)} remaining',
        color: _accentAmber,
        icon: Icons.flag_outlined,
      ));
      cards.add(const SizedBox(height: 12));
    }

    // Daily average
    final dailyAvg = (data['daily_avg_income_7d'] ?? 0).toDouble();
    if (dailyAvg > 0) {
      cards.add(_insightCard(
        title: 'Daily Earning Pace',
        description:
            'Your 7-day daily average is ₹${dailyAvg.toStringAsFixed(0)}. '
            'On track days are your highest-value shifts.',
        metric: '₹${dailyAvg.toStringAsFixed(0)}/day avg',
        color: _accentPurple,
        icon: Icons.bar_chart,
      ));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: cards.isEmpty
          ? [
              const Center(
                child: Text(
                  'Add more transactions to see patterns.',
                  style: TextStyle(color: Colors.white38, fontSize: 13),
                ),
              ),
            ]
          : cards,
    );
  }

  Widget _insightCard({
    required String title,
    required String description,
    required String metric,
    required Color color,
    required IconData icon,
  }) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _surface,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white10),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.15),
                  borderRadius: BorderRadius.circular(6),
                  border: Border.all(color: color.withOpacity(0.3)),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(icon, color: color, size: 11),
                    const SizedBox(width: 4),
                    Text(
                      metric,
                      style: TextStyle(color: color, fontSize: 11, fontWeight: FontWeight.bold),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(title, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(description, style: const TextStyle(color: Colors.white70, fontSize: 12, height: 1.3)),
        ],
      ),
    );
  }
}
