import 'dart:convert';
import 'dart:io';

import 'package:fitnexus_app/features/student/student_access_transport.dart';
import 'package:fitnexus_app/features/student/student_access_transport_contract.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

const String _expectedStudentId = 'bdbe631a-4c44-53fc-a0da-38310bbdf90e';
const String _expectedPlanId = 'a1c29966-b4c1-59fc-bb9e-ac0b055ea577';
const String _expectedExerciseId = '585b0618-8141-513c-a37e-02cb5ccd93f1';
const String _expectedStudentName = 'Stage32 Synthetic Student';
const String _expectedPlanName = 'Stage32 Synthetic Plan';
const String _expectedExerciseName = 'Stage32 Synthetic Exercise';

final bool _liveProofEnabled =
    Platform.environment['STAGE32_POST_CUTOVER_LIVE_PROOF_ENABLED'] == '1';

const Set<String> _forbiddenResponseKeys = <String>{
  'token',
  'token_hash',
  'authorization',
  'apikey',
  'headers',
  'network_origin',
  'raw_network_origin',
  'origin_hash',
  'client_ip',
  'ip',
  'secret',
  'service_role',
  'cf-connecting-ip',
  'x-forwarded-for',
  'x-real-ip',
};

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  throw StateError('Stage32 Edge response was not a JSON object.');
}

Set<String> _walkKeys(Object? value) {
  final keys = <String>{};
  if (value is Map) {
    for (final entry in value.entries) {
      keys.add(entry.key.toString().toLowerCase());
      keys.addAll(_walkKeys(entry.value));
    }
  } else if (value is List) {
    for (final item in value) {
      keys.addAll(_walkKeys(item));
    }
  }
  return keys;
}

void _assertSafeResponse(Map<String, dynamic> value, String rawToken) {
  final encoded = jsonEncode(value);
  expect(encoded.contains(rawToken), isFalse,
      reason: 'Stage32 response returned the raw synthetic bearer.');
  final leaked = _forbiddenResponseKeys.intersection(_walkKeys(value));
  expect(leaked, isEmpty,
      reason: 'Stage32 response returned forbidden security metadata.');
}

String _requiredEnv(String name) {
  final value = Platform.environment[name]?.trim() ?? '';
  if (value.isEmpty) {
    throw StateError('Missing required Stage32 proof environment input: $name');
  }
  return value;
}

String _requiredUuid(Object? value, String label) {
  final raw = value?.toString() ?? '';
  final valid = RegExp(
    r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$',
  ).hasMatch(raw);
  if (!valid) {
    throw StateError('Stage32 proof did not receive a valid $label UUID.');
  }
  return raw;
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test(
    'Stage 32 proves all five routes through the production-selected Edge transport',
    () async {
      expect(
        StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.edgeGateway,
      );
      expect(
        StudentAccessTransportContract.resolvedMode,
        StudentAccessTransportMode.edgeGateway,
      );
      expect(StudentAccessTransportContract.edgeGatewaySelected, isTrue);
      expect(
        StudentAccessTransportContract.automaticEdgeToDirectFallback,
        isFalse,
      );
      expect(StudentAccessTransportContract.explicitRollbackRequested, isFalse);
      expect(StudentAccessTransportContract.explicitRollbackAuthorized, isFalse);
      expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
      expect(StudentAccessTransportContract.rollbackVerified, isFalse);
      expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);

      final rawToken = _requiredEnv('STAGE32_SYNTHETIC_TOKEN');
      expect(RegExp(r'^[0-9a-f]{64}$').hasMatch(rawToken), isTrue);

      final url = _requiredEnv('STAGE32_SUPABASE_URL');
      final publishableKey =
          _requiredEnv('STAGE32_SUPABASE_PUBLISHABLE_KEY');

      // flutter_test installs a mock HttpClient for widget isolation. This is a
      // deliberately live integration proof of the production-selected client path.
      HttpOverrides.global = null;

      await Supabase.initialize(
        url: url,
        publishableKey: publishableKey,
      );

      final transport = StudentAccessTransport.instance;

      final workout = _map(await transport.invoke(
        action: 'get_workout',
        directParams: const <String, dynamic>{},
        edgePayload: <String, dynamic>{'token': rawToken},
      ));
      _assertSafeResponse(workout, rawToken);
      expect(workout['error'], isNull);

      final student = _map(workout['student']);
      final plan = _map(workout['plan']);
      final exercises =
          workout['exercises'] as List<dynamic>? ?? const <dynamic>[];
      expect(student['id'], _expectedStudentId);
      expect(student['name'], _expectedStudentName);
      expect(plan['id'], _expectedPlanId);
      expect(plan['name'], _expectedPlanName);
      expect(workout['session'], isNull);
      expect(workout['history'], const <dynamic>[]);
      expect(exercises, hasLength(1));
      final exercise = _map(exercises.single);
      expect(exercise['id'], _expectedExerciseId);
      expect(exercise['name'], _expectedExerciseName);
      expect(exercise['completed'], isFalse);
      expect(exercise['completed_at'], isNull);

      final started = _map(await transport.invoke(
        action: 'start_workout',
        directParams: const <String, dynamic>{},
        edgePayload: <String, dynamic>{
          'token': rawToken,
          'command_id': '32000000000000000000000000000001',
        },
      ));
      _assertSafeResponse(started, rawToken);
      expect(started['error'], isNull);
      expect(started['replayed'], isFalse);
      final sessionId = _requiredUuid(started['session_id'], 'session');

      final completion = _map(await transport.invoke(
        action: 'set_completion',
        directParams: const <String, dynamic>{},
        edgePayload: <String, dynamic>{
          'token': rawToken,
          'session_id': sessionId,
          'exercise_id': _expectedExerciseId,
          'completed': true,
          'command_id': '32000000000000000000000000000002',
        },
      ));
      _assertSafeResponse(completion, rawToken);
      expect(completion['error'], isNull);
      expect(completion['session_id'], sessionId);
      expect(completion['status'], 'completed');
      expect(completion['completed_exercises'], 1);
      expect(completion['total_exercises'], 1);
      expect(completion['adherence'], 100);

      final feedbackContext = _map(await transport.invoke(
        action: 'get_feedback_context',
        directParams: const <String, dynamic>{},
        edgePayload: <String, dynamic>{'token': rawToken},
      ));
      _assertSafeResponse(feedbackContext, rawToken);
      expect(feedbackContext['error'], isNull);
      expect(feedbackContext['eligible'], isTrue);
      expect(feedbackContext['session_id'], sessionId);
      expect(feedbackContext['plan_name'], _expectedPlanName);
      expect(feedbackContext['submitted'], isFalse);
      expect(feedbackContext['feedback'], isNull);
      expect(feedbackContext['completed_at'], isA<String>());

      final submitted = _map(await transport.invoke(
        action: 'submit_feedback',
        directParams: const <String, dynamic>{},
        edgePayload: <String, dynamic>{
          'token': rawToken,
          'session_id': sessionId,
          'perceived_exertion': 5,
          'pain_score': 0,
          'energy_score': 4,
          'pain_location': null,
          'note': null,
          'command_id': '32000000000000000000000000000003',
        },
      ));
      _assertSafeResponse(submitted, rawToken);
      expect(submitted['error'], isNull);
      _requiredUuid(submitted['feedback_id'], 'feedback');
      expect(submitted['session_id'], sessionId);
      expect(submitted['submitted'], isTrue);
      expect(submitted['risk_signal'], 'low');

      expect(
        StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.edgeGateway,
      );
      expect(StudentAccessTransportContract.edgeGatewaySelected, isTrue);
      expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
      expect(StudentAccessTransportContract.rollbackVerified, isFalse);
      expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);
    },
    timeout: const Timeout(Duration(minutes: 3)),
    skip: _liveProofEnabled
        ? false
        : 'Stage32 post-cutover live proof executes only in its sealed one-shot workflow.',
  );
}
