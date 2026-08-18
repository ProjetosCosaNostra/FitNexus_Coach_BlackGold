import 'package:supabase_flutter/supabase_flutter.dart';

import '../auth/auth_service.dart';

class ProfessorFeedbackRecord {
  const ProfessorFeedbackRecord({
    required this.feedbackId,
    required this.sessionId,
    required this.studentId,
    required this.studentName,
    required this.planName,
    required this.perceivedExertion,
    required this.painScore,
    required this.energyScore,
    required this.riskSignal,
    required this.submittedAt,
    this.painLocation,
    this.note,
  });

  final String feedbackId;
  final String sessionId;
  final String studentId;
  final String studentName;
  final String planName;
  final int perceivedExertion;
  final int painScore;
  final int energyScore;
  final String riskSignal;
  final String? painLocation;
  final String? note;
  final DateTime submittedAt;

  factory ProfessorFeedbackRecord.fromJson(Map<String, dynamic> json) {
    return ProfessorFeedbackRecord(
      feedbackId: json['feedback_id'] as String? ?? '',
      sessionId: json['session_id'] as String? ?? '',
      studentId: json['student_id'] as String? ?? '',
      studentName: json['student_name'] as String? ?? 'Aluno',
      planName: json['plan_name'] as String? ?? 'Treino',
      perceivedExertion: (json['perceived_exertion'] as num?)?.toInt() ?? 0,
      painScore: (json['pain_score'] as num?)?.toInt() ?? 0,
      energyScore: (json['energy_score'] as num?)?.toInt() ?? 0,
      riskSignal: json['risk_signal'] as String? ?? 'low',
      painLocation: json['pain_location'] as String?,
      note: json['note'] as String?,
      submittedAt:
          DateTime.tryParse(json['submitted_at']?.toString() ?? '') ??
              DateTime.fromMillisecondsSinceEpoch(0),
    );
  }
}

class ProfessorFeedbackSnapshot {
  const ProfessorFeedbackSnapshot({
    required this.items,
    required this.generatedAt,
  });

  final List<ProfessorFeedbackRecord> items;
  final DateTime generatedAt;

  int get highSignals =>
      items.where((ProfessorFeedbackRecord item) => item.riskSignal == 'high').length;

  int get painAlerts =>
      items.where((ProfessorFeedbackRecord item) => item.painScore >= 7).length;

  factory ProfessorFeedbackSnapshot.fromJson(Map<String, dynamic> json) {
    final List<dynamic> rows = json['items'] as List<dynamic>? ?? const <dynamic>[];
    return ProfessorFeedbackSnapshot(
      items: rows
          .map(
            (dynamic row) => ProfessorFeedbackRecord.fromJson(
              row is Map<String, dynamic>
                  ? row
                  : Map<String, dynamic>.from(row as Map),
            ),
          )
          .toList(growable: false),
      generatedAt:
          DateTime.tryParse(json['generated_at']?.toString() ?? '') ?? DateTime.now(),
    );
  }
}

class ProfessorFeedbackRepository {
  ProfessorFeedbackRepository._();

  static final ProfessorFeedbackRepository instance =
      ProfessorFeedbackRepository._();

  SupabaseClient get _client => Supabase.instance.client;

  Future<ProfessorFeedbackSnapshot> fetchFeed() async {
    final String organizationId =
        await AuthService.instance.ensureProfessorOrganization();

    final dynamic response = await _client.rpc(
      'get_professor_feedback_feed',
      params: <String, dynamic>{'p_organization_id': organizationId},
    );

    final Map<String, dynamic> json = response is Map<String, dynamic>
        ? response
        : Map<String, dynamic>.from(response as Map);
    return ProfessorFeedbackSnapshot.fromJson(json);
  }
}
