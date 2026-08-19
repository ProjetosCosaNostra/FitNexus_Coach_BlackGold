import 'package:fitnexus_app/features/professor/professor_subscription_repository.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('trial snapshot preserves limits, usage, features and authority', () {
    final SubscriptionEntitlementSnapshot snapshot =
        SubscriptionEntitlementSnapshot.fromJson(<String, dynamic>{
      'organization_id': 'org-1',
      'plan': <String, dynamic>{
        'code': 'trial',
        'display_name': 'BlackGold Trial',
        'student_limit': 10,
        'member_limit': 1,
        'feature_flags': <String, dynamic>{
          'coach_action_center': true,
          'decision_intelligence': true,
        },
      },
      'subscription': <String, dynamic>{
        'status': 'trialing',
        'effective_status': 'trialing',
        'write_enabled': true,
        'trial_started_at': '2026-08-18T22:00:00Z',
        'trial_ends_at': '2026-09-01T22:00:00Z',
        'trial_seconds_remaining': 1209600,
        'cancel_at_period_end': false,
        'provider_connected': false,
        'authority_source': 'system_trial',
        'authority_version': 1,
      },
      'usage': <String, dynamic>{
        'students': 4,
        'student_limit': 10,
        'student_remaining': 6,
        'members': 1,
        'member_limit': 1,
        'member_remaining': 0,
      },
      'features': <String, dynamic>{
        'coach_action_center': true,
        'decision_intelligence': true,
      },
      'pricing': <String, dynamic>{
        'state': 'UNFROZEN',
        'provider_bound': false,
      },
      'guardrails': <String, dynamic>{
        'server_enforced_student_limit': true,
        'direct_subscription_mutation': false,
        'provider_neutral_core': true,
      },
      'generated_at': '2026-08-18T22:10:00Z',
    });

    expect(snapshot.organizationId, 'org-1');
    expect(snapshot.plan.code, 'trial');
    expect(snapshot.subscription.writeEnabled, isTrue);
    expect(snapshot.subscription.trialDaysRemaining, 14);
    expect(snapshot.usage.students, 4);
    expect(snapshot.usage.studentRemaining, 6);
    expect(snapshot.usage.memberRemaining, 0);
    expect(snapshot.featureEnabled('decision_intelligence'), isTrue);
    expect(snapshot.featureEnabled('missing_feature'), isFalse);
    expect(snapshot.pricingState, 'UNFROZEN');
    expect(snapshot.providerBound, isFalse);
    expect(snapshot.guardrails['provider_neutral_core'], isTrue);
  });

  test('expired snapshot is read-only even if stored status was trialing', () {
    final SubscriptionEntitlementSnapshot snapshot =
        SubscriptionEntitlementSnapshot.fromJson(<String, dynamic>{
      'organization_id': 'org-2',
      'plan': <String, dynamic>{
        'code': 'trial',
        'display_name': 'BlackGold Trial',
        'student_limit': 10,
        'member_limit': 1,
        'feature_flags': <String, dynamic>{},
      },
      'subscription': <String, dynamic>{
        'status': 'trialing',
        'effective_status': 'expired',
        'write_enabled': false,
        'trial_seconds_remaining': 0,
        'cancel_at_period_end': false,
        'provider_connected': false,
        'authority_source': 'system_trial',
        'authority_version': 1,
      },
      'usage': <String, dynamic>{
        'students': 10,
        'student_limit': 10,
        'student_remaining': 0,
        'members': 1,
        'member_limit': 1,
        'member_remaining': 0,
      },
      'features': <String, dynamic>{},
      'pricing': <String, dynamic>{'state': 'UNFROZEN', 'provider_bound': false},
      'guardrails': <String, dynamic>{},
      'generated_at': '2026-09-02T00:00:00Z',
    });

    expect(snapshot.subscription.status, 'trialing');
    expect(snapshot.subscription.effectiveStatus, 'expired');
    expect(snapshot.subscription.writeEnabled, isFalse);
    expect(snapshot.subscription.trialDaysRemaining, 0);
    expect(snapshot.usage.studentRatio, 1);
  });

  test('catalog item keeps commercial capacity independent from price', () {
    final SubscriptionPlanCatalogItem item =
        SubscriptionPlanCatalogItem.fromJson(<String, dynamic>{
      'code': 'pro',
      'display_name': 'Coach Pro',
      'student_limit': 100,
      'member_limit': 3,
      'trial_days': 0,
    });

    expect(item.code, 'pro');
    expect(item.studentLimit, 100);
    expect(item.memberLimit, 3);
  });
}
