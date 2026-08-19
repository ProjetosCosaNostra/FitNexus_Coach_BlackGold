import 'package:fitnexus_app/features/professor/professor_billing_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('selected provider remains blocked while credentials and price are pending', () {
    final BillingProviderReadiness readiness =
        BillingProviderReadiness.fromJson(<String, dynamic>{
      'organization_id': 'org-1',
      'scope': 'BR_V1',
      'provider': <String, dynamic>{
        'code': 'asaas',
        'display_name': 'Asaas',
        'selection_state': 'selected_pending_credentials',
        'evidence_version': '2026-08-18-official-docs-v1',
        'capabilities': <String, dynamic>{
          'hosted_checkout': true,
          'recurring_subscriptions': true,
          'credit_card_recurring': true,
          'pix': true,
          'pix_automatic': true,
          'sandbox': true,
          'webhooks': true,
        },
      },
      'pricing': <String, dynamic>{
        'state': 'UNFROZEN',
        'active_price_count': 0,
      },
      'credentials': <String, dynamic>{
        'state': 'PENDING_EXTERNAL_CREDENTIAL_BOUNDARY',
        'secret_exposed_to_flutter': false,
      },
      'checkout': <String, dynamic>{
        'ready': false,
        'server_amount_authority': true,
        'client_amount_allowed': false,
        'silent_provider_fallback': false,
      },
      'subscription_provider_bound': false,
      'generated_at': '2026-08-19T02:55:00Z',
    });

    expect(readiness.provider.code, 'asaas');
    expect(readiness.provider.selectionState, 'selected_pending_credentials');
    expect(readiness.provider.capability('pix_automatic'), isTrue);
    expect(readiness.pricing.state, 'UNFROZEN');
    expect(readiness.pricing.promoted, isFalse);
    expect(readiness.credentials.configured, isFalse);
    expect(readiness.credentials.secretExposedToFlutter, isFalse);
    expect(readiness.checkout.ready, isFalse);
    expect(readiness.checkout.serverAmountAuthority, isTrue);
    expect(readiness.checkout.clientAmountAllowed, isFalse);
    expect(readiness.checkout.silentProviderFallback, isFalse);
    expect(readiness.externalBoundaryPending, isTrue);
  });

  test('checkout only reports ready after external authority and promoted price', () {
    final BillingProviderReadiness readiness =
        BillingProviderReadiness.fromJson(<String, dynamic>{
      'organization_id': 'org-2',
      'scope': 'BR_V1',
      'provider': <String, dynamic>{
        'code': 'asaas',
        'display_name': 'Asaas',
        'selection_state': 'active',
        'evidence_version': 'v2',
        'capabilities': <String, dynamic>{'hosted_checkout': true},
      },
      'pricing': <String, dynamic>{
        'state': 'PROMOTED',
        'active_price_count': 3,
      },
      'credentials': <String, dynamic>{
        'state': 'EXTERNAL_AUTHORITY_CONFIGURED',
        'secret_exposed_to_flutter': false,
      },
      'checkout': <String, dynamic>{
        'ready': true,
        'server_amount_authority': true,
        'client_amount_allowed': false,
        'silent_provider_fallback': false,
      },
      'subscription_provider_bound': true,
      'generated_at': '2026-08-19T03:00:00Z',
    });

    expect(readiness.credentials.configured, isTrue);
    expect(readiness.pricing.promoted, isTrue);
    expect(readiness.checkout.ready, isTrue);
    expect(readiness.externalBoundaryPending, isFalse);
  });
}
