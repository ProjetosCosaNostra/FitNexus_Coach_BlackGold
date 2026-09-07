import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import 'professor_billing_repository.dart';
import 'professor_subscription_repository.dart';

class ProfessorSubscriptionPage extends StatefulWidget {
  const ProfessorSubscriptionPage({super.key});

  @override
  State<ProfessorSubscriptionPage> createState() =>
      _ProfessorSubscriptionPageState();
}

class _ProfessorSubscriptionPageState extends State<ProfessorSubscriptionPage> {
  final ProfessorSubscriptionRepository _repository =
      ProfessorSubscriptionRepository.instance;
  final ProfessorBillingRepository _billing = ProfessorBillingRepository.instance;

  SubscriptionEntitlementSnapshot? _snapshot;
  BillingProviderReadiness? _billingReadiness;
  List<SubscriptionPlanCatalogItem> _catalog =
      const <SubscriptionPlanCatalogItem>[];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _reload();
  }

  Future<void> _reload() async {
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
      });
    }
    try {
      final List<Object> result = await Future.wait<Object>(<Future<Object>>[
        _repository.fetchSnapshot(),
        _repository.fetchCatalog(),
        _billing.fetchReadiness(),
      ]);
      if (!mounted) return;
      setState(() {
        _snapshot = result[0] as SubscriptionEntitlementSnapshot;
        _catalog = result[1] as List<SubscriptionPlanCatalogItem>;
        _billingReadiness = result[2] as BillingProviderReadiness;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('SUBSCRIPTION_NOT_INITIALIZED')) {
      return 'A autoridade de assinatura ainda não foi inicializada para esta organização.';
    }
    if (text.contains('BILLING_PROVIDER_NOT_SELECTED')) {
      return 'O provedor de cobrança ainda não possui uma seleção promovida para este mercado.';
    }
    return 'Não foi possível carregar o plano agora. ${text.replaceFirst('Exception: ', '')}';
  }

  @override
  Widget build(BuildContext context) {
    final SubscriptionEntitlementSnapshot? snapshot = _snapshot;

    return Scaffold(
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _CommercialAtmosphere()),
          SafeArea(
            child: RefreshIndicator(
              color: AppColors.gold,
              onRefresh: _reload,
              child: ListView(
                physics: const AlwaysScrollableScrollPhysics(),
                padding: const EdgeInsets.fromLTRB(
                  BlackGoldSpace.lg,
                  BlackGoldSpace.xl,
                  BlackGoldSpace.lg,
                  120,
                ),
                children: <Widget>[
                  _CommercialHeader(
                    loading: _loading,
                    onRefresh: _reload,
                  ),
                  const SizedBox(height: BlackGoldSpace.lg),
                  if (_loading && snapshot == null)
                    const _LoadingPanel()
                  else if (_error != null && snapshot == null)
                    _Notice(text: _error!, error: true)
                  else if (snapshot != null) ...<Widget>[
                    _PlanHero(snapshot: snapshot),
                    const SizedBox(height: BlackGoldSpace.lg),
                    _CommercialSummary(
                      snapshot: snapshot,
                      readiness: _billingReadiness,
                    ),
                    const SizedBox(height: BlackGoldSpace.lg),
                    if (_billingReadiness != null) ...<Widget>[
                      _BillingReadinessCard(readiness: _billingReadiness!),
                      const SizedBox(height: BlackGoldSpace.lg),
                    ],
                    _UsageCard(snapshot: snapshot),
                    const SizedBox(height: BlackGoldSpace.lg),
                    _FeaturesCard(snapshot: snapshot),
                    const SizedBox(height: BlackGoldSpace.lg),
                    _AuthorityCard(snapshot: snapshot),
                    const SizedBox(height: BlackGoldSpace.lg),
                    _CatalogCard(
                      catalog: _catalog,
                      currentCode: snapshot.plan.code,
                    ),
                    if (_error != null) ...<Widget>[
                      const SizedBox(height: BlackGoldSpace.md),
                      _Notice(text: _error!, error: true),
                    ],
                  ],
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CommercialAtmosphere extends StatelessWidget {
  const _CommercialAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.72, -0.95),
            radius: 1.2,
            colors: <Color>[
              AppColors.gold.withValues(alpha: 0.075),
              Colors.transparent,
            ],
          ),
        ),
      ),
    );
  }
}

class _CommercialHeader extends StatelessWidget {
  const _CommercialHeader({required this.loading, required this.onRefresh});

  final bool loading;
  final Future<void> Function() onRefresh;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.xl),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.hero),
        border: Border.all(color: AppColors.borderGold),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool compact = constraints.maxWidth < BlackGoldBreakpoints.tablet;
          final Widget copy = const Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'BLACKGOLD COMMERCIAL CORE',
                style: TextStyle(
                  color: AppColors.goldSoft,
                  fontSize: 11,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.25,
                ),
              ),
              SizedBox(height: BlackGoldSpace.xs),
              Text(
                'Plano, capacidade e autoridade comercial',
                style: TextStyle(
                  color: AppColors.text,
                  fontSize: 30,
                  height: 1.06,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.7,
                ),
              ),
              SizedBox(height: BlackGoldSpace.sm),
              Text(
                'Limites, preço, provedor e prontidão do checkout vêm do servidor. O aplicativo não inventa valores, não guarda segredos do provedor e não concede plano por interface.',
                style: TextStyle(
                  color: AppColors.muted,
                  height: 1.5,
                  fontSize: 14,
                ),
              ),
            ],
          );

          final Widget refresh = IconButton.outlined(
            tooltip: 'Atualizar assinatura',
            onPressed: loading ? null : onRefresh,
            icon: loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh_rounded),
          );

          if (compact) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                copy,
                const SizedBox(height: BlackGoldSpace.md),
                Align(alignment: Alignment.centerLeft, child: refresh),
              ],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: BlackGoldSpace.lg),
              refresh,
            ],
          );
        },
      ),
    );
  }
}

class _PlanHero extends StatelessWidget {
  const _PlanHero({required this.snapshot});

  final SubscriptionEntitlementSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final SubscriptionStateInfo state = snapshot.subscription;
    final _StateVisual visual = _stateVisual(state.effectiveStatus);
    final String trialText = state.effectiveStatus == 'trialing'
        ? '${state.trialDaysRemaining} dia${state.trialDaysRemaining == 1 ? '' : 's'} restantes no trial'
        : visual.subtitle;

    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.xl),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.hero),
        border: Border.all(color: visual.color.withValues(alpha: 0.42)),
        boxShadow: <BoxShadow>[
          ...BlackGoldEffects.cardShadow,
          BoxShadow(
            color: visual.color.withValues(alpha: 0.08),
            blurRadius: 28,
            spreadRadius: -8,
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final Widget copy = Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    snapshot.plan.displayName,
                    style: const TextStyle(
                      color: AppColors.text,
                      fontSize: 27,
                      height: 1.05,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: BlackGoldSpace.xs),
                  Text(
                    trialText,
                    style: TextStyle(
                      color: visual.color,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ],
              );

              if (constraints.maxWidth < BlackGoldBreakpoints.mobile) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    copy,
                    const SizedBox(height: BlackGoldSpace.sm),
                    _Pill(label: visual.label, color: visual.color),
                  ],
                );
              }

              return Row(
                children: <Widget>[
                  Expanded(child: copy),
                  _Pill(label: visual.label, color: visual.color),
                ],
              );
            },
          ),
          const SizedBox(height: BlackGoldSpace.md),
          Container(
            padding: const EdgeInsets.all(BlackGoldSpace.md),
            decoration: BoxDecoration(
              color: AppColors.blackSoft,
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Icon(
                  state.writeEnabled
                      ? Icons.lock_open_rounded
                      : Icons.lock_outline_rounded,
                  color: state.writeEnabled
                      ? AppColors.success
                      : AppColors.warning,
                  size: 20,
                ),
                const SizedBox(width: BlackGoldSpace.sm),
                Expanded(
                  child: Text(
                    state.writeEnabled
                        ? 'Novas operações comerciais estão liberadas pelos gates do servidor.'
                        : 'Novas operações comerciais estão bloqueadas pelo estado atual da assinatura. Seus dados continuam preservados.',
                    style: const TextStyle(
                      color: AppColors.muted,
                      height: 1.45,
                    ),
                  ),
                ),
              ],
            ),
          ),
          if (state.trialEndsAt != null && state.effectiveStatus == 'trialing') ...<Widget>[
            const SizedBox(height: BlackGoldSpace.sm),
            Text(
              'Trial até ${_formatDate(state.trialEndsAt!)}',
              style: const TextStyle(
                color: AppColors.mutedSoft,
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _CommercialSummary extends StatelessWidget {
  const _CommercialSummary({required this.snapshot, required this.readiness});

  final SubscriptionEntitlementSnapshot snapshot;
  final BillingProviderReadiness? readiness;

  @override
  Widget build(BuildContext context) {
    final List<_SummaryData> items = <_SummaryData>[
      _SummaryData(
        Icons.groups_rounded,
        '${snapshot.usage.students}/${snapshot.usage.studentLimit}',
        'Alunos',
        '${snapshot.usage.studentRemaining} disponíveis',
      ),
      _SummaryData(
        Icons.badge_rounded,
        '${snapshot.usage.members}/${snapshot.usage.memberLimit}',
        'Equipe',
        '${snapshot.usage.memberRemaining} disponíveis',
      ),
      _SummaryData(
        Icons.workspace_premium_rounded,
        snapshot.subscription.effectiveStatus.toUpperCase(),
        'Entitlement',
        snapshot.subscription.writeEnabled ? 'escrita liberada' : 'escrita bloqueada',
      ),
      _SummaryData(
        Icons.payments_rounded,
        readiness?.checkout.ready == true ? 'PRONTO' : 'BLOQUEADO',
        'Checkout',
        readiness?.provider.displayName ?? 'aguardando leitura',
      ),
    ];

    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final int columns = constraints.maxWidth >= 1040
            ? 4
            : constraints.maxWidth >= BlackGoldBreakpoints.mobile
                ? 2
                : 1;
        const double gap = BlackGoldSpace.sm;
        final double width =
            (constraints.maxWidth - gap * (columns - 1)) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: items
              .map((item) => SizedBox(width: width, child: _SummaryCard(data: item)))
              .toList(growable: false),
        );
      },
    );
  }
}

class _SummaryData {
  const _SummaryData(this.icon, this.value, this.label, this.caption);

  final IconData icon;
  final String value;
  final String label;
  final String caption;
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.data});

  final _SummaryData data;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        border: Border.all(color: AppColors.border),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Row(
        children: <Widget>[
          Container(
            width: 42,
            height: 42,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(color: AppColors.border),
            ),
            child: Icon(data.icon, color: AppColors.goldSoft),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  data.value,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontWeight: FontWeight.w900,
                    fontSize: 18,
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.xxs),
                Text(
                  data.label,
                  style: const TextStyle(
                    color: AppColors.goldSoft,
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  data.caption,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.mutedSoft,
                    fontSize: 10,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _BillingReadinessCard extends StatelessWidget {
  const _BillingReadinessCard({required this.readiness});

  final BillingProviderReadiness readiness;

  @override
  Widget build(BuildContext context) {
    final BillingProviderDescriptor provider = readiness.provider;
    final bool credentialsReady = readiness.credentials.configured;
    final bool pricingReady = readiness.pricing.promoted;
    final bool checkoutReady = readiness.checkout.ready;

    return _Card(
      icon: Icons.account_balance_wallet_rounded,
      title: 'Cobrança online',
      subtitle: 'Provedor selecionado e gates de prontidão',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          LayoutBuilder(
            builder: (BuildContext context, BoxConstraints constraints) {
              final Widget providerCopy = Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Text(
                    provider.displayName,
                    style: const TextStyle(
                      color: AppColors.text,
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                    ),
                  ),
                  const SizedBox(height: BlackGoldSpace.xxs),
                  Text(
                    '${readiness.scope} • evidência ${provider.evidenceVersion}',
                    style: const TextStyle(
                      color: AppColors.mutedSoft,
                      fontSize: 11,
                    ),
                  ),
                ],
              );

              final Widget pill = _Pill(
                label: checkoutReady ? 'CHECKOUT PRONTO' : 'AINDA BLOQUEADO',
                color: checkoutReady ? AppColors.success : AppColors.warning,
              );

              if (constraints.maxWidth < BlackGoldBreakpoints.mobile) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    providerCopy,
                    const SizedBox(height: BlackGoldSpace.sm),
                    pill,
                  ],
                );
              }

              return Row(
                children: <Widget>[
                  Expanded(child: providerCopy),
                  pill,
                ],
              );
            },
          ),
          const SizedBox(height: BlackGoldSpace.md),
          _GateLine(
            label: 'Seleção do provedor',
            passed: provider.selectionState == 'active',
            detail: provider.selectionState == 'active'
                ? 'Autoridade externa verificada e ativada.'
                : 'Selecionado para o Brasil, aguardando a fronteira externa de credenciais.',
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          _GateLine(
            label: 'Credenciais',
            passed: credentialsReady,
            detail: credentialsReady
                ? 'Credencial externa validada sem exposição ao Flutter.'
                : 'Pendente. Nenhum segredo foi exposto ao aplicativo.',
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          _GateLine(
            label: 'Preço comercial',
            passed: pricingReady,
            detail: pricingReady
                ? '${readiness.pricing.activePriceCount} preço(s) promovido(s) pelo servidor.'
                : 'UNFROZEN — nenhum valor será inventado nem enviado pelo cliente.',
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          _GateLine(
            label: 'Checkout',
            passed: checkoutReady,
            detail: checkoutReady
                ? 'Checkout autorizado pelos gates de provedor + preço.'
                : 'Bloqueado até credencial e preço terem autoridade comprovada.',
          ),
          const SizedBox(height: BlackGoldSpace.md),
          Wrap(
            spacing: BlackGoldSpace.xs,
            runSpacing: BlackGoldSpace.xs,
            children: <Widget>[
              if (provider.capability('recurring_subscriptions'))
                const _Capability(label: 'Recorrência'),
              if (provider.capability('credit_card_recurring'))
                const _Capability(label: 'Cartão recorrente'),
              if (provider.capability('pix')) const _Capability(label: 'Pix'),
              if (provider.capability('pix_automatic'))
                const _Capability(label: 'Pix Automático'),
              if (provider.capability('hosted_checkout'))
                const _Capability(label: 'Checkout hospedado'),
              if (provider.capability('sandbox')) const _Capability(label: 'Sandbox'),
              if (provider.capability('webhooks')) const _Capability(label: 'Webhooks'),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const _AuthorityLine(
            icon: Icons.price_check_rounded,
            text:
                'O valor da cobrança vem somente do preço promovido no banco. O Flutter não pode informar o valor ao checkout.',
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          const _AuthorityLine(
            icon: Icons.key_off_rounded,
            text:
                'Segredos do provedor ficam fora do aplicativo. A ativação exige uma autoridade externa verificada.',
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          const _AuthorityLine(
            icon: Icons.swap_horiz_rounded,
            text: 'Não existe fallback silencioso para outro provedor de pagamento.',
          ),
        ],
      ),
    );
  }
}

class _GateLine extends StatelessWidget {
  const _GateLine({
    required this.label,
    required this.passed,
    required this.detail,
  });

  final String label;
  final bool passed;
  final String detail;

  @override
  Widget build(BuildContext context) {
    final Color color = passed ? AppColors.success : AppColors.warning;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.055),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(color: color.withValues(alpha: 0.22)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            passed ? Icons.check_circle_rounded : Icons.hourglass_top_rounded,
            color: color,
            size: 19,
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.xxs),
                Text(
                  detail,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 12,
                    height: 1.4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _Capability extends StatelessWidget {
  const _Capability({required this.label});

  final String label;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(color: AppColors.border),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: AppColors.goldSoft,
          fontSize: 11,
          fontWeight: FontWeight.w800,
        ),
      ),
    );
  }
}

class _Pill extends StatelessWidget {
  const _Pill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 7),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _UsageCard extends StatelessWidget {
  const _UsageCard({required this.snapshot});

  final SubscriptionEntitlementSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    final SubscriptionUsageInfo usage = snapshot.usage;
    return _Card(
      icon: Icons.bar_chart_rounded,
      title: 'Uso e limites',
      subtitle: 'Capacidade validada diretamente pelo backend',
      child: Column(
        children: <Widget>[
          _UsageLine(
            label: 'Alunos',
            used: usage.students,
            limit: usage.studentLimit,
            remaining: usage.studentRemaining,
            ratio: usage.studentRatio,
          ),
          const SizedBox(height: BlackGoldSpace.lg),
          _UsageLine(
            label: 'Equipe',
            used: usage.members,
            limit: usage.memberLimit,
            remaining: usage.memberRemaining,
            ratio: usage.memberRatio,
          ),
        ],
      ),
    );
  }
}

class _UsageLine extends StatelessWidget {
  const _UsageLine({
    required this.label,
    required this.used,
    required this.limit,
    required this.remaining,
    required this.ratio,
  });

  final String label;
  final int used;
  final int limit;
  final int remaining;
  final double ratio;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: <Widget>[
        Row(
          children: <Widget>[
            Expanded(
              child: Text(
                label,
                style: const TextStyle(
                  color: AppColors.text,
                  fontWeight: FontWeight.w900,
                ),
              ),
            ),
            Text(
              '$used / $limit',
              style: const TextStyle(
                color: AppColors.goldSoft,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        ClipRRect(
          borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
          child: LinearProgressIndicator(
            value: ratio,
            minHeight: 8,
            backgroundColor: AppColors.cardSoft,
            color: AppColors.gold,
          ),
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        Text(
          '$remaining disponível${remaining == 1 ? '' : 'is'}',
          style: const TextStyle(
            color: AppColors.mutedSoft,
            fontSize: 11,
          ),
        ),
      ],
    );
  }
}

class _FeaturesCard extends StatelessWidget {
  const _FeaturesCard({required this.snapshot});

  final SubscriptionEntitlementSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    const Map<String, String> labels = <String, String>{
      'coach_action_center': 'Coach Action Center',
      'decision_intelligence': 'Decision Intelligence',
      'smart_templates': 'Smart Templates',
      'training_lineage': 'Training Lineage',
      'student_feedback': 'Feedback do aluno',
    };
    return _Card(
      icon: Icons.extension_rounded,
      title: 'Recursos liberados',
      subtitle: 'Entitlements atuais do seu plano',
      child: Wrap(
        spacing: BlackGoldSpace.xs,
        runSpacing: BlackGoldSpace.xs,
        children: labels.entries.map((MapEntry<String, String> entry) {
          final bool enabled = snapshot.featureEnabled(entry.key);
          final Color color = enabled ? AppColors.success : AppColors.danger;
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 9),
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.07),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(color: color.withValues(alpha: 0.20)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(
                  enabled ? Icons.check_circle_rounded : Icons.block_rounded,
                  size: 16,
                  color: color,
                ),
                const SizedBox(width: BlackGoldSpace.xs),
                Text(
                  entry.value,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 12,
                    fontWeight: FontWeight.w700,
                  ),
                ),
              ],
            ),
          );
        }).toList(growable: false),
      ),
    );
  }
}

class _AuthorityCard extends StatelessWidget {
  const _AuthorityCard({required this.snapshot});

  final SubscriptionEntitlementSnapshot snapshot;

  @override
  Widget build(BuildContext context) {
    return _Card(
      icon: Icons.verified_user_rounded,
      title: 'Autoridade comercial',
      subtitle: 'O cliente não pode se conceder plano ou limite pelo aplicativo',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _AuthorityLine(
            icon: Icons.shield_outlined,
            text: 'Limites de alunos e equipe são impostos no PostgreSQL.',
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          const _AuthorityLine(
            icon: Icons.lock_outline_rounded,
            text: 'Mudança direta de assinatura pelo Flutter é proibida.',
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          _AuthorityLine(
            icon: Icons.sync_alt_rounded,
            text: snapshot.providerBound
                ? 'A assinatura já possui uma autoridade externa vinculada.'
                : 'O núcleo continua independente do provedor; uma integração financeira pode mudar sem reescrever o domínio de alunos e treinos.',
          ),
        ],
      ),
    );
  }
}

class _AuthorityLine extends StatelessWidget {
  const _AuthorityLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, color: AppColors.goldSoft, size: 19),
        const SizedBox(width: BlackGoldSpace.sm),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(color: AppColors.muted, height: 1.45),
          ),
        ),
      ],
    );
  }
}

class _CatalogCard extends StatelessWidget {
  const _CatalogCard({required this.catalog, required this.currentCode});

  final List<SubscriptionPlanCatalogItem> catalog;
  final String currentCode;

  @override
  Widget build(BuildContext context) {
    final List<SubscriptionPlanCatalogItem> paid = catalog
        .where((SubscriptionPlanCatalogItem item) => item.code != 'trial')
        .toList(growable: false);

    return _Card(
      icon: Icons.view_carousel_rounded,
      title: 'Capacidades comerciais',
      subtitle: 'A camada de preço continua desacoplada do domínio de entitlement',
      child: paid.isEmpty
          ? const Text(
              'Nenhum plano comercial disponível.',
              style: TextStyle(color: AppColors.muted),
            )
          : LayoutBuilder(
              builder: (BuildContext context, BoxConstraints constraints) {
                final int columns = constraints.maxWidth >= 900
                    ? 3
                    : constraints.maxWidth >= BlackGoldBreakpoints.mobile
                        ? 2
                        : 1;
                const double gap = BlackGoldSpace.sm;
                final double width =
                    (constraints.maxWidth - gap * (columns - 1)) / columns;

                return Wrap(
                  spacing: gap,
                  runSpacing: gap,
                  children: paid.map((SubscriptionPlanCatalogItem item) {
                    final bool current = item.code == currentCode;
                    return SizedBox(
                      width: width,
                      child: Container(
                        padding: const EdgeInsets.all(BlackGoldSpace.md),
                        decoration: BoxDecoration(
                          color: current
                              ? AppColors.gold.withValues(alpha: 0.07)
                              : AppColors.cardRaised,
                          borderRadius:
                              BorderRadius.circular(BlackGoldRadius.card),
                          border: Border.all(
                            color: current
                                ? AppColors.borderGold
                                : AppColors.border,
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: <Widget>[
                            Text(
                              item.displayName,
                              style: const TextStyle(
                                color: AppColors.text,
                                fontSize: 16,
                                fontWeight: FontWeight.w900,
                              ),
                            ),
                            const SizedBox(height: BlackGoldSpace.xs),
                            Text(
                              'Até ${item.studentLimit} alunos • ${item.memberLimit} usuário${item.memberLimit == 1 ? '' : 's'} de equipe',
                              style: const TextStyle(
                                color: AppColors.muted,
                                fontSize: 12,
                                height: 1.4,
                              ),
                            ),
                            if (current) ...<Widget>[
                              const SizedBox(height: BlackGoldSpace.sm),
                              const Text(
                                'PLANO ATUAL',
                                style: TextStyle(
                                  color: AppColors.goldSoft,
                                  fontSize: 10,
                                  fontWeight: FontWeight.w900,
                                  letterSpacing: 0.6,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  }).toList(growable: false),
                );
              },
            ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.child,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.borderGold),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                width: 40,
                height: 40,
                decoration: BoxDecoration(
                  color: AppColors.gold.withValues(alpha: 0.09),
                  borderRadius: BorderRadius.circular(BlackGoldRadius.control),
                  border: Border.all(color: AppColors.border),
                ),
                child: Icon(icon, color: AppColors.goldSoft, size: 20),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      title,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 18,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        color: AppColors.mutedSoft,
                        fontSize: 12,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          child,
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, this.error = false});

  final String text;
  final bool error;

  @override
  Widget build(BuildContext context) {
    final Color color = error ? AppColors.danger : AppColors.gold;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            error ? Icons.error_outline_rounded : Icons.info_outline_rounded,
            color: color,
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: AppColors.text, height: 1.45),
            ),
          ),
        ],
      ),
    );
  }
}

class _LoadingPanel extends StatelessWidget {
  const _LoadingPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 300,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
      ),
      child: const Column(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          CircularProgressIndicator(color: AppColors.gold),
          SizedBox(height: BlackGoldSpace.md),
          Text(
            'Consultando autoridade comercial…',
            style: TextStyle(color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

class _StateVisual {
  const _StateVisual(this.label, this.subtitle, this.color);

  final String label;
  final String subtitle;
  final Color color;
}

_StateVisual _stateVisual(String state) {
  return switch (state) {
    'trialing' => const _StateVisual(
        'TRIAL', 'Período de avaliação ativo', AppColors.goldSoft),
    'active' => const _StateVisual(
        'ATIVO', 'Assinatura ativa', AppColors.success),
    'grace' => const _StateVisual(
        'TOLERÂNCIA', 'Período de tolerância ativo', AppColors.warning),
    'past_due' => const _StateVisual(
        'PENDENTE', 'Pagamento pendente', AppColors.warning),
    'canceled' => const _StateVisual(
        'CANCELADO', 'Assinatura cancelada', AppColors.danger),
    'expired' => const _StateVisual(
        'EXPIRADO', 'Período disponível encerrado', AppColors.danger),
    _ => const _StateVisual(
        'INDISPONÍVEL', 'Estado comercial indisponível', AppColors.muted),
  };
}

String _formatDate(DateTime value) {
  final DateTime local = value.toLocal();
  String two(int number) => number.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)}/${local.year} ${two(local.hour)}:${two(local.minute)}';
}
