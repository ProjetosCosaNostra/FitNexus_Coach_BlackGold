import 'dart:convert';
import 'dart:io';

import 'package:fitnexus_app/features/student/student_access_transport.dart';
import 'package:fitnexus_app/features/student/student_access_transport_contract.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

const String _expectedStudentId = 'bbdf3d96-0569-51d4-aadc-251ed0abc24e';
const String _expectedPlanId = 'b54064b9-f6a8-539e-b4a2-976d99141844';
const String _expectedExerciseId = '51871b03-c901-5a8f-b659-40f63e1f22e4';
const String _expectedStudentName = 'Stage31 Synthetic Student';
const String _expectedPlanName = 'Stage31 Synthetic Plan';
const String _expectedExerciseName = 'Stage31 Synthetic Exercise';

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
  throw StateError('Stage31 Edge response was not a JSON object.');
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
      reason: 'Stage31 response returned the raw synthetic bearer.');
  final leaked = _forbiddenResponseKeys.intersection(_walkKeys(value));
  expect(leaked, isEmpty,
      reason: 'Stage31 response returned forbidden security metadata.');
}

String _requiredEnv(String name) {
  final value = Platform.environment[name]?.trim() ?? '';
  if (value.isEmpty) {
    throw StateError('Missing required Stage31 proof environment input: $name');
  }
  return value;
}

String _requiredUuid(Object? value, String label) {
  final raw = value?.toString() ?? '';
  final parsed = Uri.tryParse('urn:uuid:$raw');
  if (raw.length != 36 || parsed == null) {
    throw StateError('Stage31 proof did not receive a valid $label UUID.');
  }
  return raw;
}

void main() {
  test('Stage 31 proves all five student routes through Flutter Edge transport',
      () async {
    expect(StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.directRpc);
    expect(StudentAccessTransportContract.resolvedMode,
        StudentAccessTransportMode.directRpc);
    expect(StudentAccessTransportContract.edgeGatewaySelected, isFalse);
    expect(StudentAccessTransportContract.automaticEdgeToDirectFallback, isFalse);
    expect(StudentAccessTransportContract.explicitRollbackRequested, isFalse);
    expect(StudentAccessTransportContract.explicitRollbackAuthorized, isFalse);
    expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
    expect(StudentAccessTransportContract.clientCutoverVerified, isFalse);

    final rawToken = _requiredEnv('STAGE31_SYNTHETIC_TOKEN');
    expect(RegExp(r'^[0-9a-f]{64}$').hasMatch(rawToken), isTrue);

    final url = _requiredEnv('STAGE31_SUPABASE_URL');
    final publishableKey = _requiredEnv('STAGE31_SUPABASE_PUBLISHABLE_KEY');

    // flutter_test installs a mock HttpClient for widget isolation. This proof is
    // intentionally a live integration test and restores the VM's real client.
    HttpOverrides.global = null;

    final client = SupabaseClient(url, publishableKey);
    final transport = StudentAccessTransport.forVerification(
      client: client,
      configuredMode: StudentAccessTransportMode.edgeGateway,
    );

    final workout = _map(await transport.invoke(
      action: 'get_workout',
      directParams: const <String, dynamic>{},
      edgePayload: <String, dynamic>{'token': rawToken},
    ));
    _assertSafeResponse(workout, rawToken);
    expect(workout['error'], isNull);

    final student = _map(workout['student']);
    final plan = _map(workout['plan']);
    final exercises = workout['exercises'] as List<dynamic>? ?? const <dynamic>[];
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
        'command_id': '31000000000000000000000000000001',
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
        'command_id': '31000000000000000000000000000002',
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
        'command_id': '31000000000000000000000000000003',
      },
    ));
    _assertSafeResponse(submitted, rawToken);
    expect(submitted['error'], isNull);
    _requiredUuid(submitted['feedback_id'], 'feedback');
    expect(submitted['session_id'], sessionId);
    expect(submitted['submitted'], isTrue);
    expect(submitted['risk_signal'], 'low');

    expect(StudentAccessTransportContract.activeMode,
        StudentAccessTransportMode.directRpc);
    expect(StudentAccessTransportContract.edgeGatewaySelected, isFalse);
    expect(StudentAccessTransportContract.directRpcExecuteRevoked, isFalse);
  }, timeout: const Timeout(Duration(minutes: 3)));
}
