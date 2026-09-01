import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import 'play_billing_service.dart';
import 'professor_billing_repository.dart';

class ProfessorCheckoutPage extends StatefulWidget {
  const ProfessorCheckoutPage({super.key});

  @override
  State<ProfessorCheckoutPage> createState() => _ProfessorCheckoutPageState();
}

class _ProfessorCheckoutPageState extends State<ProfessorCheckoutPage> {
  final ProfessorBillingRepository _billing = ProfessorBillingRepository.instance;
  final PlayBillingService _play = PlayBillingService.instance;

  PricingCatalogSnapshot? _pricing;
  Map<String, PlaySubscriptionOffer> _playOffers =
      <String, PlaySubscriptionOffer>{};
  StreamSubscription<PlayBillingEvent>? _playEventSubscription;
  bool _loading = true;
  String? _error;
  String? _notice;
  String? _busyKey;

  bool get _androidPlay => _play.isAndroidPlayRuntime;

  @override
  void initState() {
    super.initState();
    _playEventSubscription = _play.events.listen(_onPlayEvent);
    _reload();
  }

  @override
  void dispose() {
    _playEventSubscription?.cancel();
    super.dispose();
  }

  Future<void> _reload() async {
    setState(() {
      _loading = true;
      _error = null;
      _notice = null;
    });
    try {
      final PricingCatalogSnapshot pricing =
          await _billing.fetchPricingCatalog();
      Map<String, PlaySubscriptionOffer> playOffers =
          <String, PlaySubscriptionOffer>{};
      if (_androidPlay) {
        playOffers = await _play.loadOffers();
      }
      if (!mounted) return;
      setState(() {
        _pricing = pricing;
        _playOffers = playOffers;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _onPlayEvent(PlayBillingEvent event) {
    if (!mounted) return;
    setState(() {
      _busyKey = null;
      if (event.type == PlayBillingEventType.error) {
        _error = event.message;
        _notice = null;
      } else {
        _error = null;
        _notice = event.message;
      }
    });
  }

  Future<void> _startPlayPurchase(
    PricingCatalogOffer offer,
    String interval,
  ) async {
    if (!_androidPlay) {
      setState(() {
        _error = 'A compra da assinatura é feita pelo app Android no Google Play. '
            'Depois de assinar, a mesma conta pode usar o FitNexus no Web e no PC.';
      });
      return;
    }

    final String key = '${offer.planCode}:$interval';
    setState(() {
      _busyKey = key;
      _error = null;
      _notice = null;
    });
    try {
      await _play.buy(
        planCode: offer.planCode,
        billingInterval: interval,
      );
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _busyKey = null;
        _error = _friendlyError(error);
      });
    }
  }

  Future<void> _restorePurchases() async {
    if (!_androidPlay) return;
    setState(() {
      _error = null;
      _notice = 'Consultando suas assinaturas no Google Play...';
    });
    try {
      await _play.restore();
    } catch (error) {
      if (!mounted) return;
      setState(() => _error = _friendlyError(error));
    }
  }

  Future<void> _manageSubscription() async {
    final Uri uri = Uri.parse(
      'https://play.google.com/store/account/subscriptions'
      '?package=br.com.lafamigliaplayworks.fitnexuscoach',
    );
    if (!await launchUrl(uri, mode: LaunchMode.platformDefault)) {
      if (!mounted) return;
      setState(() => _error = 'Não foi possível abrir a central de assinaturas do Google Play.');
    }
  }

  String _friendlyError(Object error) {
    final String text = error.toString();
    if (text.contains('GOOGLE_PLAY_PRODUCTS_NOT_CONFIGURED') ||
        text.contains('GOOGLE_PLAY_BASE_PLAN_NOT_CONFIGURED')) {
      return 'Os produtos da assinatura ainda precisam ser ativados no Play Console. '
          'O app já está preparado e não cria cobrança fora do Google Play.';
    }
    if (text.contains('GOOGLE_PLAY_BILLING_UNAVAILABLE')) {
      return 'O Google Play Billing não está disponível neste dispositivo. '
          'Use uma instalação do FitNexus entregue pelo Google Play.';
    }
    if (text.contains('GOOGLE_PLAY_PRODUCT_QUERY_FAILED')) {
      return 'O Google Play não conseguiu carregar os planos agora. Tente novamente.';
    }
    if (text.contains('GOOGLE_PLAY_BILLING_FLOW_NOT_LAUNCHED')) {
      return 'O Google Play não conseguiu abrir a compra. Tente novamente.';
    }
    if (text.contains('GOOGLE_PLAY_BILLING_ANDROID_ONLY')) {
      return 'A assinatura é comprada pelo app Android no Google Play. '
          'A mesma conta continua disponível no Web e no PC.';
    }
    return 'Não foi possível iniciar a assinatura agora. Tente novamente.';
  }

  @override
  Widget build(BuildContext context) {
    final PricingCatalogSnapshot? pricing = _pricing;

    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: const Color(0xFF050505),
        foregroundColor: Colors.white,
        title: const Text('Planos FitNexus'),
      ),
      body: RefreshIndicator(
        color: const Color(0xFFE1B92F),
        onRefresh: _reload,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(20, 14, 20, 80),
          children: <Widget>[
            const Text(
              'FITNEXUS PREMIUM',
              style: TextStyle(
                color: Color(0xFFFFD45A),
                fontSize: 11,
                fontWeight: FontWeight.w900,
                letterSpacing: 1.1,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              _androidPlay
                  ? 'Assine com segurança pelo Google Play.'
                  : 'O mesmo FitNexus no Web e no PC.',
              style: const TextStyle(
                color: Colors.white,
                fontSize: 28,
                height: 1.06,
                fontWeight: FontWeight.w900,
              ),
            ),
            const SizedBox(height: 9),
            Text(
              _androidPlay
                  ? 'Preço, renovação, pagamento, cancelamento e recibo são gerenciados pelo Google Play. O FitNexus só libera recursos premium depois da validação da compra.'
                  : 'Use a mesma conta e os mesmos recursos no navegador ou no aplicativo para PC. A compra da assinatura é feita no app Android pelo Google Play e o acesso premium acompanha a conta.',
              style: const TextStyle(color: Color(0xFFAAAAAA), height: 1.45),
            ),
            const SizedBox(height: 18),
            _PlayAuthorityBanner(androidPlay: _androidPlay),
            if (_error != null) ...<Widget>[
              const SizedBox(height: 12),
              _Notice(text: _error!, error: true),
            ],
            if (_notice != null) ...<Widget>[
              const SizedBox(height: 12),
              _Notice(text: _notice!, error: false),
            ],
            const SizedBox(height: 16),
            if (_loading && pricing == null)
              const SizedBox(
                height: 320,
                child: Center(child: CircularProgressIndicator()),
              )
            else if (pricing == null || pricing.offers.isEmpty)
              const _Notice(
                text: 'O catálogo de planos ainda não está disponível.',
                error: true,
              )
            else
              ...pricing.offers.map((PricingCatalogOffer offer) {
                return Padding(
                  padding: const EdgeInsets.only(bottom: 14),
                  child: _OfferCard(
                    offer: offer,
                    androidPlay: _androidPlay,
                    monthlyPlayOffer: _playOffers['${offer.planCode}:month'],
                    annualPlayOffer: _playOffers['${offer.planCode}:year'],
                    busyKey: _busyKey,
                    onCheckout: _startPlayPurchase,
                  ),
                );
              }),
            const SizedBox(height: 6),
            if (_androidPlay) ...<Widget>[
              OutlinedButton.icon(
                onPressed: _busyKey == null ? _restorePurchases : null,
                icon: const Icon(Icons.restore_rounded),
                label: const Text('Restaurar assinatura'),
              ),
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: _manageSubscription,
                icon: const Icon(Icons.open_in_new_rounded),
                label: const Text('Gerenciar ou cancelar no Google Play'),
              ),
              const SizedBox(height: 12),
            ],
            const _SecurityNote(),
          ],
        ),
      ),
    );
  }
}

class _PlayAuthorityBanner extends StatelessWidget {
  const _PlayAuthorityBanner({required this.androidPlay});

  final bool androidPlay;

  @override
  Widget build(BuildContext context) {
    final Color color = androidPlay
        ? const Color(0xFF75E39B)
        : const Color(0xFF8EBBFF);
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
            androidPlay ? Icons.shop_rounded : Icons.devices_rounded,
            color: color,
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  androidPlay ? 'Google Play Billing' : 'Conta multiplataforma',
                  style: TextStyle(color: color, fontWeight: FontWeight.w900),
                ),
                const SizedBox(height: 3),
                Text(
                  androidPlay
                      ? 'A cobrança acontece somente dentro do fluxo oficial do Google Play.'
                      : 'Web e PC usam o mesmo SaaS e o mesmo acesso premium da conta.',
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
    required this.androidPlay,
    required this.monthlyPlayOffer,
    required this.annualPlayOffer,
    required this.busyKey,
    required this.onCheckout,
  });

  final PricingCatalogOffer offer;
  final bool androidPlay;
  final PlaySubscriptionOffer? monthlyPlayOffer;
  final PlaySubscriptionOffer? annualPlayOffer;
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
            price: androidPlay
                ? (monthlyPlayOffer?.displayPrice ?? 'Configurar no Play Console')
                : 'Disponível pelo app Android',
            child: FilledButton(
              onPressed: !androidPlay || monthlyPlayOffer == null || anyBusy
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
                  : Text(androidPlay ? 'Assinar mensal' : 'Google Play'),
            ),
          ),
          const Divider(height: 24, color: Color(0xFF2B2B2B)),
          _PriceLine(
            label: 'Anual',
            price: androidPlay
                ? (annualPlayOffer?.displayPrice ?? 'Configurar no Play Console')
                : 'Disponível pelo app Android',
            child: FilledButton.tonal(
              onPressed: !androidPlay || annualPlayOffer == null || anyBusy
                  ? null
                  : () => onCheckout(offer, 'year'),
              child: annualBusy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Text(androidPlay ? 'Assinar anual' : 'Google Play'),
            ),
          ),
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
  });

  final String label;
  final String price;
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
            'No Android, o FitNexus não recebe dados de cartão. A compra é processada pelo Google Play e o acesso premium só é reconhecido depois da validação da transação.',
            style: TextStyle(color: Color(0xFF8E8E8E), fontSize: 12, height: 1.4),
          ),
        ),
      ],
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, required this.error});

  final String text;
  final bool error;

  @override
  Widget build(BuildContext context) {
    final Color background = error
        ? const Color(0xFF2A1711)
        : const Color(0xFF102219);
    final Color border = error
        ? const Color(0xFF704327)
        : const Color(0xFF315E43);
    final Color foreground = error
        ? const Color(0xFFFFC995)
        : const Color(0xFF9FE7B7);
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: border),
      ),
      child: Text(
        text,
        style: TextStyle(color: foreground, height: 1.4),
      ),
    );
  }
}
