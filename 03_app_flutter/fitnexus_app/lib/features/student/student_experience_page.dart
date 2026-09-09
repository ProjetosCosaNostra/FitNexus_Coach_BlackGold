import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_floating_action.dart';
import 'student_feedback_sheet.dart';
import 'student_workout_page.dart';

class StudentExperiencePage extends StatelessWidget {
  const StudentExperiencePage({super.key, this.token});

  final String? token;

  String _resolvedToken() {
    final String direct = (token ?? '').trim();
    if (direct.isNotEmpty) return direct;

    // Student bearer tokens are intentionally accepted only from the URL
    // fragment. Fragments are not sent in HTTP requests and avoid leaking the
    // possession token through normal server logs/referrer query handling.
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
      backgroundColor: AppColors.cardRaised,
      barrierColor: AppColors.black.withValues(alpha: 0.78),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(
          top: Radius.circular(BlackGoldRadius.panel),
        ),
        side: BorderSide(
          color: AppColors.borderGold,
          width: BlackGoldStroke.hairline,
        ),
      ),
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
            right: BlackGoldSpace.md,
            bottom: BlackGoldSpace.md,
            child: SafeArea(
              child: FitFloatingAction(
                key: const ValueKey<String>('student-feedback-action'),
                heroTag: 'fitnexus_student_feedback',
                onTap: () => _openFeedback(context, accessToken),
                icon: Icons.forum_rounded,
                label: 'Como foi o treino?',
              ),
            ),
          ),
      ],
    );
  }
}
