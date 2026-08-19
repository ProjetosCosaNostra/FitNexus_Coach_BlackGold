import 'package:fitnexus_app/features/professor/professor_engine_lab_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('engine lab snapshot preserves champion challenger and promotion gate', () {
    final DecisionEngineLabSnapshot snapshot =
        DecisionEngineLabSnapshot.fromJson(<String, dynamic>{
      'champion': <String, dynamic>{
        'engine_version': 'blackgold_deterministic_v1',
        'role': 'champion',
        'lifecycle': 'active',
        'description': 'Motor de produção',
      },
      'challengers': <Map<String, dynamic>>[
        <String, dynamic>{
          'engine_version': 'blackgold_deterministic_v1_1_shadow',
          'role': 'challenger',
          'lifecycle': 'lab_only',
          'description': 'Motor sombra',
        },
      ],
      'latest_evaluation': <String, dynamic>{
        'evaluation_run_id': 'eval-13',
        'challenger_version': 'blackgold_deterministic_v1_1_shadow',
        'status': 'blocked_insufficient_evidence',
        'case_count': 8,
        'resolved_count': 4,
        'champion_alignment_rate': 75,
        'challenger_alignment_rate': 75,
        'alignment_uplift': 0,
        'recommendation_changes': 2,
        'risk_changes': 1,
        'safety_downgrades': 0,
        'unsafe_actionability_conflicts': 0,
        'created_at': '2026-08-18T22:20:00Z',
      },
      'promotion_packet': <String, dynamic>{
        'gate_status': 'blocked_insufficient_evidence',
      },
      'shadow_only': true,
      'production_engine_unchanged': true,
      'auto_activation': false,
    });

    expect(snapshot.champion!.version, 'blackgold_deterministic_v1');
    expect(snapshot.champion!.lifecycle, 'active');
    expect(snapshot.challengers.single.lifecycle, 'lab_only');
    expect(snapshot.latestEvaluation!.caseCount, 8);
    expect(snapshot.latestEvaluation!.resolvedCount, 4);
    expect(snapshot.latestEvaluation!.safetyPassed, isTrue);
    expect(
      snapshot.promotionGateStatus,
      'blocked_insufficient_evidence',
    );
    expect(snapshot.shadowOnly, isTrue);
    expect(snapshot.productionEngineUnchanged, isTrue);
    expect(snapshot.autoActivation, isFalse);
  });

  test('engine lab flags safety regression when a shadow run weakens guardrails', () {
    final DecisionEngineEvaluationSnapshot evaluation =
        DecisionEngineEvaluationSnapshot.fromJson(<String, dynamic>{
      'evaluation_run_id': 'eval-risk',
      'challenger_version': 'challenger-risky',
      'status': 'blocked_safety_regression',
      'case_count': 30,
      'resolved_count': 20,
      'champion_alignment_rate': 70,
      'challenger_alignment_rate': 80,
      'alignment_uplift': 10,
      'recommendation_changes': 7,
      'risk_changes': 3,
      'safety_downgrades': 1,
      'unsafe_actionability_conflicts': 0,
      'created_at': '2026-08-18T22:21:00Z',
    });

    expect(evaluation.safetyPassed, isFalse);
    expect(evaluation.status, 'blocked_safety_regression');
    expect(evaluation.alignmentUplift, 10);
  });
}
