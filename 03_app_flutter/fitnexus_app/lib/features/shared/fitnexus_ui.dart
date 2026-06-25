import 'package:flutter/material.dart';

class FitColors {
  static const Color bg = Color(0xFF050505);
  static const Color card = Color(0xFF121212);
  static const Color cardSoft = Color(0xFF181818);
  static const Color gold = Color(0xFFE1B92F);
  static const Color goldSoft = Color(0xFFFFD45A);
  static const Color text = Color(0xFFF5F5F5);
  static const Color muted = Color(0xFFB8B8B8);
  static const Color border = Color(0xFF2A2A2A);
}

class FitShell extends StatelessWidget {
  const FitShell({
    super.key,
    required this.child,
    this.maxWidth = 1160,
  });

  final Widget child;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: FitColors.bg,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(22, 22, 22, 36),
          child: Center(
            child: ConstrainedBox(
              constraints: BoxConstraints(maxWidth: maxWidth),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const FitHeader(),
                  const SizedBox(height: 38),
                  child,
                ],
              ),
            ),
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
    return Wrap(
      spacing: 16,
      runSpacing: 16,
      alignment: WrapAlignment.spaceBetween,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: <Widget>[
        Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Container(
              width: 48,
              height: 48,
              decoration: BoxDecoration(
                color: FitColors.gold,
                borderRadius: BorderRadius.circular(14),
                boxShadow: <BoxShadow>[
                  BoxShadow(
                    color: FitColors.gold.withValues(alpha: 0.22),
                    blurRadius: 22,
                  ),
                ],
              ),
              child: const Icon(
                Icons.fitness_center,
                color: Colors.black,
                size: 24,
              ),
            ),
            const SizedBox(width: 14),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  'FitNexus Coach',
                  style: TextStyle(
                    color: FitColors.text,
                    fontWeight: FontWeight.w900,
                    fontSize: 20,
                  ),
                ),
                SizedBox(height: 2),
                Text(
                  'BlackGold SaaS Fitness',
                  style: TextStyle(
                    color: FitColors.muted,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ],
        ),
        Wrap(
          spacing: 10,
          runSpacing: 10,
          children: <Widget>[
            GhostButton(
              label: 'Landing',
              onTap: () => Navigator.pushNamedAndRemoveUntil(
                context,
                '/',
                (_) => false,
              ),
            ),
            GoldButton(
              label: 'Demonstração',
              icon: Icons.play_circle_outline,
              onTap: () => Navigator.pushNamedAndRemoveUntil(
                context,
                '/demo',
                (_) => false,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class SectionLabel extends StatelessWidget {
  const SectionLabel(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text.toUpperCase(),
      style: const TextStyle(
        color: FitColors.goldSoft,
        fontSize: 12,
        fontWeight: FontWeight.w900,
        letterSpacing: 0.8,
      ),
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
  final VoidCallback onTap;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return FilledButton.icon(
      onPressed: onTap,
      icon: Icon(icon ?? Icons.arrow_forward, size: 18),
      label: Text(label),
      style: FilledButton.styleFrom(
        backgroundColor: FitColors.gold,
        foregroundColor: Colors.black,
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        textStyle: const TextStyle(fontWeight: FontWeight.w900),
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
      icon: Icon(icon ?? Icons.arrow_outward, size: 18),
      label: Text(label),
      style: OutlinedButton.styleFrom(
        foregroundColor: FitColors.text,
        side: BorderSide(color: FitColors.gold.withValues(alpha: 0.45)),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        textStyle: const TextStyle(fontWeight: FontWeight.w800),
      ),
    );
  }
}

class FitCard extends StatelessWidget {
  const FitCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(24),
  });

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: padding,
      decoration: BoxDecoration(
        color: FitColors.card,
        borderRadius: BorderRadius.circular(26),
        border: Border.all(color: FitColors.border),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.28),
            blurRadius: 28,
            offset: const Offset(0, 18),
          ),
        ],
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
  });

  final IconData icon;
  final String title;
  final String text;

  @override
  Widget build(BuildContext context) {
    return FitCard(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Icon(icon, color: FitColors.goldSoft, size: 28),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Text(
                  title,
                  style: const TextStyle(
                    color: FitColors.text,
                    fontSize: 18,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  text,
                  style: const TextStyle(
                    color: FitColors.muted,
                    height: 1.45,
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
