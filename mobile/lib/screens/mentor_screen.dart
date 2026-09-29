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
  final ScrollController _scrollController = ScrollController();

  final List<Map<String, dynamic>> _messages = [
    {
      'sender': 'rahat',
      'text': "Namaste Ramesh! I'm Rahat, your personal financial mentor. I remember your ₹4,500 bike loan EMI and your recent earning rhythms. How can I help you today?",
    }
  ];
  bool _isProcessing = false;
  String _lastSentMessage = '';

  final List<String> _quickPrompts = [
    "I need ₹4,500 for my EMI in 5 days. What should I do?",
    "I earned ₹950 today from delivery shifts",
    "I spent ₹250 on petrol",
    "How much have I saved so far for my bike goal?",
  ];

  @override
  void dispose() {
    _controller.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  void _sendMessage(String text) async {
    if (text.trim().isEmpty || _isProcessing) return;

    _lastSentMessage = text.trim();
    setState(() {
      _messages.add({'sender': 'user', 'text': text.trim()});
      _isProcessing = true;
    });
    _controller.clear();
    _scrollToBottom();

    try {
      final res = await ApiService.sendAgentMessage(text.trim());
      if (mounted) {
        setState(() {
          _messages.add({
            'sender': 'rahat',
            'text': res.text,
            'response': res,
          });
          _isProcessing = false;
        });
        _scrollToBottom();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _messages.add({
            'sender': 'rahat',
            'text': "Rahat couldn't connect right now. Your financial records are safe.",
            'isError': true,
          });
          _isProcessing = false;
        });
        _scrollToBottom();
      }
    }
  }

  void _retryLastMessage() {
    if (_lastSentMessage.isEmpty || _isProcessing) return;
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
      isScrollControlled: true,
      backgroundColor: const Color(0xFF13171F),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return Padding(
          padding: EdgeInsets.only(
            top: 20,
            left: 20,
            right: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 24,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: const [
                      Icon(Icons.auto_awesome, color: Color(0xFF10B981), size: 18),
                      SizedBox(width: 8),
                      Text(
                        "Why Rahat Gave This Advice",
                        style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 16),
                      ),
                    ],
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.grey, size: 20),
                    onPressed: () => Navigator.pop(ctx),
                  )
                ],
              ),
              const Divider(color: Colors.white10, height: 20),

              // Current Facts
              Row(
                children: const [
                  Icon(Icons.account_balance_wallet_outlined, color: Color(0xFF10B981), size: 15),
                  SizedBox(width: 6),
                  Text("Current Financial Facts (SQLite):", style: TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 13)),
                ],
              ),
              const SizedBox(height: 6),
              if (res.facts.isEmpty)
                const Text("No recent transaction constraints applied.", style: TextStyle(color: Colors.white54, fontSize: 12))
              else
                ...res.facts.map((f) => Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text("• $f", style: const TextStyle(color: Colors.white70, fontSize: 12)),
                )),

              const SizedBox(height: 14),

              // Experiential Memory
              Row(
                children: const [
                  Icon(Icons.psychology_outlined, color: Color(0xFF38BDF8), size: 15),
                  SizedBox(width: 6),
                  Text("Experiential Memory (Hindsight):", style: TextStyle(color: Color(0xFF38BDF8), fontWeight: FontWeight.bold, fontSize: 13)),
                ],
              ),
              const SizedBox(height: 6),
              if (res.whyThisAdvice.isEmpty)
                const Text("Formed from baseline pacing principles.", style: TextStyle(color: Colors.white54, fontSize: 12))
              else
                ...res.whyThisAdvice.map((w) => Padding(
                  padding: const EdgeInsets.only(bottom: 3),
                  child: Text("• $w", style: const TextStyle(color: Colors.white70, fontSize: 12)),
                )),

              if (res.primaryMemoryInfluence.isNotEmpty) ...[
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: const Color(0xFF0F2B36),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.3)),
                  ),
                  child: Text(
                    "Key Influence: ${res.primaryMemoryInfluence}",
                    style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 11, fontWeight: FontWeight.w600),
                  ),
                ),
              ],

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
              radius: 17,
              child: const Icon(Icons.psychology, color: Colors.white, size: 20),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: const [
                Text("Rahat", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
                Text("Outcome-Aware Financial Mentor", style: TextStyle(color: Color(0xFF10B981), fontSize: 11)),
              ],
            )
          ],
        ),
      ),
      body: Column(
        children: [
          // Chat message stream
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
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
                    constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.85),
                    padding: const EdgeInsets.all(13),
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
                          // Memory influence badge
                          if (res.primaryMemoryInfluence.isNotEmpty || res.memoriesUsedCount > 0) ...[
                            Container(
                              margin: const EdgeInsets.only(bottom: 6),
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF0F2B36),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(color: const Color(0xFF38BDF8).withOpacity(0.4)),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.psychology, color: Color(0xFF38BDF8), size: 12),
                                  const SizedBox(width: 4),
                                  Flexible(
                                    child: Text(
                                      res.primaryMemoryInfluence.isNotEmpty
                                          ? "Influenced by Hindsight: ${res.primaryMemoryInfluence}"
                                          : "Influenced by ${res.memoriesUsedCount} past experiences",
                                      style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 10, fontWeight: FontWeight.w600),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ],
                          // Why this advice button
                          InkWell(
                            onTap: () => _showWhyThisAdvice(res),
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: Colors.black26,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: const Color(0xFF10B981).withOpacity(0.3)),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  const Icon(Icons.auto_awesome, color: Color(0xFF10B981), size: 12),
                                  const SizedBox(width: 4),
                                  Text(
                                    "Why this advice? (${res.memoriesUsedCount} memories used)",
                                    style: const TextStyle(color: Color(0xFF10B981), fontSize: 11),
                                  ),
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

          // Processing progress indicator
          if (_isProcessing)
            Container(
              padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
              color: const Color(0xFF13171F),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: const [
                  SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF10B981)),
                    ),
                  ),
                  SizedBox(width: 10),
                  Text(
                    "Consulting Hindsight memory & financial state...",
                    style: TextStyle(color: Color(0xFF10B981), fontSize: 11, fontWeight: FontWeight.w500),
                  ),
                ],
              ),
            ),

          // Quick Prompt Suggestion Chips (Horizontal Scroll)
          Container(
            color: const Color(0xFF13171F),
            padding: const EdgeInsets.only(top: 8, bottom: 4, left: 10, right: 10),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _quickPrompts.map((prompt) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ActionChip(
                      backgroundColor: const Color(0xFF1A202C),
                      side: const BorderSide(color: Colors.white12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                      label: Text(prompt, style: const TextStyle(color: Colors.white70, fontSize: 11)),
                      onPressed: () => _sendMessage(prompt),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // Chat Input Bar
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
            color: const Color(0xFF13171F),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _controller,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _sendMessage,
                      style: const TextStyle(color: Colors.white, fontSize: 13),
                      decoration: InputDecoration(
                        hintText: "Ask Rahat about EMI, shifts, or expenses...",
                        hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                        filled: true,
                        fillColor: const Color(0xFF1A202C),
                        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                        border: OutlineInputBorder(borderRadius: BorderRadius.circular(20), borderSide: BorderSide.none),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  CircleAvatar(
                    backgroundColor: const Color(0xFF059669),
                    radius: 20,
                    child: IconButton(
                      icon: const Icon(Icons.send, color: Colors.white, size: 18),
                      onPressed: () => _sendMessage(_controller.text),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
