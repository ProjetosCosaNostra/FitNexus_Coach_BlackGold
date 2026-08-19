import 'package:flutter/material.dart';

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
    setState(() {
      _loading = true;
      _error = null;
    });
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
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: const Color(0xFF050505),
        foregroundColor: Colors.white,
        title: const Text('Plano & assinatura'),
      ),
      body: RefreshIndicator(
        color: const Color(0xFFE1B92F),
        onRefresh: _reload,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 100),
          children: <Widget>[
            const Text(
              'BLACKGOLD COMMERCIAL CORE',
              style: TextStyle(
                color: Color(0xFFFFD45A),
                fontSize: 11,
                fontWeight: FontWeight.w900,
                letterSpacing: 1,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Capacidade, trial e recursos do seu espaço FitNexus',
              style: TextStyle(
                color: Colors.white,
                fontSize: 27,
                fontWeight: FontWeight.w900,
                height: 1.08,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Os limites, o provedor e a prontidão do checkout vêm do servidor. O aplicativo não escolhe preço, não guarda segredo do provedor e não ativa cobrança sozinho.',
              style: TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
            ),
            const SizedBox(height: 20),
            if (_loading && snapshot == null)
              const SizedBox(
                height: 300,
                child: Center(child: CircularProgressIndicator()),
              )
            else if (_error != null && snapshot == null)
              _Notice(text: _error!, error: true)
            else if (snapshot != null) ...<Widget>[
              _PlanHero(snapshot: snapshot),
              const SizedBox(height: 16),
              if (_billingReadiness != null) ...<Widget>[
                _BillingReadinessCard(readiness: _billingReadiness!),
                const SizedBox(height: 16),
              ],
              _UsageCard(snapshot: snapshot),
              const SizedBox(height: 16),
              _FeaturesCard(snapshot: snapshot),
              const SizedBox(height: 16),
              _AuthorityCard(snapshot: snapshot),
              const SizedBox(height: 20),
              _CatalogCard(catalog: _catalog, currentCode: snapshot.plan.code),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 14),
                _Notice(text: _error!, error: true),
              ],
            ],
          ],
        ),
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
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF171205), Color(0xFF0C0C0C)],
        ),
        border: Border.all(color: visual.color.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      snapshot.plan.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 25,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      trialText,
                      style: TextStyle(color: visual.color, fontWeight: FontWeight.w800),
                    ),
                  ],
                ),
              ),
              _Pill(label: visual.label, color: visual.color),
            ],
          ),
          const SizedBox(height: 16),
          Text(
            state.writeEnabled
                ? 'Novas operações comerciais estão liberadas pelos gates do servidor.'
                : 'Novas operações comerciais estão bloqueadas pelo estado atual da assinatura. Seus dados continuam preservados.',
            style: const TextStyle(color: Color(0xFFBBBBBB), height: 1.4),
          ),
          if (state.trialEndsAt != null && state.effectiveStatus == 'trialing') ...<Widget>[
            const SizedBox(height: 8),
            Text(
              'Trial até ${_formatDate(state.trialEndsAt!)}',
              style: const TextStyle(color: Color(0xFF888888), fontSize: 12),
            ),
          ],
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
      title: 'Cobrança online',
      subtitle: 'Provedor selecionado e gates que ainda precisam estar verdes',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Row(
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      provider.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '${readiness.scope} • evidência ${provider.evidenceVersion}',
                      style: const TextStyle(color: Color(0xFF888888), fontSize: 11),
                    ),
                  ],
                ),
              ),
              _Pill(
                label: checkoutReady ? 'CHECKOUT PRONTO' : 'AINDA BLOQUEADO',
                color: checkoutReady ? const Color(0xFF75E39B) : const Color(0xFFFFC85A),
              ),
            ],
          ),
          const SizedBox(height: 16),
          _GateLine(
            label: 'Seleção do provedor',
            passed: provider.selectionState == 'active',
            detail: provider.selectionState == 'active'
                ? 'Autoridade externa verificada e ativada.'
                : 'Selecionado para o Brasil, aguardando a fronteira externa de credenciais.',
          ),
          const SizedBox(height: 10),
          _GateLine(
            label: 'Credenciais',
            passed: credentialsReady,
            detail: credentialsReady
                ? 'Credencial externa validada sem exposição ao Flutter.'
                : 'Pendente. Nenhum segredo foi exposto ao aplicativo.',
          ),
          const SizedBox(height: 10),
          _GateLine(
            label: 'Preço comercial',
            passed: pricingReady,
            detail: pricingReady
                ? '${readiness.pricing.activePriceCount} preço(s) promovido(s) pelo servidor.'
                : 'UNFROZEN — nenhum valor será inventado nem enviado pelo cliente.',
          ),
          const SizedBox(height: 10),
          _GateLine(
            label: 'Checkout',
            passed: checkoutReady,
            detail: checkoutReady
                ? 'Checkout autorizado pelos gates de provedor + preço.'
                : 'Bloqueado até credencial e preço terem autoridade comprovada.',
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
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
          const SizedBox(height: 14),
          const _AuthorityLine(
            icon: Icons.price_check_rounded,
            text: 'O valor da cobrança vem somente do preço promovido no banco. O Flutter não pode informar o valor ao checkout.',
          ),
          const SizedBox(height: 9),
          const _AuthorityLine(
            icon: Icons.key_off_rounded,
            text: 'Segredos do provedor ficam fora do aplicativo. A ativação exige uma autoridade externa verificada.',
          ),
          const SizedBox(height: 9),
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
    final Color color = passed ? const Color(0xFF75E39B) : const Color(0xFFFFC85A);
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(
          passed ? Icons.check_circle_rounded : Icons.hourglass_top_rounded,
          color: color,
          size: 19,
        ),
        const SizedBox(width: 9),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                label,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900),
              ),
              const SizedBox(height: 2),
              Text(
                detail,
                style: const TextStyle(color: Color(0xFF999999), fontSize: 12, height: 1.35),
              ),
            ],
          ),
        ),
      ],
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
        color: const Color(0xFF101B23),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0xFF29475F)),
      ),
      child: Text(
        label,
        style: const TextStyle(
          color: Color(0xFF9CCEFF),
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
        borderRadius: BorderRadius.circular(999),
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
          const SizedBox(height: 18),
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
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w900),
              ),
            ),
            Text(
              '$used / $limit',
              style: const TextStyle(color: Color(0xFFFFD45A), fontWeight: FontWeight.w900),
            ),
          ],
        ),
        const SizedBox(height: 8),
        LinearProgressIndicator(
          value: ratio,
          minHeight: 8,
          borderRadius: BorderRadius.circular(999),
          backgroundColor: const Color(0xFF262626),
          color: const Color(0xFFE1B92F),
        ),
        const SizedBox(height: 7),
        Text(
          '$remaining disponível${remaining == 1 ? '' : 'is'}',
          style: const TextStyle(color: Color(0xFF888888), fontSize: 11),
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
      title: 'Recursos liberados',
      subtitle: 'Entitlements atuais do seu plano',
      child: Wrap(
        spacing: 9,
        runSpacing: 9,
        children: labels.entries.map((MapEntry<String, String> entry) {
          final bool enabled = snapshot.featureEnabled(entry.key);
          return Container(
            padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 9),
            decoration: BoxDecoration(
              color: enabled ? const Color(0xFF102018) : const Color(0xFF211313),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(
                  enabled ? Icons.check_circle_rounded : Icons.block_rounded,
                  size: 16,
                  color: enabled ? const Color(0xFF75E39B) : const Color(0xFFFF8B8B),
                ),
                const SizedBox(width: 7),
                Text(entry.value),
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
      title: 'Autoridade comercial',
      subtitle: 'O cliente não pode se conceder plano ou limite pelo aplicativo',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          const _AuthorityLine(
            icon: Icons.shield_outlined,
            text: 'Limites de alunos e equipe são impostos no PostgreSQL.',
          ),
          const SizedBox(height: 9),
          const _AuthorityLine(
            icon: Icons.lock_outline_rounded,
            text: 'Mudança direta de assinatura pelo Flutter é proibida.',
          ),
          const SizedBox(height: 9),
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
        Icon(icon, color: const Color(0xFF8EBBFF), size: 19),
        const SizedBox(width: 9),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(color: Color(0xFFBBBBBB), height: 1.4),
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
      title: 'Capacidades comerciais',
      subtitle: 'A camada de preço continua desacoplada do domínio de entitlement',
      child: paid.isEmpty
          ? const Text(
              'Nenhum plano comercial disponível.',
              style: TextStyle(color: Color(0xFF888888)),
            )
          : Wrap(
              spacing: 10,
              runSpacing: 10,
              children: paid.map((SubscriptionPlanCatalogItem item) {
                final bool current = item.code == currentCode;
                return Container(
                  width: 220,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: current ? const Color(0xFF1B1708) : const Color(0xFF151515),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(
                      color: current ? const Color(0xFFE1B92F) : const Color(0xFF2D2D2D),
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      Text(
                        item.displayName,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.w900,
                        ),
                      ),
                      const SizedBox(height: 7),
                      Text(
                        'Até ${item.studentLimit} alunos • ${item.memberLimit} usuário${item.memberLimit == 1 ? '' : 's'} de equipe',
                        style: const TextStyle(
                          color: Color(0xFFAAAAAA),
                          fontSize: 12,
                          height: 1.4,
                        ),
                      ),
                      if (current) ...<Widget>[
                        const SizedBox(height: 9),
                        const Text(
                          'PLANO ATUAL',
                          style: TextStyle(
                            color: Color(0xFFFFD45A),
                            fontSize: 10,
                            fontWeight: FontWeight.w900,
                          ),
                        ),
                      ],
                    ],
                  ),
                );
              }).toList(growable: false),
            ),
    );
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.title, required this.subtitle, required this.child});

  final String title;
  final String subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFF2C2A22)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: <Widget>[
          Text(
            title,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            subtitle,
            style: const TextStyle(color: Color(0xFF888888), fontSize: 12),
          ),
          const SizedBox(height: 15),
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
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: error ? const Color(0xFF351515) : const Color(0xFF111111),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        text,
        style: const TextStyle(color: Colors.white, height: 1.4),
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
        'TRIAL', 'Período de avaliação ativo', Color(0xFF8EBBFF)),
    'active' => const _StateVisual(
        'ATIVO', 'Assinatura ativa', Color(0xFF75E39B)),
    'grace' => const _StateVisual(
        'TOLERÂNCIA', 'Período de tolerância ativo', Color(0xFFFFC85A)),
    'past_due' => const _StateVisual(
        'PENDENTE', 'Pagamento pendente', Color(0xFFFF9B6A)),
    'canceled' => const _StateVisual(
        'CANCELADO', 'Assinatura cancelada', Color(0xFFFF8B8B)),
    'expired' => const _StateVisual(
        'EXPIRADO', 'Período disponível encerrado', Color(0xFFFF8B8B)),
    _ => const _StateVisual(
        'INDISPONÍVEL', 'Estado comercial indisponível', Color(0xFFAAAAAA)),
  };
}

String _formatDate(DateTime value) {
  final DateTime local = value.toLocal();
  String two(int number) => number.toString().padLeft(2, '0');
  return '${two(local.day)}/${two(local.month)}/${local.year} ${two(local.hour)}:${two(local.minute)}';
}
