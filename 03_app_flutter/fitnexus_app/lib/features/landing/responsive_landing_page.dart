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
          right: size.width < 720 ? 14 : 24,
          bottom: size.width < 720 ? 14 : 24,
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
