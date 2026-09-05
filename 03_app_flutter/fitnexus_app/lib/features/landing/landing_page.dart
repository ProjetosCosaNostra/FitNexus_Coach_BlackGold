import 'package:flutter/material.dart';

import 'blackgold_contract_landing_page.dart' as premium;
import 'blackgold_desktop_home.dart';

/// Public entry that preserves the frozen BlackGold mobile contract and uses
/// a purpose-built desktop cockpit at 900 px and above.
class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  static const double _compactTabletWidth = 759;
  static const double _desktopBreakpoint = 900;
  static const double _visualTextScale = .95;
  static const double _compactTabletTextScale = .90;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final double width = constraints.maxWidth;

        if (width >= _desktopBreakpoint) {
          return const BlackGoldDesktopHome();
        }

        final MediaQueryData media = MediaQuery.of(context);
        final bool compactTablet = width >= 760;
        final MediaQueryData stableMedia = media.copyWith(
          size: Size(
            compactTablet ? _compactTabletWidth : media.size.width,
            media.size.height,
          ),
          textScaler: TextScaler.linear(
            compactTablet ? _compactTabletTextScale : _visualTextScale,
          ),
        );

        if (!compactTablet) {
          return MediaQuery(
            data: stableMedia,
            child: const premium.LandingPage(),
          );
        }

        return ColoredBox(
          color: premium.LandingPage.canvas,
          child: Center(
            child: SizedBox(
              width: _compactTabletWidth,
              child: MediaQuery(
                data: stableMedia,
                child: const premium.LandingPage(),
              ),
            ),
          ),
        );
      },
    );
  }
}