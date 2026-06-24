import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';

// FitNexus Coach BlackGold Landing Page V11 - copy corrigida, sem promessa falsa e sem termos prematuros.

class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: AppColors.black,
      body: SingleChildScrollView(
        child: Column(
          children: <Widget>[
            _HeroSection(),
            _AudienceSection(),
            _ProductSection(),
            _ConversionSection(),
            _FinalCtaSection(),
          ],
        ),
      ),
    );
  }
}

class _HeroSection extends StatelessWidget {
  const _HeroSection();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final double width = constraints.maxWidth;
        final double screenHeight = MediaQuery.sizeOf(context).height;
        final bool isMobile = width < 720;
        final bool isTablet = width >= 720 && width < 1100;

        final double heroHeight = isMobile
            ? math.max(screenHeight * 0.82, 650)
            : isTablet
                ? math.max(screenHeight * 0.74, 620)
                : math.max(screenHeight * 0.68, 620);

        return SizedBox(
          width: double.infinity,
          height: heroHeight,
          child: Stack(
            fit: StackFit.expand,
            children: <Widget>[
              _HeroBackground(isMobile: isMobile, isTablet: isTablet),
              SafeArea(
                child: _PageShell(
                  horizontalPadding: isMobile ? 18 : 64,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: <Widget>[
                      const SizedBox(height: 18),
                      const _TopBar(),
                      Expanded(
                        child: Align(
                          alignment: isMobile || isTablet
                              ? Alignment.center
                              : Alignment.centerLeft,
                          child: _HeroPanel(
                            usePanel: isMobile || isTablet,
                            showCompactCards: !isMobile,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}

class _HeroBackground extends StatelessWidget {
  final bool isMobile;
  final bool isTablet;

  const _HeroBackground({
    required this.isMobile,
    required this.isTablet,
  });

  @override
  Widget build(BuildContext context) {
    final double opacity = isMobile
        ? 0.38
        : isTablet
            ? 0.58
            : 0.94;

    return Stack(
      fit: StackFit.expand,
      children: <Widget>[
        Opacity(
          opacity: opacity,
          child: Image.asset(
            'assets/images/hero_bg.webp',
            fit: BoxFit.cover,
            alignment: isMobile ? Alignment.centerRight : Alignment.centerRight,
          ),
        ),
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.centerLeft,
              end: Alignment.centerRight,
              stops: const <double>[0.0, 0.34, 0.66, 1.0],
              colors: <Color>[
                Colors.black.withValues(alpha: isMobile ? 0.98 : 0.99),
                Colors.black.withValues(alpha: isMobile ? 0.90 : 0.87),
                Colors.black.withValues(alpha: isMobile ? 0.66 : 0.32),
                Colors.black.withValues(alpha: isMobile ? 0.44 : 0.10),
              ],
            ),
          ),
        ),
        DecoratedBox(
          decoration: BoxDecoration(
            gradient: LinearGradient(
              begin: Alignment.topCenter,
              end: Alignment.bottomCenter,
              stops: const <double>[0.0, 0.70, 1.0],
              colors: <Color>[
                Colors.black.withValues(alpha: 0.04),
                Colors.transparent,
                AppColors.black.withValues(alpha: 0.98),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _AudienceSection extends StatelessWidget {
  const _AudienceSection();

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool isMobile = width < 720;

    return _PageShell(
      horizontalPadding: isMobile ? 18 : 64,
      child: Padding(
        padding: EdgeInsets.only(top: isMobile ? 24 : 34, bottom: isMobile ? 30 : 42),
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _SectionHeader(
              eyebrow: 'PARA QUEM É',
              title: 'Feito para quem quer entregar treino com cara de produto profissional.',
              subtitle:
                  'Para personal, professor e pequeno estúdio que ainda perde tempo com WhatsApp bagunçado, PDF solto ou ficha em papel.',
            ),
            SizedBox(height: 22),
            _AudienceGrid(),
          ],
        ),
      ),
    );
  }
}

class _ProductSection extends StatelessWidget {
  const _ProductSection();

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool isMobile = width < 720;

    return _PageShell(
      horizontalPadding: isMobile ? 18 : 64,
      child: Padding(
        padding: EdgeInsets.only(bottom: isMobile ? 32 : 48),
        child: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            _SectionHeader(
              eyebrow: 'COMO FUNCIONA',
              title: 'Um fluxo simples: o professor monta, o aluno executa.',
              subtitle:
                  'A primeira entrega precisa resolver o básico com qualidade: treino organizado, acesso pelo celular e evolução visível.',
            ),
            SizedBox(height: 24),
            _ProductShowcase(),
          ],
        ),
      ),
    );
  }
}

class _ConversionSection extends StatelessWidget {
  const _ConversionSection();

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool isMobile = width < 720;

    return _PageShell(
      horizontalPadding: isMobile ? 18 : 64,
      child: Padding(
        padding: EdgeInsets.only(bottom: isMobile ? 32 : 48),
        child: const _ConversionPanel(),
      ),
    );
  }
}

class _FinalCtaSection extends StatelessWidget {
  const _FinalCtaSection();

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final bool isMobile = width < 720;

    return _PageShell(
      horizontalPadding: isMobile ? 18 : 64,
      child: Padding(
        padding: EdgeInsets.only(bottom: isMobile ? 44 : 72),
        child: const _FounderOffer(),
      ),
    );
  }
}

class _PageShell extends StatelessWidget {
  final Widget child;
  final double horizontalPadding;

  const _PageShell({
    required this.child,
    required this.horizontalPadding,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 1360),
        child: Padding(
          padding: EdgeInsets.symmetric(horizontal: horizontalPadding),
          child: child,
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    final bool showButtons = MediaQuery.sizeOf(context).width >= 620;

    return Row(
      children: <Widget>[
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(15),
            gradient: const LinearGradient(
              colors: <Color>[AppColors.goldSoft, AppColors.gold],
            ),
            boxShadow: <BoxShadow>[
              BoxShadow(
                color: AppColors.gold.withValues(alpha: 0.28),
                blurRadius: 24,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: const Icon(Icons.fitness_center, color: Colors.black),
        ),
        const SizedBox(width: 14),
        const Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                'FitNexus Coach',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(
                  color: AppColors.text,
                  fontSize: 20,
                  fontWeight: FontWeight.w900,
                ),
              ),
              SizedBox(height: 2),
              Text(
                'BlackGold SaaS Fitness',
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: TextStyle(color: AppColors.muted, fontSize: 12),
              ),
            ],
          ),
        ),
        if (showButtons) ...<Widget>[
          const SizedBox(width: 18),
          const _SmallButton(text: 'Demonstraçãonstração', filled: false, onTap: _emptyAction),
          const SizedBox(width: 10),
          const _SmallButton(text: 'Conhecer projeto', filled: true, onTap: _emptyAction),
        ],
      ],
    );
  }
}

class _HeroPanel extends StatelessWidget {
  final bool usePanel;
  final bool showCompactCards;

  const _HeroPanel({
    required this.usePanel,
    required this.showCompactCards,
  });

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final double maxWidth = width < 720
        ? double.infinity
        : width < 1100
            ? 720
            : 660;

    final Widget content = ConstrainedBox(
      constraints: BoxConstraints(maxWidth: maxWidth),
      child: _HeroCopy(showCompactCards: showCompactCards),
    );

    if (!usePanel) {
      return content;
    }

    return Container(
      width: maxWidth,
      padding: EdgeInsets.all(width < 420 ? 18 : 24),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.70),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white.withValues(alpha: 0.08)),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.50),
            blurRadius: 38,
            offset: const Offset(0, 20),
          ),
        ],
      ),
      child: content,
    );
  }
}

class _HeroCopy extends StatelessWidget {
  final bool showCompactCards;

  const _HeroCopy({required this.showCompactCards});

  @override
  Widget build(BuildContext context) {
    final double width = MediaQuery.sizeOf(context).width;
    final double titleSize = width < 390
        ? 29
        : width < 720
            ? 34
            : width < 1100
                ? 42
                : 52;

    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const _HeroBadge(),
        const SizedBox(height: 18),
        Text(
          'Treinos digitais profissionais para personal, professor e academia.',
          style: TextStyle(
            color: AppColors.text,
            fontSize: titleSize,
            height: 1.03,
            fontWeight: FontWeight.w900,
            letterSpacing: -1.1,
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Pare de entregar treino por papel, PDF ou WhatsApp bagunçado. '
          'Com o FitNexus, o aluno recebe o treino no celular, registra carga e acompanha sua evolução.',
          style: TextStyle(
            color: AppColors.muted,
            fontSize: 16,
            height: 1.48,
          ),
        ),
        const SizedBox(height: 24),
        const Wrap(
          spacing: 14,
          runSpacing: 14,
          children: <Widget>[
            _HeroButton(
              text: 'Ver demonstração',
              icon: Icons.rocket_launch,
              filled: true,
              onTap: _emptyAction,
            ),
            _HeroButton(
              text: 'Como funciona',
              icon: Icons.play_circle_outline,
              filled: false,
              onTap: _emptyAction,
            ),
          ],
        ),
        if (showCompactCards) ...<Widget>[
          const SizedBox(height: 22),
          const _HeroMiniGrid(),
        ] else ...<Widget>[
          const SizedBox(height: 18),
          const _MobileTrustLine(),
        ],
      ],
    );
  }
}

class _HeroBadge extends StatelessWidget {
  const _HeroBadge();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.border),
      ),
      child: const Text(
        'Treino digital organizado para aluno e professor',
        style: TextStyle(
          color: AppColors.goldSoft,
          fontSize: 13,
          fontWeight: FontWeight.w900,
        ),
      ),
    );
  }
}

class _MobileTrustLine extends StatelessWidget {
  const _MobileTrustLine();

  @override
  Widget build(BuildContext context) {
    return const Wrap(
      spacing: 14,
      runSpacing: 10,
      children: <Widget>[
        _TrustChip(icon: Icons.check_circle, text: 'Treino organizado'),
        _TrustChip(icon: Icons.qr_code_2, text: 'Link e QR'),
        _TrustChip(icon: Icons.insights, text: 'Evolução'),
      ],
    );
  }
}

class _TrustChip extends StatelessWidget {
  final IconData icon;
  final String text;

  const _TrustChip({
    required this.icon,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Icon(icon, size: 16, color: AppColors.goldSoft),
        const SizedBox(width: 7),
        Text(
          text,
          style: const TextStyle(
            color: AppColors.text,
            fontSize: 12,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}

class _HeroMiniGrid extends StatelessWidget {
  const _HeroMiniGrid();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool twoColumns = constraints.maxWidth < 620;
        final double itemWidth =
            twoColumns ? (constraints.maxWidth - 12) / 2 : (constraints.maxWidth - 36) / 4;

        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: <Widget>[
            SizedBox(
              width: itemWidth,
              child: const _HeroMiniCard(
                icon: Icons.app_registration,
                title: 'Gestão',
                text: 'Alunos e treinos',
              ),
            ),
            SizedBox(
              width: itemWidth,
              child: const _HeroMiniCard(
                icon: Icons.phone_android,
                title: 'Aluno',
                text: 'Treino no celular',
              ),
            ),
            SizedBox(
              width: itemWidth,
              child: const _HeroMiniCard(
                icon: Icons.qr_code_2,
                title: 'Acesso',
                text: 'Link e QR Code',
              ),
            ),
            SizedBox(
              width: itemWidth,
              child: const _HeroMiniCard(
                icon: Icons.insights,
                title: 'Evolução',
                text: 'Histórico real',
              ),
            ),
          ],
        );
      },
    );
  }
}

class _HeroMiniCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String text;

  const _HeroMiniCard({
    required this.icon,
    required this.title,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 74,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.black.withValues(alpha: 0.38),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
      ),
      child: Row(
        children: <Widget>[
          Icon(icon, color: AppColors.goldSoft, size: 22),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontWeight: FontWeight.w900,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  text,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(color: AppColors.muted, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _AudienceGrid extends StatelessWidget {
  const _AudienceGrid();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        const double gap = 14;
        final int columns = constraints.maxWidth < 560
            ? 1
            : constraints.maxWidth < 980
                ? 2
                : 3;
        final double itemWidth =
            (constraints.maxWidth - (gap * (columns - 1))) / columns;

        return Wrap(
          spacing: gap,
          runSpacing: gap,
          children: <Widget>[
            SizedBox(
              width: itemWidth,
              child: const _AudienceCard(
                icon: Icons.person,
                title: 'Personal trainer',
                text: 'Organize alunos, treinos e evolução sem mensagens soltas.',
              ),
            ),
            SizedBox(
              width: itemWidth,
              child: const _AudienceCard(
                icon: Icons.sports_gymnastics,
                title: 'Professor',
                text: 'Entregue fichas digitais com exercícios, séries e carga.',
              ),
            ),
            SizedBox(
              width: itemWidth,
              child: const _AudienceCard(
                icon: Icons.storefront,
                title: 'Estúdio pequeno',
                text: 'Comece simples e evolua para gestão completa.',
              ),
            ),
          ],
        );
      },
    );
  }
}

class _AudienceCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String text;

  const _AudienceCard({
    required this.icon,
    required this.title,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    final bool compact = MediaQuery.sizeOf(context).width < 720;

    return Container(
      padding: EdgeInsets.all(compact ? 18 : 20),
      decoration: BoxDecoration(
        color: AppColors.blackSoft,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 42,
            height: 42,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.12),
              borderRadius: BorderRadius.circular(14),
              border: Border.all(color: AppColors.border),
            ),
            child: Icon(icon, color: AppColors.goldSoft, size: 22),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: TextStyle(
                    color: AppColors.text,
                    fontSize: compact ? 16 : 17,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 7),
                Text(
                  text,
                  style: TextStyle(
                    color: AppColors.muted,
                    height: 1.42,
                    fontSize: compact ? 13 : 14,
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

class _ProductShowcase extends StatelessWidget {
  const _ProductShowcase();

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool narrow = constraints.maxWidth < 980;

        if (narrow) {
          return const Column(
            children: <Widget>[
              _ProcessPanel(),
              SizedBox(height: 22),
              _DemoPanel(),
            ],
          );
        }

        return const Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Expanded(flex: 10, child: _ProcessPanel()),
            SizedBox(width: 28),
            Expanded(flex: 9, child: _DemoPanel()),
          ],
        );
      },
    );
  }
}

class _ProcessPanel extends StatelessWidget {
  const _ProcessPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(26),
      decoration: BoxDecoration(
        color: AppColors.blackSoft.withValues(alpha: 0.94),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
      ),
      child: const Column(
        children: <Widget>[
          _ProcessStep(
            number: '01',
            title: 'O profissional monta o treino',
            text: 'Cria ficha, séries, repetições, descanso e observações por aluno.',
          ),
          _ProcessConnector(),
          _ProcessStep(
            number: '02',
            title: 'O aluno acessa pelo celular',
            text: 'Recebe o treino por link ou QR Code e registra conclusão e carga.',
          ),
          _ProcessConnector(),
          _ProcessStep(
            number: '03',
            title: 'O sistema registra evolução',
            text: 'Histórico preparado para relatórios, retenção de alunos e IA futura.',
          ),
        ],
      ),
    );
  }
}

class _ProcessStep extends StatelessWidget {
  final String number;
  final String title;
  final String text;

  const _ProcessStep({
    required this.number,
    required this.title,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Container(
          width: 52,
          height: 52,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: AppColors.gold.withValues(alpha: 0.14),
            borderRadius: BorderRadius.circular(18),
            border: Border.all(color: AppColors.border),
          ),
          child: Text(
            number,
            style: const TextStyle(
              color: AppColors.goldSoft,
              fontWeight: FontWeight.w900,
              fontSize: 15,
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(top: 3),
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
                const SizedBox(height: 8),
                Text(
                  text,
                  style: const TextStyle(color: AppColors.muted, height: 1.45),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }
}

class _ProcessConnector extends StatelessWidget {
  const _ProcessConnector();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      alignment: Alignment.centerLeft,
      padding: const EdgeInsets.only(left: 25, top: 8, bottom: 8),
      child: Container(width: 2, height: 22, color: AppColors.border),
    );
  }
}

class _DemoPanel extends StatelessWidget {
  const _DemoPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 560),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.blackSoft.withValues(alpha: 0.96),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: AppColors.border),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.45),
            blurRadius: 34,
            offset: const Offset(0, 20),
          ),
        ],
      ),
      child: const Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              CircleAvatar(
                radius: 22,
                backgroundColor: AppColors.gold,
                child: Icon(Icons.person, color: Colors.black),
              ),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Aluno: Mariana Alves',
                      style: TextStyle(
                        color: AppColors.text,
                        fontWeight: FontWeight.w900,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      'Treino A — Inferiores',
                      style: TextStyle(color: AppColors.muted, fontSize: 13),
                    ),
                  ],
                ),
              ),
              Icon(Icons.qr_code_2, color: AppColors.goldSoft),
            ],
          ),
          SizedBox(height: 22),
          _MetricRow(),
          SizedBox(height: 20),
          _ExerciseItem(
            name: 'Agachamento livre',
            detail: '4 séries • 10 a 12 repetições • descanso 60s',
            done: true,
          ),
          _ExerciseItem(
            name: 'Leg press',
            detail: '4 séries • 12 repetições • carga moderada',
            done: false,
          ),
          _ExerciseItem(
            name: 'Cadeira extensora',
            detail: '3 séries • 12 a 15 repetições • controle total',
            done: false,
          ),
          SizedBox(height: 20),
          _TimerNotice(),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  const _MetricRow();

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: <Widget>[
        Expanded(child: _MetricCard(label: 'Treinos', value: '12')),
        SizedBox(width: 10),
        Expanded(child: _MetricCard(label: 'Conclusão', value: '86%')),
        SizedBox(width: 10),
        Expanded(child: _MetricCard(label: 'Carga', value: '+8kg')),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;

  const _MetricCard({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.06)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            value,
            style: const TextStyle(
              color: AppColors.goldSoft,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(label, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
        ],
      ),
    );
  }
}

class _ExerciseItem extends StatelessWidget {
  final String name;
  final String detail;
  final bool done;

  const _ExerciseItem({
    required this.name,
    required this.detail,
    required this.done,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: done
              ? AppColors.gold.withValues(alpha: 0.55)
              : Colors.white.withValues(alpha: 0.06),
        ),
      ),
      child: Row(
        children: <Widget>[
          Icon(
            done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? AppColors.goldSoft : AppColors.muted,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  name,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  detail,
                  style: const TextStyle(color: AppColors.muted, fontSize: 12),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _TimerNotice extends StatelessWidget {
  const _TimerNotice();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.gold.withValues(alpha: 0.10),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.border),
      ),
      child: const Row(
        children: <Widget>[
          Icon(Icons.timer, color: AppColors.goldSoft),
          SizedBox(width: 10),
          Expanded(
            child: Text(
              'Cronômetro de descanso pronto para o próximo exercício.',
              style: TextStyle(color: AppColors.text),
            ),
          ),
        ],
      ),
    );
  }
}

class _ConversionPanel extends StatelessWidget {
  const _ConversionPanel();

  @override
  Widget build(BuildContext context) {
    final bool mobile = MediaQuery.sizeOf(context).width < 720;

    return Container(
      padding: EdgeInsets.all(mobile ? 22 : 26),
      decoration: BoxDecoration(
        color: AppColors.blackSoft.withValues(alpha: 0.88),
        borderRadius: BorderRadius.circular(30),
        border: Border.all(color: Colors.white.withValues(alpha: 0.07)),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool narrow = constraints.maxWidth < 960;

          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text(
                'Por que isso vende?',
                style: TextStyle(
                  color: AppColors.goldSoft,
                  fontWeight: FontWeight.w900,
                  fontSize: 14,
                  letterSpacing: 0.7,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                'O aluno não vê só uma ficha. Ele percebe organização, acompanhamento e cuidado.',
                style: TextStyle(
                  color: AppColors.text,
                  fontSize: mobile ? 25 : 30,
                  height: 1.12,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 12),
              Text(
                'A proposta precisa ser simples: tirar o treino do improviso e colocar uma experiência clara no celular.',
                style: TextStyle(
                  color: AppColors.muted,
                  fontSize: mobile ? 14 : 16,
                  height: 1.5,
                ),
              ),
            ],
          );

          const Widget bullets = Column(
            children: <Widget>[
              _ConversionBullet(
                icon: Icons.bolt,
                title: 'Valor fácil de entender',
                text: 'Treino organizado no celular, sem PDF perdido e sem conversa bagunçada.',
              ),
              SizedBox(height: 12),
              _ConversionBullet(
                icon: Icons.workspace_premium,
                title: 'Experiência mais profissional',
                text: 'Visual premium para reforçar cuidado, confiança e organização.',
              ),
              SizedBox(height: 12),
              _ConversionBullet(
                icon: Icons.auto_graph,
                title: 'Base preparada',
                text: 'Começa simples, com estrutura para evoluir depois sem prometer o que ainda não está pronto.',
              ),
            ],
          );

          if (narrow) {
            return Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[copy, const SizedBox(height: 22), bullets],
            );
          }

          return Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(flex: 9, child: copy),
              const SizedBox(width: 34),
              const Expanded(flex: 8, child: bullets),
            ],
          );
        },
      ),
    );
  }
}

class _ConversionBullet extends StatelessWidget {
  final IconData icon;
  final String title;
  final String text;

  const _ConversionBullet({
    required this.icon,
    required this.title,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: <Widget>[
        Container(
          width: 46,
          height: 46,
          decoration: BoxDecoration(
            color: AppColors.gold.withValues(alpha: 0.13),
            borderRadius: BorderRadius.circular(15),
            border: Border.all(color: AppColors.border),
          ),
          child: Icon(icon, color: AppColors.goldSoft),
        ),
        const SizedBox(width: 14),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Text(
                title,
                style: const TextStyle(
                  color: AppColors.text,
                  fontWeight: FontWeight.w900,
                  fontSize: 16,
                ),
              ),
              const SizedBox(height: 5),
              Text(
                text,
                style: const TextStyle(color: AppColors.muted, height: 1.35),
              ),
            ],
          ),
        ),
      ],
    );
  }
}

class _FounderOffer extends StatelessWidget {
  const _FounderOffer();

  @override
  Widget build(BuildContext context) {
    final bool mobile = MediaQuery.sizeOf(context).width < 720;

    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(mobile ? 22 : 28),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF1B1608), Color(0xFF0D0D0D)],
        ),
        border: Border.all(color: AppColors.border),
      ),
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool narrow = constraints.maxWidth < 880;

          final Widget copy = Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Text(
                'Comece pelo essencial',
                style: TextStyle(
                  color: AppColors.goldSoft,
                  fontSize: 15,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Transforme a entrega do treino em uma experiência digital mais profissional.',
                style: TextStyle(
                  color: AppColors.text,
                  fontSize: mobile ? 25 : 28,
                  fontWeight: FontWeight.w900,
                  height: 1.15,
                ),
              ),
              const SizedBox(height: 10),
              const Text(
                'Primeira versão focada em personal/professor individual. '
                'O foco agora é entregar uma experiência clara, organizada e profissional para aluno e professor.',
                style: TextStyle(
                  color: AppColors.muted,
                  fontSize: 15,
                  height: 1.5,
                ),
              ),
            ],
          );

          const Widget button = _HeroButton(
            text: 'Ver demonstração',
            icon: Icons.arrow_forward,
            filled: true,
            onTap: _emptyAction,
          );

          if (narrow) {
            return const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                _FounderOfferCopy(),
                SizedBox(height: 18),
                _HeroButton(
                  text: 'Ver demonstração',
                  icon: Icons.arrow_forward,
                  filled: true,
                  onTap: _emptyAction,
                ),
              ],
            );
          }

          return Row(
            children: <Widget>[
              Expanded(child: copy),
              const SizedBox(width: 24),
              button,
            ],
          );
        },
      ),
    );
  }
}

class _FounderOfferCopy extends StatelessWidget {
  const _FounderOfferCopy();

  @override
  Widget build(BuildContext context) {
    final bool mobile = MediaQuery.sizeOf(context).width < 720;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        const Text(
          'Comece pelo essencial',
          style: TextStyle(
            color: AppColors.goldSoft,
            fontSize: 15,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'Transforme a entrega do treino em uma experiência digital mais profissional.',
          style: TextStyle(
            color: AppColors.text,
            fontSize: mobile ? 25 : 28,
            fontWeight: FontWeight.w900,
            height: 1.15,
          ),
        ),
        const SizedBox(height: 10),
        const Text(
          'Primeira versão focada em personal/professor individual. '
          'O foco agora é entregar uma experiência clara, organizada e profissional para aluno e professor.',
          style: TextStyle(
            color: AppColors.muted,
            fontSize: 15,
            height: 1.5,
          ),
        ),
      ],
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String eyebrow;
  final String title;
  final String subtitle;

  const _SectionHeader({
    required this.eyebrow,
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    final bool mobile = MediaQuery.sizeOf(context).width < 720;

    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 920),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            eyebrow,
            style: const TextStyle(
              color: AppColors.goldSoft,
              fontWeight: FontWeight.w900,
              fontSize: 13,
              letterSpacing: 0.8,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            title,
            style: TextStyle(
              color: AppColors.text,
              fontSize: mobile ? 29 : 34,
              height: 1.09,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 12),
          Text(
            subtitle,
            style: TextStyle(
              color: AppColors.muted,
              fontSize: mobile ? 14 : 16,
              height: 1.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _HeroButton extends StatelessWidget {
  final String text;
  final IconData icon;
  final bool filled;
  final VoidCallback onTap;

  const _HeroButton({
    required this.text,
    required this.icon,
    required this.filled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onTap,
      icon: Icon(icon, size: 19),
      label: Text(text),
      style: ElevatedButton.styleFrom(
        backgroundColor: filled ? AppColors.gold : Colors.transparent,
        foregroundColor: filled ? Colors.black : AppColors.goldSoft,
        side: BorderSide(color: filled ? AppColors.gold : AppColors.border),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 17),
        textStyle: const TextStyle(fontWeight: FontWeight.w900, fontSize: 15),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(999)),
      ),
    );
  }
}

class _SmallButton extends StatelessWidget {
  final String text;
  final bool filled;
  final VoidCallback onTap;

  const _SmallButton({
    required this.text,
    required this.filled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return TextButton(
      onPressed: onTap,
      style: TextButton.styleFrom(
        backgroundColor: filled ? AppColors.gold : Colors.transparent,
        foregroundColor: filled ? Colors.black : AppColors.text,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(999),
          side: BorderSide(color: filled ? AppColors.gold : AppColors.border),
        ),
      ),
      child: Text(text, style: const TextStyle(fontWeight: FontWeight.w900)),
    );
  }
}

void _emptyAction() {}




