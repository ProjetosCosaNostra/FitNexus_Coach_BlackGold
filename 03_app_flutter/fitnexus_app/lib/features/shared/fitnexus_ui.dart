import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';

/// Compatibility facade used by the existing feature surfaces.
/// All values are now sourced from the frozen BlackGold design system.
class FitColors {
  const FitColors._();

  static const Color bg = AppColors.black;
  static const Color card = AppColors.card;
  static const Color cardSoft = AppColors.cardRaised;
  static const Color gold = AppColors.gold;
  static const Color goldSoft = AppColors.goldSoft;
  static const Color text = AppColors.text;
  static const Color muted = AppColors.muted;
  static const Color border = AppColors.borderGold;
}

class FitShell extends StatelessWidget {
  const FitShell({
    super.key,
    required this.child,
    this.maxWidth = 1160,
    this.showHeader = true,
  });

  final Widget child;
  final double maxWidth;
  final bool showHeader;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FitColors.bg,
      body: Stack(
        fit: StackFit.expand,
        children: <Widget>[
          const _BlackGoldBackdrop(),
          SafeArea(
            child: LayoutBuilder(
              builder: (BuildContext context, BoxConstraints constraints) {
                final double horizontalPadding = constraints.maxWidth < 600
                    ? BlackGoldSpace.md
                    : constraints.maxWidth < 1000
                        ? BlackGoldSpace.xl
                        : BlackGoldSpace.xxl;

                return SingleChildScrollView(
                  padding: EdgeInsets.fromLTRB(
                    horizontalPadding,
                    BlackGoldSpace.lg,
                    horizontalPadding,
                    BlackGoldSpace.section,
                  ),
                  child: Center(
                    child: ConstrainedBox(
                      constraints: BoxConstraints(maxWidth: maxWidth),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: <Widget>[
                          if (showHeader) ...<Widget>[
                            const FitHeader(),
                            const SizedBox(height: BlackGoldSpace.xxl),
                          ],
                          child,
                        ],
                      ),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class _BlackGoldBackdrop extends StatelessWidget {
  const _BlackGoldBackdrop();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: DecoratedBox(
        decoration: const BoxDecoration(
          color: AppColors.black,
          gradient: RadialGradient(
            center: Alignment(0.72, -0.86),
            radius: 1.28,
            colors: <Color>[
              Color(0x222C2109),
              Color(0x120F0C05),
              Color(0xFF000000),
            ],
            stops: <double>[0, 0.43, 1],
          ),
        ),
      ),
    );
  }
}

class FitHeader extends StatelessWidget {
  const FitHeader({super.key});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final bool compact = constraints.maxWidth < 720;
        final Widget brand = const _FitNexusBrand();
        final Widget actions = Wrap(
          spacing: BlackGoldSpace.xs,
          runSpacing: BlackGoldSpace.xs,
          alignment: WrapAlignment.end,
          children: <Widget>[
            GhostButton(
              label: 'Ecossistema',
              icon: Icons.hub_outlined,
              onTap: () => Navigator.pushNamed(context, '/links'),
            ),
            GoldButton(
              label: 'Início',
              icon: Icons.home_rounded,
              onTap: () => Navigator.pushNamedAndRemoveUntil(
                context,
                '/',
                (_) => false,
              ),
            ),
          ],
        );

        if (compact) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              brand,
              const SizedBox(height: BlackGoldSpace.md),
              actions,
            ],
          );
        }

        return Row(
          children: <Widget>[
            brand,
            const Spacer(),
            actions,
          ],
        );
      },
    );
  }
}

class _FitNexusBrand extends StatelessWidget {
  const _FitNexusBrand();

  @override
  Widget build(BuildContext context) {
    return Semantics(
      header: true,
      label: 'FitNexus Coach BlackGold',
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text.rich(
            const TextSpan(
              children: <InlineSpan>[
                TextSpan(
                  text: 'FIT',
                  style: TextStyle(color: AppColors.text),
                ),
                TextSpan(
                  text: 'NEXUS',
                  style: TextStyle(color: AppColors.goldSoft),
                ),
              ],
            ),
            style: const TextStyle(
              fontSize: 25,
              height: 1,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.4,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'C O A C H   B L A C K G O L D',
            style: TextStyle(
              color: AppColors.muted,
              fontSize: 8.5,
              height: 1,
              fontWeight: FontWeight.w700,
              letterSpacing: 1.55,
            ),
          ),
        ],
      ),
    );
  }
}

class SectionLabel extends StatelessWidget {
  const SectionLabel(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: 18,
          height: 1,
          color: AppColors.gold,
        ),
        const SizedBox(width: BlackGoldSpace.xs),
        Text(
          text.toUpperCase(),
          style: const TextStyle(
            color: AppColors.goldSoft,
            fontSize: 11,
            fontWeight: FontWeight.w900,
            letterSpacing: 1.35,
          ),
        ),
      ],
    );
  }
}

class GoldButton extends StatelessWidget {
  const GoldButton({
    super.key,
    required this.label,
    required this.onTap,
    this.icon,
  });

  final String label;
  final VoidCallback? onTap;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        boxShadow: onTap == null ? const <BoxShadow>[] : BlackGoldEffects.goldGlow,
      ),
      child: FilledButton.icon(
        onPressed: onTap,
        icon: Icon(icon ?? Icons.arrow_forward_rounded, size: 17),
        label: Text(label),
      ),
    );
  }
}

class GhostButton extends StatelessWidget {
  const GhostButton({
    super.key,
    required this.label,
    required this.onTap,
    this.icon,
  });

  final String label;
  final VoidCallback onTap;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return OutlinedButton.icon(
      onPressed: onTap,
      icon: Icon(icon ?? Icons.arrow_outward_rounded, size: 17),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        backgroundColor: AppColors.card.withValues(alpha: 0.66),
        foregroundColor: AppColors.text,
        side: const BorderSide(
          color: AppColors.borderGold,
          width: BlackGoldStroke.regular,
        ),
      ),
    );
  }
}

class FitCard extends StatelessWidget {
  const FitCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(BlackGoldSpace.xl),
    this.highlight = false,
  });

  final Widget child;
  final EdgeInsets padding;
  final bool highlight;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        gradient: BlackGoldEffects.panelGradient,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        border: Border.all(
          color: highlight
              ? AppColors.gold.withValues(alpha: 0.74)
              : AppColors.borderGold.withValues(alpha: 0.78),
          width: highlight
              ? BlackGoldStroke.emphasis
              : BlackGoldStroke.hairline,
        ),
        boxShadow: BlackGoldEffects.cardShadow,
      ),
      child: child,
    );
  }
}

class FeatureTile extends StatelessWidget {
  const FeatureTile({
    super.key,
    required this.icon,
    required this.title,
    required this.text,
    this.onTap,
  });

  final IconData icon;
  final String title;
  final String text;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final Widget content = FitCard(
      padding: const EdgeInsets.all(BlackGoldSpace.lg),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Container(
            width: 38,
            height: 38,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AppColors.gold.withValues(alpha: 0.08),
              borderRadius: BorderRadius.circular(BlackGoldRadius.control),
              border: Border.all(
                color: AppColors.gold.withValues(alpha: 0.38),
                width: BlackGoldStroke.hairline,
              ),
            ),
            child: Icon(icon, color: AppColors.goldSoft, size: 21),
          ),
          const SizedBox(width: BlackGoldSpace.md),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontSize: 16,
                    height: 1.15,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: BlackGoldSpace.xs),
                Text(
                  text,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 13,
                    height: 1.42,
                  ),
                ),
              ],
            ),
          ),
          if (onTap != null) ...<Widget>[
            const SizedBox(width: BlackGoldSpace.xs),
            const Icon(
              Icons.arrow_forward_rounded,
              color: AppColors.gold,
              size: 17,
            ),
          ],
        ],
      ),
    );

    if (onTap == null) return content;

    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(BlackGoldRadius.panel),
        child: content,
      ),
    );
  }
}

class FitPageTitle extends StatelessWidget {
  const FitPageTitle({
    super.key,
    required this.eyebrow,
    required this.title,
    this.description,
    this.trailing,
  });

  final String eyebrow;
  final String title;
  final String? description;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final Widget copy = Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            SectionLabel(eyebrow),
            const SizedBox(height: BlackGoldSpace.sm),
            Text(
              title,
              style: Theme.of(context).textTheme.headlineLarge,
            ),
            if (description != null) ...<Widget>[
              const SizedBox(height: BlackGoldSpace.xs),
              Text(
                description!,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            ],
          ],
        );

        if (trailing == null || constraints.maxWidth < 700) {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              copy,
              if (trailing != null) ...<Widget>[
                const SizedBox(height: BlackGoldSpace.md),
                trailing!,
              ],
            ],
          );
        }

        return Row(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: <Widget>[
            Expanded(child: copy),
            const SizedBox(width: BlackGoldSpace.xl),
            trailing!,
          ],
        );
      },
    );
  }
}

class FitMetricCard extends StatelessWidget {
  const FitMetricCard({
    super.key,
    required this.icon,
    required this.label,
    required this.value,
    this.detail,
    this.positive,
  });

  final IconData icon;
  final String label;
  final String value;
  final String? detail;
  final bool? positive;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      padding: const EdgeInsets.all(BlackGoldSpace.md),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(icon, color: AppColors.goldSoft, size: 19),
              const SizedBox(width: BlackGoldSpace.xs),
              Expanded(
                child: Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(
            value,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 24,
              height: 1,
              fontWeight: FontWeight.w900,
            ),
          ),
          if (detail != null) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.xs),
            Text(
              detail!,
              style: TextStyle(
                color: positive == null
                    ? AppColors.muted
                    : positive!
                        ? AppColors.success
                        : AppColors.danger,
                fontSize: 11,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ],
      ),
    );
  }
}
