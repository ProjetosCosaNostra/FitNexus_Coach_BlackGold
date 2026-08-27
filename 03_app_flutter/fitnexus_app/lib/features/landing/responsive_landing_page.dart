import 'dart:async';
import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../growth/public_funnel_telemetry.dart';
import 'landing_page.dart';

/// Keeps the landing hero readable on short browser windows without clipping
/// content and owns the public top-of-funnel entry telemetry.
class ResponsiveLandingPage extends StatefulWidget {
  const ResponsiveLandingPage({super.key});

  @override
  State<ResponsiveLandingPage> createState() => _ResponsiveLandingPageState();
}

class _ResponsiveLandingPageState extends State<ResponsiveLandingPage> {
  @override
  void initState() {
    super.initState();
    unawaited(PublicFunnelTelemetry.instance.captureLandingView());
  }

  double _minimumLogicalHeight(double width) {
    if (width < 720) return 1180;
    if (width < 1100) return 1180;
    return 980;
  }

  @override
  Widget build(BuildContext context) {
    final MediaQueryData media = MediaQuery.of(context);
    final Size size = media.size;
    final bool mobile = size.width < 720;
    final double logicalHeight = math.max(
      size.height,
      _minimumLogicalHeight(size.width),
    );

    final Widget landing = logicalHeight == size.height
        ? const LandingPage()
        : MediaQuery(
            data: media.copyWith(size: Size(size.width, logicalHeight)),
            child: const LandingPage(),
          );

    return Stack(
      children: <Widget>[
        Positioned.fill(child: landing),
        Positioned(
          left: mobile ? 14 : 24,
          bottom: mobile ? 74 : 24,
          child: SafeArea(
            child: OutlinedButton.icon(
              key: const ValueKey<String>('public-contact-entry'),
              onPressed: () => Navigator.of(context).pushNamed('/support'),
              icon: const Icon(Icons.shield_outlined, size: 18),
              label: const Text('Atendimento'),
              style: OutlinedButton.styleFrom(
                foregroundColor: const Color(0xFFFFD45A),
                side: const BorderSide(color: Color(0xFF8A7130)),
                backgroundColor: const Color(0xE6111111),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
                textStyle: const TextStyle(fontWeight: FontWeight.w900),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
            ),
          ),
        ),
        Positioned(
          right: mobile ? 14 : 24,
          bottom: mobile ? 14 : 24,
          child: SafeArea(
            child: ElevatedButton.icon(
              key: const ValueKey<String>('public-signup-entry'),
              onPressed: () => Navigator.of(context).pushNamed('/start'),
              icon: const Icon(Icons.rocket_launch_rounded, size: 18),
              label: const Text('Começar grátis'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFFE1B92F),
                foregroundColor: Colors.black,
                elevation: 10,
                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 15),
                textStyle: const TextStyle(fontWeight: FontWeight.w900),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
