import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';

/// Product-wide floating call-to-action for compact/mobile BlackGold surfaces.
///
/// Keeps floating actions in the same gold, radius, glow and typography family
/// as the approved Home instead of allowing feature-local FAB styling.
class FitFloatingAction extends StatelessWidget {
  const FitFloatingAction({
    super.key,
    required this.label,
    required this.icon,
    required this.onTap,
    this.heroTag,
  });

  final String label;
  final IconData icon;
  final VoidCallback? onTap;
  final Object? heroTag;

  @override
  Widget build(BuildContext context) {
    final Widget button = DecoratedBox(
      decoration: BoxDecoration(
        gradient: onTap == null ? null : BlackGoldEffects.goldGradient,
        color: onTap == null ? AppColors.goldDeep : null,
        borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
        border: Border.all(
          color: BlackGoldPalette.goldBright.withValues(
            alpha: onTap == null ? 0.18 : 0.58,
          ),
          width: BlackGoldStroke.hairline,
        ),
        boxShadow: onTap == null ? const <BoxShadow>[] : BlackGoldEffects.goldGlow,
      ),
      child: Material(
        type: MaterialType.transparency,
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(BlackGoldRadius.pill),
          child: Padding(
            padding: const EdgeInsets.symmetric(
              horizontal: BlackGoldSpace.md,
              vertical: BlackGoldSpace.sm,
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: <Widget>[
                Icon(icon, color: AppColors.black, size: 19),
                const SizedBox(width: BlackGoldSpace.xs),
                Text(
                  label,
                  style: const TextStyle(
                    color: AppColors.black,
                    fontSize: 13,
                    height: 1.1,
                    fontWeight: FontWeight.w900,
                    letterSpacing: 0.05,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );

    if (heroTag == null) return button;
    return Hero(tag: heroTag!, child: button);
  }
}
