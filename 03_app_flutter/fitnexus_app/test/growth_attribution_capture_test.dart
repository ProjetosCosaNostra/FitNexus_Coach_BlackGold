import 'package:fitnexus_app/features/growth/growth_attribution_capture.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('captures only explicit UTM fields and a relative landing path', () {
    final GrowthAttributionTouch? touch = GrowthAttributionTouch.fromUri(
      Uri.parse(
        'https://fitnexus.example/gestao-personal?utm_source=google&utm_medium=cpc&utm_campaign=coach_br&utm_term=app%20personal&utm_content=hero_a&email=should-not-be-captured@example.com',
      ),
    );

    expect(touch, isNotNull);
    expect(touch!.source, 'google');
    expect(touch.medium, 'cpc');
    expect(touch.campaign, 'coach_br');
    expect(touch.term, 'app personal');
    expect(touch.content, 'hero_a');
    expect(touch.landingPath, '/gestao-personal');

    final Map<String, dynamic> params = touch.rpcParams('org-1');
    expect(params['p_organization_id'], 'org-1');
    expect(params.containsKey('email'), isFalse);
    expect(params.containsKey('objective'), isFalse);
    expect(params.containsKey('pain'), isFalse);
    expect(params['p_referrer_host'], isNull);
  });

  test('returns null when no explicit UTM attribution exists', () {
    final GrowthAttributionTouch? touch = GrowthAttributionTouch.fromUri(
      Uri.parse('https://fitnexus.example/app?unrelated=value'),
    );
    expect(touch, isNull);
  });

  test('bounds campaign values before sending them to the backend', () {
    final String longCampaign = List<String>.filled(300, 'x').join();
    final GrowthAttributionTouch? touch = GrowthAttributionTouch.fromUri(
      Uri.parse('https://fitnexus.example/?utm_campaign=$longCampaign'),
    );

    expect(touch, isNotNull);
    expect(touch!.campaign, hasLength(160));
    expect(touch.landingPath, '/');
  });
}
