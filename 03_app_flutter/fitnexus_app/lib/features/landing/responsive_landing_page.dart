import 'dart:math' as math;

import 'package:flutter/material.dart';

import 'landing_page.dart';

/// Keeps the landing hero readable on short browser windows without clipping
/// content. The landing is scrollable; this only establishes a minimum logical
/// viewport height used by its hero sizing calculation.
class ResponsiveLandingPage extends StatelessWidget {
  const ResponsiveLandingPage({super.key});

  double _minimumLogicalHeight(double width) {
    if (width < 720) return 900;
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

    if (logicalHeight == size.height) {
      return const LandingPage();
    }

    return MediaQuery(
      data: media.copyWith(size: Size(size.width, logicalHeight)),
      child: const LandingPage(),
    );
  }
}
