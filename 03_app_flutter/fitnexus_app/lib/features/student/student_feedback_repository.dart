import 'student_access_command_id.dart';
import 'student_access_transport.dart';

class StudentFeedbackContext {
  const StudentFeedbackContext({
    required this.eligible,
    required this.submitted,
    this.reason,
    this.sessionId,
    this.planName,
    this.completedAt,
    this.perceivedExertion,
    this.painScore,
    this.energyScore,
    this.painLocation,
    this.note,
    this.submittedAt,
  });

  final bool eligible;
  final bool submitted;
  final String? reason;
  final String? sessionId;
  final String? planName;
  final DateTime? completedAt;
  final int? perceivedExertion;
  final int? painScore;
  final int? energyScore;
  final String? painLocation;
  final String? note;
  final DateTime? submittedAt;

  factory StudentFeedbackContext.fromJson(Map<String, dynamic> json) {
    final Map<String, dynamic> feedback = _map(json['feedback']);
    return StudentFeedbackContext(
      eligible: json['eligible'] as bool? ?? false,
      submitted: json['submitted'] as bool? ?? false,
      reason: json['reason'] as String?,
      sessionId: json['session_id'] as String?,
      planName: json['plan_name'] as String?,
      completedAt: _dateTime(json['completed_at']),
      perceivedExertion: (feedback['perceived_exertion'] as num?)?.toInt(),
      painScore: (feedback['pain_score'] as num?)?.toInt(),
      energyScore: (feedback['energy_score'] as num?)?.toInt(),
      painLocation: feedback['pain_location'] as String?,
      note: feedback['note'] as String?,
      submittedAt: _dateTime(feedback['submitted_at']),
    );
  }
}

class StudentFeedbackResult {
  const StudentFeedbackResult({
    required this.submitted,
    required this.riskSignal,
  });

  final bool submitted;
  final String riskSignal;

  factory StudentFeedbackResult.fromJson(Map<String, dynamic> json) {
    return StudentFeedbackResult(
      submitted: json['submitted'] as bool? ?? false,
      riskSignal: json['risk_signal'] as String? ?? 'low',
    );
  }
}

class StudentFeedbackRepository {
  StudentFeedbackRepository._();

  static final StudentFeedbackRepository instance = StudentFeedbackRepository._();

  Future<StudentFeedbackContext> fetchContext(String token) async {
    final String normalizedToken = token.trim();
    final dynamic response = await StudentAccessTransport.instance.invoke(
      action: 'get_feedback_context',
      directParams: <String, dynamic>{'p_token': normalizedToken},
      edgePayload: <String, dynamic>{'token': normalizedToken},
    );
    final Map<String, dynamic> result = _map(response);
    _throwStudentAccessError(result);
    return StudentFeedbackContext.fromJson(result);
  }

  Future<StudentFeedbackResult> submit({
    required String token,
    required String sessionId,
    required int perceivedExertion,
    required int painScore,
    required int energyScore,
    String? painLocation,
    String? note,
  }) async {
    final String normalizedToken = token.trim();
    final String commandId = newStudentAccessCommandId();
    final String? normalizedPainLocation = _nullable(painLocation);
    final String? normalizedNote = _nullable(note);
    final dynamic response = await StudentAccessTransport.instance.invoke(
      action: 'submit_feedback',
      directParams: <String, dynamic>{
        'p_token': normalizedToken,
        'p_session_id': sessionId,
        'p_perceived_exertion': perceivedExertion,
        'p_pain_score': painScore,
        'p_energy_score': energyScore,
        'p_pain_location': normalizedPainLocation,
        'p_note': normalizedNote,
        'p_command_id': commandId,
      },
      edgePayload: <String, dynamic>{
        'token': normalizedToken,
        'session_id': sessionId,
        'perceived_exertion': perceivedExertion,
        'pain_score': painScore,
        'energy_score': energyScore,
        'pain_location': normalizedPainLocation,
        'note': normalizedNote,
        'command_id': commandId,
      },
    );
    final Map<String, dynamic> result = _map(response);
    _throwStudentAccessError(result);
    return StudentFeedbackResult.fromJson(result);
  }
}

void _throwStudentAccessError(Map<String, dynamic> value) {
  final String code = value['error']?.toString() ?? '';
  if (code.isEmpty) return;

  switch (code) {
    case 'STUDENT_ACCESS_INVALID':
      throw StateError('Este link de aluno é inválido, expirou ou foi substituído.');
    case 'STUDENT_ACCESS_RATE_LIMITED':
      throw StateError('Muitas ações em pouco tempo. Aguarde alguns segundos e tente novamente.');
    case 'STUDENT_COMMAND_IN_PROGRESS':
      throw StateError('Este feedback ainda está sendo confirmado. Tente novamente em instantes.');
    case 'STUDENT_COMMAND_ID_INVALID':
      throw StateError('A proteção do feedback recusou um identificador inválido.');
    default:
      throw StateError('O acesso do aluno foi recusado pelo limite de segurança: $code');
  }
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

DateTime? _dateTime(dynamic value) {
  if (value == null) return null;
  return DateTime.tryParse(value.toString());
}

String? _nullable(String? value) {
  final String normalized = (value ?? '').trim();
  return normalized.isEmpty ? null : normalized;
}
