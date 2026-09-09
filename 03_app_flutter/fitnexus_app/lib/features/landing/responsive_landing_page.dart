import 'dart:async';

import 'package:flutter/material.dart';

import '../growth/public_funnel_telemetry.dart';
import 'landing_page.dart';

/// Public top-of-funnel entry. The landing owns its responsive layout directly,
/// so mobile devices use their real viewport instead of a synthetic tall canvas.
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

  @override
  Widget build(BuildContext context) {
    return const LandingPage();
  }
}
