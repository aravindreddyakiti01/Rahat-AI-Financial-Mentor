import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class MemoryScreen extends StatefulWidget {
  const MemoryScreen({super.key});

  @override
  State<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends State<MemoryScreen> {
  List<MemoryItem> _timeline = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadTimeline();
  }

  void _loadTimeline() async {
    try {
      final list = await ApiService.getMemoryTimeline();
      setState(() {
        _timeline = list;
        _loading = false;
      });
    } catch (e) {
      setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Scaffold(
        backgroundColor: Color(0xFF0B0D11),
        body: Center(child: CircularProgressIndicator(color: Color(0xFF10B981))),
      );
    }

    return Scaffold(
      backgroundColor: const Color(0xFF0B0D11),
      appBar: AppBar(
        backgroundColor: const Color(0xFF13171F),
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Text("What Rahat Remembers", style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold)),
            Text("Hindsight Long-Term Memory", style: TextStyle(color: Color(0xFF38BDF8), fontSize: 11)),
          ],
        ),
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(14),
        itemCount: _timeline.length,
        itemBuilder: (context, index) {
          final mem = _timeline[index];
          final isOutcome = mem.type == 'outcome';
          final isFailed = mem.outcomeStatus == 'failed';

          return Container(
            margin: const EdgeInsets.only(bottom: 12),
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFF13171F),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(
                color: isOutcome
                    ? (isFailed ? const Color(0xFFF59E0B).withOpacity(0.4) : const Color(0xFF10B981).withOpacity(0.4))
                    : Colors.white10,
              ),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Colors.black38,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        mem.type.toUpperCase(),
                        style: TextStyle(
                          color: isOutcome ? (isFailed ? const Color(0xFFF59E0B) : const Color(0xFF10B981)) : const Color(0xFF38BDF8),
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                    Text(mem.date, style: const TextStyle(color: Colors.grey, fontSize: 11)),
                  ],
                ),
                const SizedBox(height: 8),
                Text(mem.title, style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold)),
                const SizedBox(height: 4),
                Text(mem.content, style: const TextStyle(color: Colors.white70, fontSize: 12, height: 1.3)),
              ],
            ),
          );
        },
      ),
    );
  }
}
