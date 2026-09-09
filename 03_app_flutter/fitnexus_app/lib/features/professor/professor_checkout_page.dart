import 'dart:async';

import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
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
    if (mounted) {
      setState(() {
        _loading = true;
        _error = null;
        _notice = null;
      });
    }
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
      setState(() => _error =
          'Não foi possível abrir a central de assinaturas do Google Play.');
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
      backgroundColor: AppColors.black,
      body: Stack(
        children: <Widget>[
          const Positioned.fill(child: _CheckoutAtmosphere()),
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
                  100,
                ),
                children: <Widget>[
                  _CheckoutHeader(
                    androidPlay: _androidPlay,
                    loading: _loading,
                    onRefresh: _reload,
                  ),
                  const SizedBox(height: BlackGoldSpace.lg),
                  _PlayAuthorityBanner(androidPlay: _androidPlay),
                  if (_error != null) ...<Widget>[
                    const SizedBox(height: BlackGoldSpace.sm),
                    _Notice(text: _error!, error: true),
                  ],
                  if (_notice != null) ...<Widget>[
                    const SizedBox(height: BlackGoldSpace.sm),
                    _Notice(text: _notice!, error: false),
                  ],
                  const SizedBox(height: BlackGoldSpace.lg),
                  if (_loading && pricing == null)
                    const _LoadingPanel()
                  else if (pricing == null || pricing.offers.isEmpty)
                    const _Notice(
                      text: 'O catálogo de planos ainda não está disponível.',
                      error: true,
                    )
                  else ...<Widget>[
                    _CatalogSummary(pricing: pricing),
                    const SizedBox(height: BlackGoldSpace.lg),
                    const _SectionHeading(
                      eyebrow: 'ESCOLHA O SEU PLANO',
                      title: 'Capacidade profissional sem surpresa na cobrança',
                      subtitle:
                          'No Android, o preço exibido e a cobrança vêm do Google Play. O FitNexus apenas valida a compra e libera o entitlement da conta.',
                    ),
                    const SizedBox(height: BlackGoldSpace.md),
                    ...pricing.offers.map((PricingCatalogOffer offer) {
                      return Padding(
                        padding:
                            const EdgeInsets.only(bottom: BlackGoldSpace.sm),
                        child: _OfferCard(
                          offer: offer,
                          androidPlay: _androidPlay,
                          monthlyPlayOffer:
                              _playOffers['${offer.planCode}:month'],
                          annualPlayOffer:
                              _playOffers['${offer.planCode}:year'],
                          busyKey: _busyKey,
                          onCheckout: _startPlayPurchase,
                        ),
                      );
                    }),
                  ],
                  if (_androidPlay) ...<Widget>[
                    const SizedBox(height: BlackGoldSpace.sm),
                    _AccountActions(
                      busy: _busyKey != null,
                      onRestore: _restorePurchases,
                      onManage: _manageSubscription,
                    ),
                  ],
                  const SizedBox(height: BlackGoldSpace.lg),
                  const _SecurityNote(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _CheckoutAtmosphere extends StatelessWidget {
  const _CheckoutAtmosphere();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: RadialGradient(
            center: const Alignment(0.68, -0.95),
            radius: 1.2,
            colors: <Color>[
              AppColors.gold.withValues(alpha: 0.08),
              Colors.transparent,
            ],
          ),
        ),
      ),
    );
  }
}

class _CheckoutHeader extends StatelessWidget {
  const _CheckoutHeader({
    required this.androidPlay,
    required this.loading,
    required this.onRefresh,
  });

  final bool androidPlay;
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
          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text(
                'FITNEXUS PREMIUM',
                style: TextStyle(
                  color: AppColors.goldSoft,
                  fontSize: 11,
                  fontWeight: FontWeight.w900,
                  letterSpacing: 1.2,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.xs),
              Text(
                androidPlay
                    ? 'Assine com segurança pelo Google Play'
                    : 'O mesmo FitNexus no Web e no PC',
                style: const TextStyle(
                  color: AppColors.text,
                  fontSize: 30,
                  height: 1.06,
                  fontWeight: FontWeight.w900,
                  letterSpacing: -0.7,
                ),
              ),
              const SizedBox(height: BlackGoldSpace.sm),
              Text(
                androidPlay
                    ? 'Preço, renovação, pagamento, cancelamento e recibo são gerenciados pelo Google Play. O FitNexus só libera recursos premium depois da validação da compra.'
                    : 'Use a mesma conta e os mesmos recursos no navegador ou no aplicativo para PC. A compra da assinatura é feita no app Android pelo Google Play e o acesso premium acompanha a conta.',
                style: const TextStyle(
                  color: AppColors.muted,
                  height: 1.5,
                  fontSize: 14,
                ),
              ),
            ],
          );

          final Widget refresh = IconButton.outlined(
            tooltip: 'Atualizar planos',
            onPressed: loading ? null : onRefresh,
            icon: loading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.refresh_rounded),
          );

          if (constraints.maxWidth < BlackGoldBreakpoints.tablet) {
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

class _PlayAuthorityBanner extends StatelessWidget {
  const _PlayAuthorityBanner({required this.androidPlay});

  final bool androidPlay;

  @override
  Widget build(BuildContext context) {
    final Color color = androidPlay ? AppColors.success : AppColors.goldSoft;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: color.withValues(alpha: 0.10),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
            ),
            child: Icon(
              androidPlay ? Icons.shop_rounded : Icons.devices_rounded,
              color: color,
            ),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  androidPlay ? 'Google Play Billing' : 'Conta multiplataforma',
                  style: TextStyle(
                    color: color,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.xxs),
                Text(
                  androidPlay
                      ? 'A cobrança acontece somente dentro do fluxo oficial do Google Play.'
                      : 'Web e PC usam o mesmo SaaS e o mesmo acesso premium da conta.',
                  style: const TextStyle(
                    color: AppColors.muted,
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

class _CatalogSummary extends StatelessWidget {
  const _CatalogSummary({required this.pricing});

  final PricingCatalogSnapshot pricing;

  @override
  Widget build(BuildContext context) {
    final List<_SummaryData> data = <_SummaryData>[
      _SummaryData(
        Icons.layers_rounded,
        '${pricing.offers.length}',
        'Planos',
        'no catálogo',
      ),
      _SummaryData(
        Icons.currency_exchange_rounded,
        pricing.currency,
        'Moeda',
        pricing.mode,
      ),
      _SummaryData(
        Icons.verified_rounded,
        pricing.decisionVersion.isEmpty ? '—' : pricing.decisionVersion,
        'Autoridade',
        'decisão de preço',
      ),
      _SummaryData(
        Icons.calendar_month_rounded,
        pricing.annualStrategy.isEmpty ? '—' : pricing.annualStrategy,
        'Anual',
        'estratégia comercial',
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
          children: data
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
              color: AppColors.gold.withValues(alpha: 0.09),
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
                    fontSize: 17,
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

class _SectionHeading extends StatelessWidget {
  const _SectionHeading({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
  });

  final String eyebrow;
  final String title;
  final String subtitle;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          eyebrow,
          style: const TextStyle(
            color: AppColors.goldSoft,
            fontSize: 11,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.15,
          ),
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        Text(
          title,
          style: const TextStyle(
            color: AppColors.text,
            fontSize: 24,
            fontWeight: FontWeight.w900,
            height: 1.08,
          ),
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        Text(
          subtitle,
          style: const TextStyle(color: AppColors.muted, height: 1.45),
        ),
      ],
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
  final Future<void> Function(PricingCatalogOffer offer, String interval)
      onCheckout;

  @override
  Widget build(BuildContext context) {
    final bool monthlyBusy = busyKey == '${offer.planCode}:month';
    final bool annualBusy = busyKey == '${offer.planCode}:year';
    final bool anyBusy = busyKey != null;

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
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  gradient: BlackGoldEffects.goldGradient,
                  borderRadius: BorderRadius.circular(BlackGoldRadius.card),
                  boxShadow: BlackGoldEffects.goldGlow,
                ),
                child: const Icon(
                  Icons.workspace_premium_rounded,
                  color: Colors.black,
                ),
              ),
              const SizedBox(width: BlackGoldSpace.sm),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      offer.displayName,
                      style: const TextStyle(
                        color: AppColors.text,
                        fontSize: 21,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: BlackGoldSpace.xxs),
                    Text(
                      'Até ${offer.studentLimit} alunos • ${offer.memberLimit} usuário${offer.memberLimit == 1 ? '' : 's'} de equipe',
                      style: const TextStyle(
                        color: AppColors.muted,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Divider(height: 1),
          const SizedBox(height: BlackGoldSpace.md),
          _PriceLine(
            label: 'Mensal',
            price: androidPlay
                ? (monthlyPlayOffer?.displayPrice ?? 'Configurar no Play Console')
                : 'Disponível pelo app Android',
            child: FilledButton.icon(
              onPressed: !androidPlay || monthlyPlayOffer == null || anyBusy
                  ? null
                  : () => onCheckout(offer, 'month'),
              icon: monthlyBusy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.shopping_bag_rounded),
              label: Text(androidPlay ? 'Assinar mensal' : 'Google Play'),
            ),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Divider(height: 1),
          const SizedBox(height: BlackGoldSpace.md),
          _PriceLine(
            label: 'Anual',
            price: androidPlay
                ? (annualPlayOffer?.displayPrice ?? 'Configurar no Play Console')
                : 'Disponível pelo app Android',
            child: OutlinedButton.icon(
              onPressed: !androidPlay || annualPlayOffer == null || anyBusy
                  ? null
                  : () => onCheckout(offer, 'year'),
              icon: annualBusy
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.calendar_month_rounded),
              label: Text(androidPlay ? 'Assinar anual' : 'Google Play'),
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
        final Widget priceBlock = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              label.toUpperCase(),
              style: const TextStyle(
                color: AppColors.goldSoft,
                fontSize: 10,
                fontWeight: FontWeight.w900,
                letterSpacing: 0.8,
              ),
            ),
            const SizedBox(height: BlackGoldSpace.xxs),
            Text(
              price,
              style: const TextStyle(
                color: AppColors.text,
                fontSize: 19,
                fontWeight: FontWeight.w900,
              ),
            ),
          ],
        );

        if (constraints.maxWidth < BlackGoldBreakpoints.mobile) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: <Widget>[
              priceBlock,
              const SizedBox(height: BlackGoldSpace.sm),
              child,
            ],
          );
        }

        return Row(
          children: <Widget>[
            Expanded(child: priceBlock),
            const SizedBox(width: BlackGoldSpace.md),
            child,
          ],
        );
      },
    );
  }
}

class _AccountActions extends StatelessWidget {
  const _AccountActions({
    required this.busy,
    required this.onRestore,
    required this.onManage,
  });

  final bool busy;
  final Future<void> Function() onRestore;
  final Future<void> Function() onManage;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
      ),
      child: Wrap(
        spacing: BlackGoldSpace.sm,
        runSpacing: BlackGoldSpace.sm,
        children: <Widget>[
          OutlinedButton.icon(
            onPressed: busy ? null : onRestore,
            icon: const Icon(Icons.restore_rounded),
            label: const Text('Restaurar assinatura'),
          ),
          TextButton.icon(
            onPressed: onManage,
            icon: const Icon(Icons.open_in_new_rounded),
            label: const Text('Gerenciar ou cancelar no Google Play'),
          ),
        ],
      ),
    );
  }
}

class _SecurityNote extends StatelessWidget {
  const _SecurityNote();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: AppColors.border),
      ),
      child: const Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(Icons.lock_outline_rounded, color: AppColors.goldSoft, size: 18),
          SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Text(
              'No Android, o FitNexus não recebe dados de cartão. A compra é processada pelo Google Play e o acesso premium só é reconhecido depois da validação da transação.',
              style: TextStyle(
                color: AppColors.muted,
                fontSize: 12,
                height: 1.45,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _Notice extends StatelessWidget {
  const _Notice({required this.text, required this.error});

  final String text;
  final bool error;

  @override
  Widget build(BuildContext context) {
    final Color color = error ? AppColors.danger : AppColors.success;
    return Container(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.07),
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(color: color.withValues(alpha: 0.30)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(
            error ? Icons.error_outline_rounded : Icons.check_circle_outline_rounded,
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
      height: 320,
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
            'Consultando planos disponíveis…',
            style: TextStyle(color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}
