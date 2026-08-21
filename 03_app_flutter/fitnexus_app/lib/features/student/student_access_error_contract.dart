enum StudentAccessErrorContext {
  workout,
  feedback,
}

void throwStudentAccessError(
  Map<String, dynamic> value, {
  required StudentAccessErrorContext context,
}) {
  final String code = value['error']?.toString() ?? '';
  if (code.isEmpty) return;
  throw studentAccessStateError(code, context: context);
}

StateError studentAccessStateError(
  String code, {
  required StudentAccessErrorContext context,
}) {
  return StateError(studentAccessErrorMessage(code, context: context));
}

String studentAccessErrorMessage(
  String code, {
  required StudentAccessErrorContext context,
}) {
  switch (code) {
    case 'STUDENT_ACCESS_INVALID':
      return 'Este link de aluno é inválido, expirou ou foi substituído.';
    case 'STUDENT_ACCESS_RATE_LIMITED':
    case 'STUDENT_NETWORK_RATE_LIMITED':
      return 'Muitas ações em pouco tempo. Aguarde alguns segundos e tente novamente.';
    case 'STUDENT_COMMAND_IN_PROGRESS':
      return context == StudentAccessErrorContext.feedback
          ? 'Este feedback ainda está sendo confirmado. Tente novamente em instantes.'
          : 'Esta ação ainda está sendo confirmada. Tente novamente em instantes.';
    case 'STUDENT_COMMAND_ID_INVALID':
      return context == StudentAccessErrorContext.feedback
          ? 'A proteção do feedback recusou um identificador inválido.'
          : 'A proteção da ação do aluno recusou um identificador inválido.';
    case 'STUDENT_GATEWAY_BODY_TOO_LARGE':
    case 'STUDENT_GATEWAY_BODY_INVALID':
    case 'STUDENT_GATEWAY_ACTION_INVALID':
    case 'STUDENT_GATEWAY_PAYLOAD_INVALID':
    case 'STUDENT_GATEWAY_METHOD_NOT_ALLOWED':
      return 'O app não conseguiu enviar a solicitação do aluno com segurança. Atualize a página e tente novamente.';
    case 'STUDENT_NETWORK_ORIGIN_UNAVAILABLE':
    case 'STUDENT_GATEWAY_BACKEND_AUTH_UNAVAILABLE':
    case 'STUDENT_NETWORK_RATE_LIMIT_UNAVAILABLE':
    case 'STUDENT_GATEWAY_UPSTREAM_FAILED':
    case 'STUDENT_GATEWAY_UNAVAILABLE':
    case 'STUDENT_GATEWAY_REQUEST_FAILED':
      return 'Não foi possível confirmar o acesso agora. Aguarde alguns instantes e tente novamente.';
    default:
      return 'O acesso do aluno foi recusado pelo limite de segurança: $code';
  }
}
