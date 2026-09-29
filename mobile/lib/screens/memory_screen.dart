import 'package:flutter/material.dart';
import '../services/api_service.dart';
import '../models/models.dart';

class MemoryScreen extends StatefulWidget {
  const MemoryScreen({super.key});

  @override
  State<MemoryScreen> createState() => _MemoryScreenState();
}

class _MemoryScreenState extends State<MemoryScreen> {
  List<MemoryItem> _allMemories = [];
  List<MemoryItem> _filteredMemories = [];
  bool _loading = true;
  String _errorMessage = '';
  
  String _searchQuery = '';
  String _selectedFilter = 'ALL'; // 'ALL', 'PLAN', 'OUTCOME', 'PATTERN', 'PROFILE_FACT', 'PREFERENCE'

  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _loadMemories();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadMemories() async {
    setState(() {
      _loading = true;
      _errorMessage = '';
    });

    try {
      final list = await ApiService.getMemoryTimeline();
      if (mounted) {
        setState(() {
          _allMemories = list;
          _applyFilters();
          _loading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString().replaceAll('ApiException', 'Error');
          _loading = false;
        });
      }
    }
  }

  void _applyFilters() {
    List<MemoryItem> result = List.from(_allMemories);

    // Filter by type if not ALL
    if (_selectedFilter != 'ALL') {
      final targetType = _selectedFilter.toLowerCase();
      result = result.where((m) => m.type.toLowerCase().replaceAll('_', '') == targetType.replaceAll('_', '')).toList();
    }

    // Filter by search query
    if (_searchQuery.trim().isNotEmpty) {
      final q = _searchQuery.trim().toLowerCase();
      result = result.where((m) {
        final titleMatch = m.title.toLowerCase().contains(q);
        final contentMatch = m.content.toLowerCase().contains(q);
        final categoryMatch = m.category.toLowerCase().contains(q);
        final tagMatch = m.tags.any((t) => t.toLowerCase().contains(q));
        return titleMatch || contentMatch || categoryMatch || tagMatch;
      }).toList();
    }

    setState(() {
      _filteredMemories = result;
    });
  }

  void _onSearchChanged(String val) {
    _searchQuery = val;
    _applyFilters();
  }

  void _onFilterSelected(String filterKey) {
    setState(() {
      _selectedFilter = filterKey;
      _applyFilters();
    });
  }

  void _confirmDelete(MemoryItem mem) {
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: const Color(0xFF13171F),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Color(0xFFF59E0B), size: 22),
            SizedBox(width: 8),
            Text("Delete Memory?", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
          ],
        ),
        content: Text(
          "Rahat will no longer consider this experience ('${mem.title}') when forming future financial recommendations.",
          style: const TextStyle(color: Colors.white70, fontSize: 13, height: 1.4),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text("Cancel", style: TextStyle(color: Colors.grey)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red.shade800,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onPressed: () async {
              Navigator.pop(ctx);
              await _deleteMemoryItem(mem.id);
            },
            child: const Text("Delete", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Future<void> _deleteMemoryItem(String memoryId) async {
    try {
      await ApiService.deleteMemory(memoryId: memoryId);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text("Memory deleted from Hindsight storage."),
            backgroundColor: Color(0xFF10B981),
            duration: Duration(seconds: 2),
          ),
        );
        _loadMemories();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text("Failed to delete memory: $e"),
            backgroundColor: Colors.red.shade800,
          ),
        );
      }
    }
  }

  void _showMemoryDetailModal(MemoryItem mem) {
    final typeColor = _getTypeColor(mem.type, mem.outcomeStatus);
    final typeIcon = _getTypeIcon(mem.type);

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
              // Modal top bar
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: typeColor.withOpacity(0.15),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: typeColor.withOpacity(0.4)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(typeIcon, color: typeColor, size: 14),
                        const SizedBox(width: 6),
                        Text(
                          mem.type.toUpperCase().replaceAll('_', ' '),
                          style: TextStyle(color: typeColor, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ],
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, color: Colors.grey, size: 20),
                    onPressed: () => Navigator.pop(ctx),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Title
              Text(
                mem.title,
                style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 6),
              // Date & Category row
              Row(
                children: [
                  const Icon(Icons.calendar_today_outlined, color: Colors.grey, size: 12),
                  const SizedBox(width: 4),
                  Text("Recorded ${mem.date}", style: const TextStyle(color: Colors.grey, fontSize: 12)),
                  const SizedBox(width: 12),
                  const Icon(Icons.label_outline, color: Color(0xFF38BDF8), size: 12),
                  const SizedBox(width: 4),
                  Text(mem.category.toUpperCase(), style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 12, fontWeight: FontWeight.w600)),
                ],
              ),
              const Divider(color: Colors.white10, height: 24),

              // Content / Narrative
              const Text("What Rahat Remembers:", style: TextStyle(color: Colors.grey, fontSize: 12, fontWeight: FontWeight.w600)),
              const SizedBox(height: 6),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF1A202C),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: Colors.white10),
                ),
                child: Text(
                  mem.content,
                  style: const TextStyle(color: Colors.white, fontSize: 13, height: 1.4),
                ),
              ),

              const SizedBox(height: 14),

              // Mentor Influence Card
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFF0D2818),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: const Color(0xFF10B981).withOpacity(0.3)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.psychology, color: Color(0xFF10B981), size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            "Used by Mentor",
                            style: TextStyle(color: Color(0xFF10B981), fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _getMentorInfluenceDescription(mem),
                            style: const TextStyle(color: Colors.white70, fontSize: 11, height: 1.3),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),

              // Related Plan/Goal if present
              if (mem.relatedPlanId != null || mem.relatedGoalId != null) ...[
                const SizedBox(height: 12),
                Row(
                  children: [
                    if (mem.relatedPlanId != null) ...[
                      Chip(
                        backgroundColor: Colors.black38,
                        label: Text("Plan: ${mem.relatedPlanId}", style: const TextStyle(color: Colors.white60, fontSize: 11)),
                        visualDensity: VisualDensity.compact,
                      ),
                      const SizedBox(width: 6),
                    ],
                    if (mem.relatedGoalId != null) ...[
                      Chip(
                        backgroundColor: Colors.black38,
                        label: Text("Goal: ${mem.relatedGoalId}", style: const TextStyle(color: Colors.white60, fontSize: 11)),
                        visualDensity: VisualDensity.compact,
                      ),
                    ],
                  ],
                ),
              ],

              // Relevance Tags
              if (mem.tags.isNotEmpty) ...[
                const SizedBox(height: 10),
                Wrap(
                  spacing: 6,
                  runSpacing: 4,
                  children: mem.tags.map((t) => Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.05),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: Colors.white12),
                    ),
                    child: Text("#$t", style: const TextStyle(color: Colors.grey, fontSize: 10)),
                  )).toList(),
                ),
              ],

              const SizedBox(height: 20),

              // Delete action button
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.red.shade400,
                    side: BorderSide(color: Colors.red.shade900.withOpacity(0.6)),
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  icon: const Icon(Icons.delete_outline, size: 18),
                  label: const Text("Delete This Memory", style: TextStyle(fontWeight: FontWeight.w600)),
                  onPressed: () {
                    Navigator.pop(ctx);
                    _confirmDelete(mem);
                  },
                ),
              ),
            ],
          ),
        );
      },
    );
  }

  String _getMentorInfluenceDescription(MemoryItem mem) {
    switch (mem.type.toLowerCase()) {
      case 'outcome':
        return "This real-world result guides Rahat to adjust daily savings targets when similar obligations arrive.";
      case 'pattern':
        return "Rahat uses this earning rhythm to balance weekday vs weekend target allocations.";
      case 'plan':
        return "This active/previous plan forms the baseline for tracking your saving progress.";
      case 'preference':
        return "Rahat respects your explicit preferences whenever structuring new financial pacing recommendations.";
      case 'profile_fact':
      default:
        return "Establishes your fundamental financial profile so advice fits your actual situation.";
    }
  }

  Color _getTypeColor(String type, String outcomeStatus) {
    switch (type.toLowerCase()) {
      case 'outcome':
        if (outcomeStatus == 'failed' || outcomeStatus == 'missed') {
          return const Color(0xFFF59E0B); // Amber warning
        }
        return const Color(0xFF10B981); // Emerald success
      case 'pattern':
        return const Color(0xFF10B981); // Emerald
      case 'plan':
        return const Color(0xFFA855F7); // Purple
      case 'preference':
        return const Color(0xFFEC4899); // Pink
      case 'profile_fact':
      default:
        return const Color(0xFF38BDF8); // Sky blue
    }
  }

  IconData _getTypeIcon(String type) {
    switch (type.toLowerCase()) {
      case 'outcome':
        return Icons.fact_check_outlined;
      case 'pattern':
        return Icons.trending_up;
      case 'plan':
        return Icons.event_note;
      case 'preference':
        return Icons.tune;
      case 'profile_fact':
      default:
        return Icons.person_outline;
    }
  }

  Widget _buildFilterChip(String label, String key) {
    final isSelected = _selectedFilter == key;
    return GestureDetector(
      onTap: () => _onFilterSelected(key),
      child: Container(
        margin: const EdgeInsets.only(right: 8),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFF10B981) : const Color(0xFF13171F),
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? const Color(0xFF10B981) : Colors.white12,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? Colors.white : Colors.grey,
            fontSize: 12,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0B0D11),
      appBar: AppBar(
        backgroundColor: const Color(0xFF13171F),
        elevation: 0,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: const [
            Text("What Rahat Remembers", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
            Text("Hindsight Experiential Long-Term Memory", style: TextStyle(color: Color(0xFF38BDF8), fontSize: 11)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF10B981)),
            tooltip: "Refresh Memory",
            onPressed: _loadMemories,
          ),
        ],
      ),
      body: Column(
        children: [
          // Search & Filter header section
          Container(
            padding: const EdgeInsets.all(12),
            color: const Color(0xFF13171F),
            child: Column(
              children: [
                // Search Input
                TextField(
                  controller: _searchController,
                  onChanged: _onSearchChanged,
                  style: const TextStyle(color: Colors.white, fontSize: 13),
                  decoration: InputDecoration(
                    hintText: "Search memories, outcomes, or tags...",
                    hintStyle: const TextStyle(color: Colors.grey, fontSize: 13),
                    prefixIcon: const Icon(Icons.search, color: Colors.grey, size: 18),
                    suffixIcon: _searchQuery.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, color: Colors.grey, size: 16),
                            onPressed: () {
                              _searchController.clear();
                              _onSearchChanged('');
                            },
                          )
                        : null,
                    filled: true,
                    fillColor: const Color(0xFF1A202C),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide.none,
                    ),
                  ),
                ),
                const SizedBox(height: 10),
                // Filter Chips Horizontal Scroll
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildFilterChip("All", "ALL"),
                      _buildFilterChip("Plans", "PLAN"),
                      _buildFilterChip("Outcomes", "OUTCOME"),
                      _buildFilterChip("Patterns", "PATTERN"),
                      _buildFilterChip("Profile", "PROFILE_FACT"),
                      _buildFilterChip("Preferences", "PREFERENCE"),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Main Content Body (Loading / Error / Empty / List)
          Expanded(
            child: _buildBody(),
          ),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_loading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(color: Color(0xFF10B981)),
            SizedBox(height: 14),
            Text("Loading Hindsight memories...", style: TextStyle(color: Colors.grey, fontSize: 13)),
          ],
        ),
      );
    }

    if (_errorMessage.isNotEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.cloud_off, color: Colors.redAccent, size: 48),
              const SizedBox(height: 14),
              const Text("Could Not Load Memories", style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 6),
              Text(_errorMessage, textAlign: TextAlign.center, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF059669),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                ),
                icon: const Icon(Icons.refresh, color: Colors.white, size: 16),
                label: const Text("Retry", style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                onPressed: _loadMemories,
              ),
            ],
          ),
        ),
      );
    }

    if (_filteredMemories.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Container(
                padding: const EdgeInsets.all(16),
                decoration: const BoxDecoration(
                  color: Color(0xFF13171F),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.psychology_outlined, color: Color(0xFF38BDF8), size: 40),
              ),
              const SizedBox(height: 16),
              Text(
                _searchQuery.isNotEmpty ? "No matching memories found" : "Rahat is building your memory",
                style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              Text(
                _searchQuery.isNotEmpty
                    ? "Try searching for another keyword or clear filters."
                    : "Rahat will remember your financial plans, real outcomes, and earning patterns as you use the mentor.",
                textAlign: TextAlign.center,
                style: const TextStyle(color: Colors.grey, fontSize: 13, height: 1.4),
              ),
            ],
          ),
        ),
      );
    }

    // Chronological Timeline view
    return ListView.builder(
      padding: const EdgeInsets.all(14),
      itemCount: _filteredMemories.length,
      itemBuilder: (context, index) {
        final mem = _filteredMemories[index];
        final typeColor = _getTypeColor(mem.type, mem.outcomeStatus);
        final typeIcon = _getTypeIcon(mem.type);
        final isLast = index == _filteredMemories.length - 1;

        return IntrinsicHeight(
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Timeline vertical line & indicator dot
              Column(
                children: [
                  Container(
                    width: 28,
                    height: 28,
                    decoration: BoxDecoration(
                      color: typeColor.withOpacity(0.15),
                      shape: BoxShape.circle,
                      border: Border.all(color: typeColor, width: 1.5),
                    ),
                    child: Icon(typeIcon, color: typeColor, size: 14),
                  ),
                  if (!isLast)
                    Expanded(
                      child: Container(
                        width: 2,
                        color: Colors.white10,
                        margin: const EdgeInsets.symmetric(vertical: 4),
                      ),
                    ),
                ],
              ),
              const SizedBox(width: 12),

              // Memory Card Content
              Expanded(
                child: GestureDetector(
                  onTap: () => _showMemoryDetailModal(mem),
                  child: Container(
                    margin: const EdgeInsets.only(bottom: 14),
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFF13171F),
                      borderRadius: BorderRadius.circular(14),
                      border: Border.all(
                        color: typeColor.withOpacity(0.3),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Card header: Type badge & Date
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: typeColor.withOpacity(0.15),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                mem.type.toUpperCase().replaceAll('_', ' '),
                                style: TextStyle(
                                  color: typeColor,
                                  fontSize: 10,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Row(
                              children: [
                                Text(mem.date, style: const TextStyle(color: Colors.grey, fontSize: 11)),
                                const SizedBox(width: 4),
                                const Icon(Icons.chevron_right, color: Colors.grey, size: 16),
                              ],
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),

                        // Title
                        Text(
                          mem.title,
                          style: const TextStyle(color: Colors.white, fontSize: 14, fontWeight: FontWeight.bold),
                        ),
                        const SizedBox(height: 4),

                        // Content preview
                        Text(
                          mem.content,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(color: Colors.white70, fontSize: 12, height: 1.3),
                        ),

                        const SizedBox(height: 10),

                        // Footer row: Category & Mentor link indicator
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(
                                color: Colors.black38,
                                borderRadius: BorderRadius.circular(4),
                              ),
                              child: Text(
                                mem.category.toUpperCase(),
                                style: const TextStyle(color: Color(0xFF38BDF8), fontSize: 9, fontWeight: FontWeight.w600),
                              ),
                            ),
                            Row(
                              children: const [
                                Icon(Icons.psychology, color: Color(0xFF10B981), size: 12),
                                SizedBox(width: 4),
                                Text("Used by Mentor", style: TextStyle(color: Color(0xFF10B981), fontSize: 10, fontWeight: FontWeight.w600)),
                              ],
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
