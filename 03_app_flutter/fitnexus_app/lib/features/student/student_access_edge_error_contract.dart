const Set<String> _trustedStudentEdgeErrorCodes = <String>{
  'STUDENT_NETWORK_ORIGIN_UNAVAILABLE',
  'STUDENT_GATEWAY_BODY_TOO_LARGE',
  'STUDENT_GATEWAY_BODY_INVALID',
  'STUDENT_GATEWAY_ACTION_INVALID',
  'STUDENT_GATEWAY_BACKEND_AUTH_UNAVAILABLE',
  'STUDENT_NETWORK_RATE_LIMIT_UNAVAILABLE',
  'STUDENT_NETWORK_RATE_LIMITED',
  'STUDENT_GATEWAY_PAYLOAD_INVALID',
  'STUDENT_GATEWAY_UPSTREAM_FAILED',
  'STUDENT_GATEWAY_METHOD_NOT_ALLOWED',
};

/// Converts a non-2xx Edge Functions exception into the same narrow JSON error
/// contract consumed by the student repositories. Arbitrary relay/upstream
/// details are never copied into the returned payload.
Map<String, dynamic> normalizeStudentEdgeFunctionException({
  required int status,
  required dynamic details,
}) {
  final Map<String, dynamic> detailMap = _map(details);
  final String detailCode = detailMap['error']?.toString() ?? '';

  if (_trustedStudentEdgeErrorCodes.contains(detailCode)) {
    final Map<String, dynamic> normalized = <String, dynamic>{
      'ok': false,
      'error': detailCode,
    };
    if (detailCode == 'STUDENT_NETWORK_RATE_LIMITED') {
      final int? retryAfter = _boundedRetryAfter(detailMap['retry_after_seconds']);
      if (retryAfter != null) {
        normalized['retry_after_seconds'] = retryAfter;
      }
    }
    return normalized;
  }

  return <String, dynamic>{
    'ok': false,
    'error': status == 0 || status >= 500
        ? 'STUDENT_GATEWAY_UNAVAILABLE'
        : 'STUDENT_GATEWAY_REQUEST_FAILED',
  };
}

int? _boundedRetryAfter(dynamic value) {
  final int? parsed = value is num
      ? value.toInt()
      : int.tryParse(value?.toString() ?? '');
  if (parsed == null || parsed < 1 || parsed > 60) return null;
  return parsed;
}

Map<String, dynamic> _map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}
