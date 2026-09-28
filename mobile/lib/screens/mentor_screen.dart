import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class MentorScreen extends StatefulWidget {
  const MentorScreen({super.key});

  @override
  State<MentorScreen> createState() => _MentorScreenState();
}

class _MentorScreenState extends State<MentorScreen> {
  final TextEditingController _controller = TextEditingController();
  final List<Map<String, dynamic>> _messages = [
    {
      'sender': 'rahat',
      'text': "Namaste Ramesh! I'm Rahat, your personal financial mentor. I remember your ₹4,500 bike loan EMI and your recent earning rhythms. How can I help you today?",
    }
  ];
  bool _isProcessing = false;
  String _lastSentMessage = '';

  void _sendMessage(String text) async {
    if (text.trim().isEmpty || _isProcessing) return;

    _lastSentMessage = text.trim();
    setState(() {
      _messages.add({'sender': 'user', 'text': text});
      _isProcessing = true;
    });
    _controller.clear();

    try {
      final res = await ApiService.sendAgentMessage(text);
      setState(() {
        _messages.add({
          'sender': 'rahat',
          'text': res.text,
          'response': res,
        });
        _isProcessing = false;
      });
    } catch (e) {
      setState(() {
        _messages.add({
          'sender': 'rahat',
          'text': "Rahat couldn't connect right now. Your records are safe.",
          'isError': true,
        });
        _isProcessing = false;
      });
    }
  }

  void _retryLastMessage() {
    if (_lastSentMessage.isEmpty || _isProcessing) return;
    // Remove the last error message before retrying
    setState(() {
      if (_messages.isNotEmpty && _messages.last['isError'] == true) {
        _messages.removeLast();
      }
    });
    _sendMessage(_lastSentMessage);
  }

  void _showWhyThisAdvice(StructuredAgentResponse res) {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF13171F),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    "Why Rahat Gave This Advice",
                    style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.grey),
                    onPressed: () => Navigator.pop(context),
                  )
                ],
              ),
              const SizedBox(height: 12),
              const Text("Current Financial Facts (SQLite):", style: TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.w600, fontSize: 13)),
              ...res.facts.map((f) => Text("• $f", style: const TextStyle(color: Colors.white70, fontSize: 12))),
              const SizedBox(height: 12),
              const Text("Experiential Memory (Hindsight):", style: TextStyle(color: Color(0xFF38BDF8), fontWeight: FontWeight.w600, fontSize: 13)),
              ...res.whyThisAdvice.map((w) => Text("• $w", style: const TextStyle(color: Colors.white70, fontSize: 12))),
              const SizedBox(height: 16),
            ],
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0D11),
      appBar: AppBar(
        backgroundColor: const Color(0xFF13171F),
        elevation: 0,
        title: Row(
          children: [
            CircleAvatar(
              backgroundColor: const Color(0xFF059669),
              radius: 16,
              child: const Icon(Icons.psychology, color: Colors.white, size: 18),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text("Rahat", style: TextStyle(color: Colors.white, fontSize: 15, fontWeight: FontWeight.bold)),
                Text("Outcome-Aware Mentor", style: TextStyle(color: Color(0xFF10B981), fontSize: 11)),
              ],
            )
          ],
        ),
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(14),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                final isUser = msg['sender'] == 'user';
                final StructuredAgentResponse? res = msg['response'];
                final bool isError = msg['isError'] == true;

                return Align(
                  alignment: isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 12),
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.8),
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: isUser
                          ? const Color(0xFF059669)
                          : isError
                              ? const Color(0xFF2D1B1B)
                              : const Color(0xFF161B24),
                      borderRadius: BorderRadius.circular(14),
                      border: isUser
                          ? null
                          : Border.all(
                              color: isError ? Colors.red.withOpacity(0.3) : Colors.white10,
                            ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          msg['text'],
                          style: TextStyle(
                            color: isError ? const Color(0xFFEF9A9A) : Colors.white,
                            fontSize: 13,
                            height: 1.4,
                          ),
                        ),
                        if (isError) ...[
                          const SizedBox(height: 8),
                          InkWell(
                            onTap: _retryLastMessage,
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                              decoration: BoxDecoration(
                                color: const Color(0xFF059669).withOpacity(0.2),
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: const Color(0xFF059669).withOpacity(0.4)),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: const [
                                  Icon(Icons.refresh, color: Color(0xFF10B981), size: 14),
                                  SizedBox(width: 4),
                                  Text("Retry", style: TextStyle(color: Color(0xFF10B981), fontSize: 12, fontWeight: FontWeight.w600)),
                                ],
                              ),
                            ),
                          ),
                        ],
                        if (res != null) ...[
                          const SizedBox(height: 8),
                          InkWell(
                            onTap: () => _showWhyThisAdvice(res),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black26,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.auto_awesome, color: Color(0xFF38BDF8), size: 12),
                                  const SizedBox(width: 4),
                                  Text("Why this advice? (${res.memoriesUsedCount} memories)", style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 11)),
                                ],
                              ),
                            ),
                          ),
                        ]
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          if (_isProcessing)
            Padding(
              padding: const EdgeInsets.all(8.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  SizedBox(
                    width: 12, height: 12,
                    child: CircularProgressIndicator(
                      strokeWidth: 1.5,
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF10B981)),
                    ),
                  ),
                  SizedBox(width: 8),
                  Text(
                    "Rahat is consulting Hindsight memory & financial facts...",
                    style: TextStyle(color: Color(0xFF10B981), fontSize: 11),
                  ),
                ],
              ),
            ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            color: const Color(0xFF13171F),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      decoration: InputDecoration(
                        hintText: "Ask about your EMI, income, or plan...",
                        hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                        filled: true,
                        fillColor: const Color(0xFF1A202C),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    icon: const Icon(Icons.send, color: Color(0xFF10B981)),
                    onPressed: () => _sendMessage(_controller.text),
                  )
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
