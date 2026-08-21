import 'package:flutter_test/flutter_test.dart';
import 'package:fitnexus_app/features/student/student_access_edge_error_contract.dart';
import 'package:fitnexus_app/features/student/student_access_error_contract.dart';

void main() {
  group('student Edge error contract', () {
    test('preserves only trusted gateway rate-limit code and bounded retry', () {
      final Map<String, dynamic> normalized =
          normalizeStudentEdgeFunctionException(
        status: 429,
        details: <String, dynamic>{
          'error': 'STUDENT_NETWORK_RATE_LIMITED',
          'retry_after_seconds': 17,
          'raw_token': 'must-not-survive',
          'upstream': 'must-not-survive',
        },
      );

      expect(normalized, <String, dynamic>{
        'ok': false,
        'error': 'STUDENT_NETWORK_RATE_LIMITED',
        'retry_after_seconds': 17,
      });
      expect(
        studentAccessErrorMessage(
          normalized['error']! as String,
          context: StudentAccessErrorContext.workout,
        ),
        'Muitas ações em pouco tempo. Aguarde alguns segundos e tente novamente.',
      );
    });

    test('does not echo arbitrary exception details', () {
      final Map<String, dynamic> normalized =
          normalizeStudentEdgeFunctionException(
        status: 502,
        details: <String, dynamic>{
          'error': 'UNTRUSTED_UPSTREAM_CODE',
          'token': 'secret-token',
          'origin': '198.51.100.10',
          'message': 'raw upstream detail',
        },
      );

      expect(normalized, <String, dynamic>{
        'ok': false,
        'error': 'STUDENT_GATEWAY_UNAVAILABLE',
      });
      expect(normalized.toString(), isNot(contains('secret-token')));
      expect(normalized.toString(), isNot(contains('198.51.100.10')));
      expect(normalized.toString(), isNot(contains('raw upstream detail')));
    });

    test('maps transport failure to generic unavailable code', () {
      expect(
        normalizeStudentEdgeFunctionException(
          status: 0,
          details: 'socket failure with private diagnostics',
        ),
        <String, dynamic>{
          'ok': false,
          'error': 'STUDENT_GATEWAY_UNAVAILABLE',
        },
      );
    });

    test('drops out-of-contract retry values', () {
      expect(
        normalizeStudentEdgeFunctionException(
          status: 429,
          details: <String, dynamic>{
            'error': 'STUDENT_NETWORK_RATE_LIMITED',
            'retry_after_seconds': 9999,
          },
        ),
        <String, dynamic>{
          'ok': false,
          'error': 'STUDENT_NETWORK_RATE_LIMITED',
        },
      );
    });
  });
}
