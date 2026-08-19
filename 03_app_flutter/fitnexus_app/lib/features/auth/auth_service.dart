import 'dart:developer' as developer;

import 'package:supabase_flutter/supabase_flutter.dart';

import '../growth/growth_attribution_capture.dart';

class AuthService {
  AuthService._();

  static final AuthService instance = AuthService._();

  String? _lastAttributionFingerprint;

  SupabaseClient get _client => Supabase.instance.client;

  Session? get currentSession => _client.auth.currentSession;
  User? get currentUser => _client.auth.currentUser;
  Stream<AuthState> get authStateChanges => _client.auth.onAuthStateChange;

  Future<AuthResponse> signIn({
    required String email,
    required String password,
  }) {
    return _client.auth.signInWithPassword(
      email: email.trim(),
      password: password,
    );
  }

  Future<AuthResponse> signUpProfessor({
    required String fullName,
    required String organizationName,
    required String email,
    required String password,
  }) {
    return _client.auth.signUp(
      email: email.trim(),
      password: password,
      data: <String, dynamic>{
        'full_name': fullName.trim(),
        'organization_name': organizationName.trim(),
        'fitnexus_role': 'professor',
      },
    );
  }

  Future<void> resendSignUpConfirmation(String email) async {
    await _client.auth.resend(
      type: OtpType.signup,
      email: email.trim(),
    );
  }

  Future<String> ensureProfessorOrganization({String? preferredName}) async {
    final User? user = currentUser;
    if (user == null) {
      throw StateError('Sessão não encontrada. Entre novamente.');
    }

    final Map<String, dynamic> metadata = user.userMetadata ?? <String, dynamic>{};
    final String metadataOrganization =
        (metadata['organization_name'] as String? ?? '').trim();
    final String metadataName = (metadata['full_name'] as String? ?? '').trim();

    final String candidate = (preferredName ?? '').trim().isNotEmpty
        ? preferredName!.trim()
        : metadataOrganization.isNotEmpty
            ? metadataOrganization
            : metadataName.isNotEmpty
                ? '$metadataName • FitNexus'
                : 'Meu espaço FitNexus';

    final dynamic result = await _client.rpc(
      'ensure_my_organization',
      params: <String, dynamic>{'p_name': candidate},
    );

    final String organizationId = result?.toString() ?? '';
    if (organizationId.isEmpty) {
      throw StateError('Não foi possível preparar a organização do professor.');
    }

    await _attachGrowthAttributionIfPresent(organizationId);
    return organizationId;
  }

  Future<void> _attachGrowthAttributionIfPresent(String organizationId) async {
    final GrowthAttributionTouch? touch =
        GrowthAttributionTouch.fromUri(Uri.base);
    if (touch == null) return;

    final String fingerprint = '$organizationId|${touch.fingerprint}';
    if (_lastAttributionFingerprint == fingerprint) return;

    try {
      await _client.rpc(
        'attach_growth_attribution',
        params: touch.rpcParams(organizationId),
      );
      _lastAttributionFingerprint = fingerprint;
    } catch (error, stackTrace) {
      developer.log(
        'Growth attribution capture failed without blocking core auth.',
        name: 'fitnexus.growth',
        error: error,
        stackTrace: stackTrace,
      );
    }
  }

  Future<void> signOut() {
    _lastAttributionFingerprint = null;
    return _client.auth.signOut();
  }
}
