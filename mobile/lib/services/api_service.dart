import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/models.dart';

// Custom exception for structured API errors
class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException(this.statusCode, this.message);

  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiService {
  /// Standard Android Emulator → Host loopback address.
  /// Change to 'http://localhost:8000' if running on desktop/web.
  static const String baseUrl = 'http://10.0.2.2:8000';

  // ─── Internal helpers ──────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> _get(String path) async {
    final res = await http.get(Uri.parse('$baseUrl$path'));
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final res = await http.post(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (res.statusCode == 200 || res.statusCode == 201) {
      return jsonDecode(res.body);
    }
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<Map<String, dynamic>> _patch(
    String path,
    Map<String, dynamic> body,
  ) async {
    final res = await http.patch(
      Uri.parse('$baseUrl$path'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode(body),
    );
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<Map<String, dynamic>> _delete(String path) async {
    final res = await http.delete(Uri.parse('$baseUrl$path'));
    if (res.statusCode == 200) return jsonDecode(res.body);
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static String _extractDetail(String body) {
    try {
      final decoded = jsonDecode(body);
      return decoded['detail']?.toString() ?? body;
    } catch (_) {
      return body;
    }
  }

  // ─── Finance ───────────────────────────────────────────────────────────────

  /// Fetch financial summary. range: 'today' | '7d' | 'month'
  static Future<FinanceSummary> getFinanceSummary({
    String userId = 'demo_user',
    String range = '7d',
  }) async {
    final data = await _get('/finance/summary?user_id=$userId&range=$range');
    return FinanceSummary.fromJson(data);
  }

  static Future<List<TransactionItem>> getTransactions({
    String userId = 'demo_user',
    int limit = 20,
  }) async {
    final res = await http.get(
      Uri.parse('$baseUrl/finance/transactions?user_id=$userId&limit=$limit'),
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => TransactionItem.fromJson(e)).toList();
    }
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<TransactionItem> addIncome({
    required String userId,
    required double amount,
    required String category,
    String description = '',
    String note = '',
    String? date,
  }) async {
    final data = await _post('/finance/income?user_id=$userId', {
      'amount': amount,
      'category': category,
      'description': description,
      'note': note,
      if (date != null) 'date': date,
    });
    return TransactionItem.fromJson(data);
  }

  static Future<TransactionItem> addExpense({
    required String userId,
    required double amount,
    required String category,
    String description = '',
    String note = '',
    String merchant = '',
    String? date,
  }) async {
    final data = await _post('/finance/expense?user_id=$userId', {
      'amount': amount,
      'category': category,
      'description': description,
      'note': note,
      'merchant': merchant,
      if (date != null) 'date': date,
    });
    return TransactionItem.fromJson(data);
  }

  static Future<void> deleteTransaction({
    required String userId,
    required String txId,
  }) async {
    await _delete('/finance/transactions/$txId?user_id=$userId');
  }

  // ─── Goals ─────────────────────────────────────────────────────────────────

  static Future<List<Goal>> getGoals({
    String userId = 'demo_user',
    String? status,
  }) async {
    final suffix = status != null ? '&status=$status' : '';
    final res = await http.get(
      Uri.parse('$baseUrl/goals?user_id=$userId$suffix'),
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => Goal.fromJson(e)).toList();
    }
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<Goal> createGoal({
    required String userId,
    required String title,
    required double targetAmount,
    required String dueDate,
    String category = 'emi',
    double initialAmount = 0.0,
  }) async {
    final data = await _post('/goals?user_id=$userId', {
      'title': title,
      'target_amount': targetAmount,
      'due_date': dueDate,
      'category': category,
      'initial_amount': initialAmount,
    });
    return Goal.fromJson(data);
  }

  static Future<Goal> updateGoal({
    required String userId,
    required String goalId,
    double? amountToAdd,
    double? newCurrentAmount,
    String? status,
  }) async {
    final body = <String, dynamic>{};
    if (amountToAdd != null) body['amount_to_add'] = amountToAdd;
    if (newCurrentAmount != null) body['new_current_amount'] = newCurrentAmount;
    if (status != null) body['status'] = status;
    final data = await _patch('/goals/$goalId?user_id=$userId', body);
    return Goal.fromJson(data);
  }

  // ─── Obligations ──────────────────────────────────────────────────────────

  static Future<List<Obligation>> getObligations({
    String userId = 'demo_user',
  }) async {
    final res = await http.get(
      Uri.parse('$baseUrl/goals/obligations/list?user_id=$userId'),
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => Obligation.fromJson(e)).toList();
    }
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<Obligation> createObligation({
    required String userId,
    required String title,
    required double amount,
    String frequency = 'monthly',
    int dueDay = 10,
    String? nextDueDate,
  }) async {
    final data = await _post('/goals/obligations?user_id=$userId', {
      'title': title,
      'amount': amount,
      'frequency': frequency,
      'due_day': dueDay,
      if (nextDueDate != null) 'next_due_date': nextDueDate,
    });
    return Obligation.fromJson(data);
  }

  // ─── Memory ────────────────────────────────────────────────────────────────

  static Future<List<MemoryItem>> getMemoryTimeline({
    String userId = 'demo_user',
  }) async {
    final res = await http.get(
      Uri.parse('$baseUrl/memory/timeline?user_id=$userId'),
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => MemoryItem.fromJson(e)).toList();
    }
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<List<MemoryItem>> searchMemories({
    String userId = 'demo_user',
    String query = '',
    String? category,
    int limit = 10,
  }) async {
    final catParam = category != null && category.isNotEmpty ? '&category=$category' : '';
    final res = await http.get(
      Uri.parse('$baseUrl/memory/search?user_id=$userId&query=${Uri.encodeComponent(query)}$catParam&limit=$limit'),
    );
    if (res.statusCode == 200) {
      final List list = jsonDecode(res.body);
      return list.map((e) => MemoryItem.fromJson(e)).toList();
    }
    throw ApiException(res.statusCode, _extractDetail(res.body));
  }

  static Future<MemoryItem> getMemoryDetail({
    required String memoryId,
    String userId = 'demo_user',
  }) async {
    final data = await _get('/memory/$memoryId?user_id=$userId');
    return MemoryItem.fromJson(data);
  }

  static Future<void> deleteMemory({
    required String memoryId,
    String userId = 'demo_user',
  }) async {
    await _delete('/memory/$memoryId?user_id=$userId');
  }

  static Future<List<Map<String, dynamic>>> getMemoryCategories() async {
    final data = await _get('/memory/categories');
    final List list = data['categories'] ?? [];
    return list.cast<Map<String, dynamic>>();
  }

  // ─── Agent ─────────────────────────────────────────────────────────────────

  static Future<StructuredAgentResponse> sendAgentMessage(
    String message, {
    String userId = 'demo_user',
  }) async {
    final data = await _post(
      '/agent/chat',
      {'message': message, 'user_id': userId},
    );
    return StructuredAgentResponse.fromJson(data);
  }

  // ─── Insights ──────────────────────────────────────────────────────────────

  static Future<Map<String, dynamic>> getInsights({
    String userId = 'demo_user',
  }) async {
    return _get('/insights?user_id=$userId');
  }

  // ─── Demo ──────────────────────────────────────────────────────────────────

  static Future<void> resetDemo() async {
    await http.post(Uri.parse('$baseUrl/demo/reset'));
  }
}
