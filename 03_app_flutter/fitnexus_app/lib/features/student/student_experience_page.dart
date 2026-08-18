import 'package:flutter/material.dart';

import 'student_feedback_sheet.dart';
import 'student_workout_page.dart';

class StudentExperiencePage extends StatelessWidget {
  const StudentExperiencePage({super.key, this.token});

  final String? token;

  String _resolvedToken() {
    final String direct = (token ?? '').trim();
    if (direct.isNotEmpty) return direct;

    final String queryToken = (Uri.base.queryParameters['token'] ?? '').trim();
    if (queryToken.isNotEmpty) return queryToken;

    final String fragment = Uri.base.fragment;
    if (fragment.isEmpty) return '';
    final Uri? fragmentUri = Uri.tryParse(
      fragment.startsWith('/') ? fragment : '/$fragment',
    );
    return (fragmentUri?.queryParameters['token'] ?? '').trim();
  }

  Future<void> _openFeedback(BuildContext context, String accessToken) async {
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: const Color(0xFF080808),
      barrierColor: Colors.black.withValues(alpha: 0.78),
      builder: (_) => StudentFeedbackSheet(token: accessToken),
    );
  }

  @override
  Widget build(BuildContext context) {
    final String accessToken = _resolvedToken();

    return Stack(
      children: <Widget>[
        StudentWorkoutPage(token: accessToken),
        if (accessToken.isNotEmpty)
          Positioned(
            right: 18,
            bottom: 18,
            child: SafeArea(
              child: FloatingActionButton.extended(
                heroTag: 'fitnexus_student_feedback',
                onPressed: () => _openFeedback(context, accessToken),
                backgroundColor: const Color(0xFFE1B92F),
                foregroundColor: Colors.black,
                icon: const Icon(Icons.forum_rounded),
                label: const Text(
                  'Como foi o treino?',
                  style: TextStyle(fontWeight: FontWeight.w900),
                ),
              ),
            ),
          ),
      ],
    );
  }
}
