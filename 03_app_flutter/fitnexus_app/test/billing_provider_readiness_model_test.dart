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
        'mode': 'NONE',
        'decision_version': null,
        'annual_strategy': null,
        'active_price_count': 0,
        'expected_price_count': 6,
        'complete': false,
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
        'pricing_decision_bound': false,
      },
      'subscription_provider_bound': false,
      'generated_at': '2026-08-19T02:55:00Z',
    });

    expect(readiness.provider.code, 'asaas');
    expect(readiness.provider.capability('pix_automatic'), isTrue);
    expect(readiness.pricing.promoted, isFalse);
    expect(readiness.pricing.experiment, isFalse);
    expect(readiness.credentials.configured, isFalse);
    expect(readiness.checkout.pricingDecisionBound, isFalse);
    expect(readiness.externalBoundaryPending, isTrue);
  });

  test('complete experiment pricing is promoted without pretending credentials exist', () {
    final BillingProviderReadiness readiness =
        BillingProviderReadiness.fromJson(<String, dynamic>{
      'organization_id': 'org-2',
      'scope': 'BR_V1',
      'provider': <String, dynamic>{
        'code': 'asaas',
        'display_name': 'Asaas',
        'selection_state': 'selected_pending_credentials',
        'evidence_version': 'v2',
        'capabilities': <String, dynamic>{'hosted_checkout': true},
      },
      'pricing': <String, dynamic>{
        'state': 'PROMOTED',
        'mode': 'EXPERIMENT',
        'decision_version': 'BR_V1_PRICING_EXPERIMENT_001',
        'annual_strategy': 'TEN_MONTHS_FOR_TWELVE',
        'active_price_count': 6,
        'expected_price_count': 6,
        'complete': true,
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
        'pricing_decision_bound': true,
      },
      'subscription_provider_bound': false,
      'generated_at': '2026-08-19T03:00:00Z',
    });

    expect(readiness.pricing.promoted, isTrue);
    expect(readiness.pricing.experiment, isTrue);
    expect(readiness.pricing.decisionVersion, 'BR_V1_PRICING_EXPERIMENT_001');
    expect(readiness.checkout.pricingDecisionBound, isTrue);
    expect(readiness.checkout.ready, isFalse);
    expect(readiness.externalBoundaryPending, isTrue);
  });

  test('pricing catalog preserves decision identity and ten-month annual strategy', () {
    final PricingCatalogSnapshot catalog =
        PricingCatalogSnapshot.fromJson(<String, dynamic>{
      'currency': 'BRL',
      'decision_version': 'BR_V1_PRICING_EXPERIMENT_001',
      'mode': 'EXPERIMENT',
      'annual_strategy': 'TEN_MONTHS_FOR_TWELVE',
      'generated_at': '2026-08-19T04:55:00Z',
      'offers': <Map<String, dynamic>>[
        <String, dynamic>{
          'plan_code': 'solo',
          'display_name': 'Coach Solo',
          'student_limit': 30,
          'member_limit': 1,
          'monthly_amount_minor': 3990,
          'annual_amount_minor': 39900,
          'annual_savings_minor': 7980,
          'annual_monthly_equivalent_minor': 3325,
          'pricing_decision_version': 'BR_V1_PRICING_EXPERIMENT_001',
        },
      ],
    });

    expect(catalog.experiment, isTrue);
    expect(catalog.offers, hasLength(1));
    expect(catalog.offers.single.monthlyAmountMinor, 3990);
    expect(catalog.offers.single.annualAmountMinor, 39900);
    expect(catalog.offers.single.annualSavingsMinor, 7980);
    expect(catalog.offers.single.pricingDecisionVersion, catalog.decisionVersion);
  });
}
