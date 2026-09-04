import 'package:flutter/material.dart';

import 'blackgold_contract_landing_page.dart' as premium;

/// Public landing entry with an explicit compact-tablet composition band.
///
/// The BlackGold contract uses the approved mobile composition below 900 px
/// and the desktop cockpit at 900 px and above. The 760-899 px band remains
/// constrained to a stable mobile/tablet rail so intermediate widths cannot
/// produce a half-desktop layout or RenderFlex drift.
class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  static const double _compactTabletWidth = 759;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (BuildContext context, BoxConstraints constraints) {
        final double width = constraints.maxWidth;
        final bool compactTablet = width >= 760 && width < 900;

        if (!compactTablet) {
          return const premium.LandingPage();
        }

        final MediaQueryData media = MediaQuery.of(context);
        return ColoredBox(
          color: premium.LandingPage.canvas,
          child: Center(
            child: SizedBox(
              width: _compactTabletWidth,
              child: MediaQuery(
                data: media.copyWith(
                  size: Size(_compactTabletWidth, media.size.height),
                ),
                child: const premium.LandingPage(),
              ),
            ),
          ),
        );
      },
    );
  }
}
