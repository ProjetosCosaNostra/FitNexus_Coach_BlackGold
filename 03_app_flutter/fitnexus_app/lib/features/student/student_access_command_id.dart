import 'dart:math';

String newStudentAccessCommandId() {
  final Random random = Random.secure();
  final StringBuffer buffer = StringBuffer();
  for (int index = 0; index < 16; index++) {
    buffer.write(random.nextInt(256).toRadixString(16).padLeft(2, '0'));
  }
  return buffer.toString();
}
