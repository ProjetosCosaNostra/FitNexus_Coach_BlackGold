import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'professor_billing_repository.dart';

class ProfessorCheckoutPage extends StatefulWidget {
  const ProfessorCheckoutPage({super.key});

  @override
  State<ProfessorCheckoutPage> createState() => _ProfessorCheckoutPageState();
}

class _ProfessorCheckoutPageState extends State<ProfessorCheckoutPage> {
  final ProfessorBillingRepository _billing = ProfessorBillingRepository.instance;

  BillingProviderReadiness? _readiness;
  PricingCatalogSnapshot? _pricing;
  bool _loading = true;
  String? _error;
  String? _busyKey;

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
        _billing.fetchReadiness(),
        _billing.fetchPricingCatalog(),
      ]);
      if (!mounted) return;
      setState(() {
        _readiness = result[0] as BillingProviderReadiness;
        _pricing = result[1] as PricingCatalogSnapshot;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _startCheckout(
    PricingCatalogOffer offer,
    String interval,
  ) async {
    final BillingProviderReadiness? readiness = _readiness;
    if (readiness == null || !readiness.checkout.ready) {
      setState(() {
        _error = 'O checkout ainda está em homologação. Assim que credenciais e preços '
            'estiverem autorizados pelo servidor, a assinatura será liberada aqui.';
      });
      return;
    }

    final String key = '${offer.planCode}:$interval';
    setState(() {
      _busyKey = key;
      _error = null;
    });
    try {
      final HostedBillingCheckout checkout = await _billing.createHostedCheckout(
        planCode: offer.planCode,
        billingInterval: interval,
      );
      final bool opened = await launchUrl(
        checkout.checkoutUrl,
        mode: LaunchMode.platformDefault,
      );
      if (!opened) {
        throw StateError('CHECKOUT_BROWSER_OPEN_FAILED');
      }
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _busyKey = null);
    }
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('BILLING_PROVIDER_CREDENTIALS_NOT_READY') ||
        text.contains('BILLING_PROVIDER_EXTERNAL_CREDENTIAL_PENDING') ||
        text.contains('ASAAS_ENVIRONMENT_CREDENTIAL_MISMATCH')) {
      return 'A cobrança online ainda está em homologação segura. Nenhuma cobrança foi criada.';
    }
    if (text.contains('COMMERCIAL_PRICE_NOT_PROMOTED') ||
        text.contains('SERVER_PRICE_AUTHORITY_MISSING') ||
        text.contains('PRICING_DECISION_NOT_CURRENT')) {
      return 'Os preços comerciais ainda não foram promovidos pelo servidor. Nenhum valor será inventado pelo aplicativo.';
    }
    if (text.contains('ASAAS_CHECKOUT_CREATE_FAILED') ||
        text.contains('ASAAS_CHECKOUT_NETWORK_FAILURE')) {
      return 'O provedor de pagamento não conseguiu abrir o checkout agora. Tente novamente em instantes.';
    }
    if (text.contains('CHECKOUT_BROWSER_OPEN_FAILED')) {
      return 'O checkout foi preparado, mas o navegador não pôde ser aberto neste dispositivo.';
    }
    return 'Não foi possível iniciar a assinatura agora. Tente novamente.';
  }

  @override
  Widget build(BuildContext context) {
    final BillingProviderReadiness? readiness = _readiness;
    final PricingCatalogSnapshot? pricing = _pricing;
    final bool checkoutReady = readiness?.checkout.ready ?? false;

    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: const Color(0xFF050505),
        foregroundColor: Colors.white,
        title: const Text('Assinar FitNexus'),
      ),
      body: RefreshIndicator(
        color: const Color(0xFFE1B92F),
        onRefresh: _reload,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 14, 20, 80),
          children: <Widget>[
            const Text(
              'BLACKGOLD BILLING',
              style: TextStyle(
                color: Color(0xFFFFD45A),
                fontSize: 11,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Escolha a capacidade. O preço vem do servidor.',
              style: TextStyle(
                color: Colors.white,
                fontSize: 28,
                height: 1.06,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 9),
            const Text(
              'O FitNexus não recebe dados de cartão. O pagamento abre no checkout hospedado do provedor e a assinatura só muda depois da confirmação financeira no backend.',
              style: TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
            ),
            const SizedBox(height: 18),
            if (_loading && pricing == null)
              const SizedBox(
                height: 320,
                child: Center(child: CircularProgressIndicator()),
              )
            else ...<Widget>[
              _CheckoutReadinessBanner(
                readiness: readiness,
                ready: checkoutReady,
              ),
              if (_error != null) ...<Widget>[
                const SizedBox(height: 12),
                _Notice(text: _error!),
              ],
              const SizedBox(height: 16),
              if (pricing == null || pricing.offers.isEmpty)
                const _Notice(
                  text: 'O catálogo comercial ainda não está disponível no servidor.',
                )
              else
                ...pricing.offers.map((PricingCatalogOffer offer) {
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 14),
                    child: _OfferCard(
                      offer: offer,
                      checkoutReady: checkoutReady,
                      busyKey: _busyKey,
                      onCheckout: _startCheckout,
                    ),
                  );
                }),
              const SizedBox(height: 6),
              const _SecurityNote(),
            ],
          ],
        ),
      ),
    );
  }
}

class _CheckoutReadinessBanner extends StatelessWidget {
  const _CheckoutReadinessBanner({
    required this.readiness,
    required this.ready,
  });

  final BillingProviderReadiness? readiness;
  final bool ready;

  @override
  Widget build(BuildContext context) {
    final Color color = ready ? const Color(0xFF75E39B) : const Color(0xFFFFC85A);
    final String provider = readiness?.provider.displayName ?? 'Provedor';
    return Container(
      padding: const EdgeInsets.all(15),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            ready ? Icons.verified_rounded : Icons.engineering_rounded,
            color: color,
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  ready ? 'Checkout autorizado' : 'Checkout em homologação',
                  style: TextStyle(color: color, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 3),
                Text(
                  ready
                      ? '$provider está liberado pelos gates do servidor.'
                      : 'A tela já está pronta, mas nenhuma cobrança será criada antes dos gates externos ficarem verdes.',
                  style: const TextStyle(color: Color(0xFFBBBBBB), height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _OfferCard extends StatelessWidget {
  const _OfferCard({
    required this.offer,
    required this.checkoutReady,
    required this.busyKey,
    required this.onCheckout,
  });

  final PricingCatalogOffer offer;
  final bool checkoutReady;
  final String? busyKey;
  final Future<void> Function(PricingCatalogOffer offer, String interval) onCheckout;

  @override
  Widget build(BuildContext context) {
    final bool monthlyBusy = busyKey == '${offer.planCode}:month';
    final bool annualBusy = busyKey == '${offer.planCode}:year';
    final bool anyBusy = busyKey != null;

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFF38301A)),
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
                      offer.displayName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 5),
                    Text(
                      'Até ${offer.studentLimit} alunos • ${offer.memberLimit} usuário${offer.memberLimit == 1 ? '' : 's'} de equipe',
                      style: const TextStyle(color: Color(0xFFAAAAAA)),
                    ),
                  ],
                ),
              ),
              const Icon(Icons.workspace_premium_rounded, color: Color(0xFFFFD45A)),
            ],
          ),
          const SizedBox(height: 18),
          _PriceLine(
            label: 'Mensal',
            price: '${_brl(offer.monthlyAmountMinor)}/mês',
            child: FilledButton(
              onPressed: !checkoutReady || anyBusy
                  ? null
                  : () => onCheckout(offer, 'month'),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFFE1B92F),
                foregroundColor: Colors.black,
              ),
              child: monthlyBusy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Assinar mensal'),
            ),
          ),
          const Divider(height: 24, color: Color(0xFF2B2B2B)),
          _PriceLine(
            label: 'Anual',
            price: '${_brl(offer.annualAmountMinor)}/ano',
            detail: offer.annualMonthlyEquivalentMinor > 0
                ? 'equivale a ${_brl(offer.annualMonthlyEquivalentMinor)}/mês'
                : null,
            child: FilledButton.tonal(
              onPressed: !checkoutReady || anyBusy
                  ? null
                  : () => onCheckout(offer, 'year'),
              child: annualBusy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('Assinar anual'),
            ),
          ),
          if (offer.annualSavingsMinor > 0) ...<Widget>[
            const SizedBox(height: 10),
            Text(
              'Economia anual: ${_brl(offer.annualSavingsMinor)}',
              style: const TextStyle(
                color: Color(0xFF75E39B),
                fontWeight: FontWeight.w800,
                fontSize: 12,
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _PriceLine extends StatelessWidget {
  const _PriceLine({
    required this.label,
    required this.price,
    required this.child,
    this.detail,
  });

  final String label;
  final String price;
  final String? detail;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 520;
        final Widget priceBlock = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(label, style: const TextStyle(color: Color(0xFF888888))),
            const SizedBox(height: 2),
            Text(
              price,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 19,
                fontWeight: FontWeight.w900,
              ),
            ),
            if (detail != null)
              Text(
                detail!,
                style: const TextStyle(color: Color(0xFF999999), fontSize: 11),
              ),
          ],
        );
        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              priceBlock,
              const SizedBox(height: 10),
              child,
            ],
          );
        }
        return Row(
          children: <Widget>[
            Expanded(child: priceBlock),
            const SizedBox(width: 14),
            child,
          ],
        );
      },
    );
  }
}

class _SecurityNote extends StatelessWidget {
  const _SecurityNote();

  @override
  Widget build(BuildContext context) {
    return const Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(Icons.lock_outline_rounded, color: Color(0xFF8EBBFF), size: 18),
        SizedBox(width: 9),
        Expanded(
          child: Text(
            'Preço, plano, provedor e ativação são validados no backend. O retorno do navegador não ativa a assinatura; a confirmação financeira é assíncrona.',
            style: TextStyle(color: Color(0xFF8E8E8E), fontSize: 12, height: 1.4),
          ),
        ),
      ],
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF2A1711),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFF704327)),
      ),
      child: Text(
        text,
        style: const TextStyle(color: Color(0xFFFFC995), height: 1.4),
      ),
    );
  }
}

String _brl(int minor) {
  final String decimal = (minor / 100).toStringAsFixed(2).replaceAll('.', ',');
  return 'R\$ $decimal';
}
