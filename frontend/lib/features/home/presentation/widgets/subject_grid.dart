import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SubjectGrid extends ConsumerWidget {
  const SubjectGrid({super.key});

  final List<Map<String, dynamic>> subjects = [
    {'name': 'Math', 'code': 'MATH', 'color': Colors.blue, 'icon': Icons.calculate},
    {'name': 'Chinese', 'code': 'CHIN', 'color': Colors.red, 'icon': Icons.language},
    {'name': 'Logic', 'code': 'LOGIC', 'color': Colors.purple, 'icon': Icons.lightbulb},
    {'name': 'Science', 'code': 'SCI', 'color': Colors.green, 'icon': Icons.science},
    {'name': 'Music', 'code': 'MUSIC', 'color': Colors.orange, 'icon': Icons.music_note},
    {'name': 'Art', 'code': 'ART', 'color': Colors.pink, 'icon': Icons.palette},
  ];

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return SliverPadding(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      sliver: SliverGrid(
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          mainAxisSpacing: 12,
          crossAxisSpacing: 12,
          childAspectRatio: 1.2,
        ),
        delegate: SliverChildBuilderDelegate(
          (context, index) {
            final subject = subjects[index];
            return _SubjectCard(
              name: subject['name'],
              code: subject['code'],
              color: subject['color'],
              icon: subject['icon'],
            );
          },
          childCount: subjects.length,
        ),
      ),
    );
  }
}

class _SubjectCard extends StatelessWidget {
  final String name;
  final String code;
  final Color color;
  final IconData icon;

  const _SubjectCard({
    required this.name,
    required this.code,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withOpacity(0.3), width: 2),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 48, color: color),
          const SizedBox(height: 8),
          Text(
            name,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                  color: color,
                ),
          ),
          Text(
            code,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: color.withOpacity(0.7),
                ),
          ),
        ],
      ),
    );
  }
}
