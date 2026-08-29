import 'package:fitnexus_app/app/fitnexus_app.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('release route surface excludes demo-only route', () {
    final routes = buildFitNexusRoutes(includeDemo: false);

    expect(routes.containsKey('/demo'), isFalse);
    expect(routes.containsKey('/professor'), isTrue);
    expect(routes.containsKey('/student'), isTrue);
    expect(routes.containsKey('/links'), isTrue);
  });

  test('non-release route surface can expose demo route', () {
    final routes = buildFitNexusRoutes(includeDemo: true);

    expect(routes.containsKey('/demo'), isTrue);
  });
}
