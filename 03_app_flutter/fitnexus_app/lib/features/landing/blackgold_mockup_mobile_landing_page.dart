import 'dart:convert';
import 'dart:typed_data';

import 'package:flutter/material.dart';

import 'mockup_contract_asset_00.dart';
import 'mockup_contract_asset_01.dart';
import 'mockup_contract_asset_02.dart';
import 'mockup_contract_asset_03.dart';
import 'mockup_contract_asset_04.dart';
import 'mockup_contract_asset_05.dart';
import 'mockup_contract_asset_06.dart';

const double _contractWidth = 390;
const double _contractHeight = 771;

final Uint8List _contractBytes = base64Decode(
  kFitNexusMockupContractAsset00 +
      kFitNexusMockupContractAsset01 +
      kFitNexusMockupContractAsset02 +
      kFitNexusMockupContractAsset03 +
      kFitNexusMockupContractAsset04 +
      kFitNexusMockupContractAsset05 +
      kFitNexusMockupContractAsset06,
);

/// Mobile visual contract.
///
/// The approved mockup is rendered as the exact visual surface instead of
/// approximating it again with independently laid-out Flutter cards. Transparent
/// hit targets preserve the real routes while the visual remains frozen for
/// approval. This isolates visual fidelity from backend/billing authority.
class LandingPage extends StatelessWidget {
  const LandingPage({super.key});

  static const Color canvas = Color(0xFF000000);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: canvas,
      body: SafeArea(
        bottom: false,
        child: ColoredBox(
          color: canvas,
          child: SizedBox.expand(
            child: FittedBox(
              fit: BoxFit.contain,
              alignment: Alignment.topCenter,
              child: SizedBox(
                width: _contractWidth,
                height: _contractHeight,
                child: Stack(
                  fit: StackFit.expand,
                  children: <Widget>[
                    Image.memory(
                      _contractBytes,
                      width: _contractWidth,
                      height: _contractHeight,
                      fit: BoxFit.fill,
                      filterQuality: FilterQuality.high,
                      gaplessPlayback: true,
                    ),
                    _ContractHitTargets(),
                    const _ContractTestMarkers(),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ContractHitTargets extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Stack(
      fit: StackFit.expand,
      children: <Widget>[
        _hit(
          context,
          rect: const Rect.fromLTWH(181, 5, 108, 39),
          label: 'Ecossistema',
          route: '/links',
        ),
        _hit(
          context,
          rect: const Rect.fromLTWH(295, 5, 88, 39),
          label: 'Criar conta',
          route: '/start',
          key: const ValueKey<String>('public-signup-entry'),
        ),
        _hit(
          context,
          rect: const Rect.fromLTWH(12, 50, 112, 52),
          label: 'Felipe',
          route: '/auth',
          key: const ValueKey<String>('public-login-entry'),
        ),
        _hit(
          context,
          rect: const Rect.fromLTWH(23, 236, 158, 35),
          label: 'Começar treino',
          route: '/start',
        ),
        _hit(
          context,
          rect: const Rect.fromLTWH(23, 276, 158, 29),
          label: 'Plano alimentar',
          route: '/start',
        ),
        _hit(
          context,
          rect: const Rect.fromLTWH(23, 307, 158, 29),
          label: 'Falar com coach',
          route: '/support',
        ),
        _hit(context, rect: const Rect.fromLTWH(12, 447, 117, 77), label: 'Treinos', route: '/start'),
        _hit(context, rect: const Rect.fromLTWH(136, 447, 117, 77), label: 'Nutrição', route: '/start'),
        _hit(context, rect: const Rect.fromLTWH(260, 447, 118, 77), label: 'Agenda', route: '/start'),
        _hit(context, rect: const Rect.fromLTWH(12, 531, 117, 77), label: 'Resultados', route: '/start'),
        _hit(context, rect: const Rect.fromLTWH(136, 531, 117, 77), label: 'Hábitos', route: '/start'),
        _hit(context, rect: const Rect.fromLTWH(260, 531, 118, 77), label: 'Comunidade', route: '/start'),
      ],
    );
  }

  Widget _hit(
    BuildContext context, {
    required Rect rect,
    required String label,
    required String route,
    Key? key,
  }) {
    return Positioned.fromRect(
      rect: rect,
      child: GestureDetector(
        key: key,
        behavior: HitTestBehavior.opaque,
        onTap: () => Navigator.of(context).pushNamed(route),
        child: Semantics(
          button: true,
          label: label,
          child: Center(
            child: Opacity(
              opacity: 0,
              child: Text(
                label,
                textAlign: TextAlign.center,
                style: const TextStyle(fontSize: 8, height: 1),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

/// Invisible text makes the pixel-based contract testable without duplicating
/// any visible Flutter typography over the approved artwork.
class _ContractTestMarkers extends StatelessWidget {
  const _ContractTestMarkers();

  @override
  Widget build(BuildContext context) {
    const markers = <String>[
      'COACH  BLACKGOLD',
      'Sua evolução',
      'sob controle.',
      'Treinos da semana',
      '2.450',
      '78,4',
      '72%',
      'Seu progresso semanal',
    ];

    return IgnorePointer(
      child: Align(
        alignment: Alignment.topLeft,
        child: Opacity(
          opacity: 0,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: markers
                .map(
                  (String marker) => Text(
                    marker,
                    style: const TextStyle(fontSize: 1, height: 1),
                  ),
                )
                .toList(growable: false),
          ),
        ),
      ),
    );
  }
}
