import 'dart:developer' as developer;
import 'dart:math' as math;

import 'package:shared_preferences/shared_preferences.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'growth_attribution_capture.dart';

class PublicFunnelTelemetry {
  PublicFunnelTelemetry._();

  static final PublicFunnelTelemetry instance = PublicFunnelTelemetry._();

  static const String _visitorPreferenceKey = 'fitnexus_public_visitor_v1';

  SupabaseClient get _client => Supabase.instance.client;

  Future<void> captureLandingView() => _capture('landing_view');

  Future<void> captureSignupStarted() => _capture('signup_started');

  Future<void> _capture(String eventName) async {
    try {
      final Uri uri = Uri.base;
      final String visitorKey = await _ensureVisitorKey();
      final GrowthAttributionTouch? touch = GrowthAttributionTouch.fromUri(uri);
      final String rawPath = uri.path.trim().isEmpty ? '/' : uri.path.trim();
      final String path = rawPath.startsWith('/') ? rawPath : '/';
      final String boundedPath =
          path.length <= 500 ? path : path.substring(0, 500);

      await _client.rpc(
        'capture_public_growth_event',
        params: <String, dynamic>{
          'p_event_name': eventName,
          'p_visitor_key': visitorKey,
          'p_landing_path': boundedPath,
          'p_source': touch?.source,
          'p_medium': touch?.medium,
          'p_campaign': touch?.campaign,
          'p_term': touch?.term,
          'p_content': touch?.content,
        },
      );
    } catch (error, stackTrace) {
      developer.log(
        'Public funnel telemetry failed without blocking navigation or signup.',
        name: 'fitnexus.growth.public',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  Future<String> _ensureVisitorKey() async {
    final SharedPreferences preferences = await SharedPreferences.getInstance();
    final String existing =
        (preferences.getString(_visitorPreferenceKey) ?? '').trim();
    if (_isValidVisitorKey(existing)) return existing;

    final math.Random random = math.Random.secure();
    final StringBuffer buffer = StringBuffer('v1_');
    for (int index = 0; index < 24; index += 1) {
      buffer.write(random.nextInt(256).toRadixString(16).padLeft(2, '0'));
    }
    final String created = buffer.toString();
    await preferences.setString(_visitorPreferenceKey, created);
    return created;
  }

  bool _isValidVisitorKey(String value) {
    if (value.length < 24 || value.length > 128) return false;
    return RegExp(r'^[A-Za-z0-9_-]+$').hasMatch(value);
  }
}
