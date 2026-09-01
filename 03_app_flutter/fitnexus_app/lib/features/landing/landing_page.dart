import 'package:flutter/material.dart';

import 'premium_landing_page.dart' as premium;

/// Public landing entry with an explicit compact-tablet composition band.
///
/// The premium surface switches its primary hero at 760 px, while several
/// internal grids stack below roughly 700 px after page padding. A viewport in
/// the 760-899 px range can therefore be wide enough to request the desktop
/// hero but too narrow for every desktop row. Keep that intermediate band on a
/// single compact content rail so the whole page uses one coherent layout
/// class instead of allowing isolated RenderFlex overflows.
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
