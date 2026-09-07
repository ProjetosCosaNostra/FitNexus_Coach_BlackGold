import 'package:flutter/material.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../auth/auth_gate.dart';
import '../auth/auth_service.dart';
import 'professor_checkout_page.dart';
import 'professor_coach_action_center_page.dart';
import 'professor_decision_intelligence_page.dart';
import 'professor_feedback_page.dart';
import 'professor_lineage_page.dart';
import 'professor_progress_page.dart';
import 'professor_subscription_page.dart';
import 'professor_templates_page.dart';
import 'student_access_management_page.dart';

class AuthenticatedProfessorPage extends StatefulWidget {
  const AuthenticatedProfessorPage({super.key});

  @override
  State<AuthenticatedProfessorPage> createState() =>
      _AuthenticatedProfessorPageState();
}

enum _ProfessorQuickAction {
  checkout,
  subscription,
  intelligence,
  lineage,
  logout,
}

class _AuthenticatedProfessorPageState
    extends State<AuthenticatedProfessorPage> {
  int _index = 0;

  static const List<Widget> _pages = <Widget>[
    ProfessorCoachActionCenterPage(),
    ProfessorProgressPage(),
    ProfessorFeedbackPage(),
    ProfessorTemplatesPage(),
    StudentAccessManagementPage(),
  ];

  Future<void> _signOut(BuildContext context) async {
    final NavigatorState navigator = Navigator.of(context);
    await AuthService.instance.signOut();
    navigator.pushNamedAndRemoveUntil('/auth', (Route<dynamic> route) => false);
  }

  void _openLineage(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(builder: (_) => const ProfessorLineagePage()),
    );
  }

  void _openDecisionIntelligence(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const ProfessorDecisionIntelligencePage(),
      ),
    );
  }

  void _openSubscription(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const ProfessorSubscriptionPage(),
      ),
    );
  }

  void _openCheckout(BuildContext context) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => const ProfessorCheckoutPage(),
      ),
    );
  }

  Future<void> _handleQuickAction(
    BuildContext context,
    _ProfessorQuickAction action,
  ) async {
    switch (action) {
      case _ProfessorQuickAction.checkout:
        _openCheckout(context);
        return;
      case _ProfessorQuickAction.subscription:
        _openSubscription(context);
        return;
      case _ProfessorQuickAction.intelligence:
        _openDecisionIntelligence(context);
        return;
      case _ProfessorQuickAction.lineage:
        _openLineage(context);
        return;
      case _ProfessorQuickAction.logout:
        await _signOut(context);
        return;
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthGate(
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool wide = constraints.maxWidth >= 980;
          final Widget body = IndexedStack(index: _index, children: _pages);

          final Widget workspace = wide
              ? Row(
                  children: <Widget>[
                    _ProfessorRail(
                      selectedIndex: _index,
                      onSelected: (int value) {
                        setState(() => _index = value);
                      },
                    ),
                    Container(
                      width: 1,
                      color: AppColors.borderGold.withValues(alpha: 0.48),
                    ),
                    Expanded(child: body),
                  ],
                )
              : Column(
                  children: <Widget>[
                    Expanded(child: body),
                    _ProfessorBottomNav(
                      selectedIndex: _index,
                      onSelected: (int value) {
                        setState(() => _index = value);
                      },
                    ),
                  ],
                );

          return ColoredBox(
            color: AppColors.black,
            child: Stack(
              children: <Widget>[
                Positioned.fill(child: workspace),
                Positioned(
                  right: wide ? BlackGoldSpace.xl : BlackGoldSpace.md,
                  bottom: wide ? BlackGoldSpace.xl : 88,
                  child: SafeArea(
                    child: _ProfessorQuickMenu(
                      onSelected: (_ProfessorQuickAction action) =>
                          _handleQuickAction(context, action),
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class _ProfessorRail extends StatelessWidget {
  const _ProfessorRail({
    required this.selectedIndex,
    required this.onSelected,
  });

  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 146,
      decoration: const BoxDecoration(
        color: Color(0xFF060606),
        gradient: LinearGradient(
          begin: Alignment.topCenter,
          end: Alignment.bottomCenter,
          colors: <Color>[
            Color(0xFF0B0A07),
            Color(0xFF050505),
          ],
        ),
      ),
      child: SafeArea(
        child: NavigationRail(
          backgroundColor: Colors.transparent,
          selectedIndex: selectedIndex,
          onDestinationSelected: onSelected,
          labelType: NavigationRailLabelType.all,
          minWidth: 92,
          minExtendedWidth: 146,
          groupAlignment: -0.72,
          indicatorColor: AppColors.gold.withValues(alpha: 0.13),
          indicatorShape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(BlackGoldRadius.control),
            side: BorderSide(
              color: AppColors.gold.withValues(alpha: 0.28),
              width: BlackGoldStroke.hairline,
            ),
          ),
          selectedIconTheme: const IconThemeData(
            color: AppColors.goldSoft,
            size: 21,
          ),
          selectedLabelTextStyle: const TextStyle(
            color: AppColors.goldSoft,
            fontSize: 11,
            fontWeight: FontWeight.w900,
          ),
          unselectedIconTheme: const IconThemeData(
            color: AppColors.muted,
            size: 20,
          ),
          unselectedLabelTextStyle: const TextStyle(
            color: AppColors.muted,
            fontSize: 11,
            fontWeight: FontWeight.w600,
          ),
          leading: const Padding(
            padding: EdgeInsets.only(bottom: BlackGoldSpace.xxl),
            child: _RailBrand(),
          ),
          destinations: const <NavigationRailDestination>[
            NavigationRailDestination(
              icon: Icon(Icons.home_rounded),
              label: Text('Hoje'),
            ),
            NavigationRailDestination(
              icon: Icon(Icons.monitor_heart_rounded),
              label: Text('Progresso'),
            ),
            NavigationRailDestination(
              icon: Icon(Icons.forum_rounded),
              label: Text('Feedbacks'),
            ),
            NavigationRailDestination(
              icon: Icon(Icons.auto_awesome_rounded),
              label: Text('Templates'),
            ),
            NavigationRailDestination(
              icon: Icon(Icons.qr_code_2_rounded),
              label: Text('Acessos'),
            ),
          ],
        ),
      ),
    );
  }
}

class _RailBrand extends StatelessWidget {
  const _RailBrand();

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      children: <Widget>[
        Container(
          width: 44,
          height: 44,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(BlackGoldRadius.card),
            border: Border.all(
              color: AppColors.gold.withValues(alpha: 0.62),
              width: BlackGoldStroke.regular,
            ),
            color: AppColors.card,
            boxShadow: BlackGoldEffects.goldGlow,
          ),
          child: const Text(
            'FN',
            style: TextStyle(
              color: AppColors.goldSoft,
              fontSize: 15,
              fontWeight: FontWeight.w900,
              letterSpacing: 0.5,
            ),
          ),
        ),
        const SizedBox(height: BlackGoldSpace.xs),
        const Text(
          'BLACKGOLD',
          style: TextStyle(
            color: AppColors.muted,
            fontSize: 7,
            fontWeight: FontWeight.w800,
            letterSpacing: 1.2,
          ),
        ),
      ],
    );
  }
}

class _ProfessorBottomNav extends StatelessWidget {
  const _ProfessorBottomNav({
    required this.selectedIndex,
    required this.onSelected,
  });

  final int selectedIndex;
  final ValueChanged<int> onSelected;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        color: const Color(0xFF070707),
        border: Border(
          top: BorderSide(
            color: AppColors.borderGold.withValues(alpha: 0.54),
            width: BlackGoldStroke.hairline,
          ),
        ),
        boxShadow: <BoxShadow>[
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.72),
            blurRadius: 24,
            offset: const Offset(0, -8),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: NavigationBar(
          height: 68,
          selectedIndex: selectedIndex,
          onDestinationSelected: onSelected,
          destinations: const <NavigationDestination>[
            NavigationDestination(
              icon: Icon(Icons.home_rounded),
              label: 'Hoje',
            ),
            NavigationDestination(
              icon: Icon(Icons.monitor_heart_rounded),
              label: 'Progresso',
            ),
            NavigationDestination(
              icon: Icon(Icons.forum_rounded),
              label: 'Feedbacks',
            ),
            NavigationDestination(
              icon: Icon(Icons.auto_awesome_rounded),
              label: 'Templates',
            ),
            NavigationDestination(
              icon: Icon(Icons.qr_code_2_rounded),
              label: 'Acessos',
            ),
          ],
        ),
      ),
    );
  }
}

class _ProfessorQuickMenu extends StatelessWidget {
  const _ProfessorQuickMenu({required this.onSelected});

  final ValueChanged<_ProfessorQuickAction> onSelected;

  @override
  Widget build(BuildContext context) {
    return PopupMenuButton<_ProfessorQuickAction>(
      tooltip: 'Ações do professor',
      onSelected: onSelected,
      color: AppColors.cardRaised,
      surfaceTintColor: Colors.transparent,
      elevation: 12,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(BlackGoldRadius.card),
        side: const BorderSide(
          color: AppColors.borderGold,
          width: BlackGoldStroke.hairline,
        ),
      ),
      itemBuilder: (BuildContext context) =>
          const <PopupMenuEntry<_ProfessorQuickAction>>[
        PopupMenuItem<_ProfessorQuickAction>(
          value: _ProfessorQuickAction.checkout,
          child: _QuickMenuRow(
            icon: Icons.payments_rounded,
            label: 'Assinar FitNexus',
          ),
        ),
        PopupMenuItem<_ProfessorQuickAction>(
          value: _ProfessorQuickAction.subscription,
          child: _QuickMenuRow(
            icon: Icons.workspace_premium_rounded,
            label: 'Meu plano',
          ),
        ),
        PopupMenuItem<_ProfessorQuickAction>(
          value: _ProfessorQuickAction.intelligence,
          child: _QuickMenuRow(
            icon: Icons.psychology_alt_rounded,
            label: 'IA Coach',
          ),
        ),
        PopupMenuItem<_ProfessorQuickAction>(
          value: _ProfessorQuickAction.lineage,
          child: _QuickMenuRow(
            icon: Icons.account_tree_rounded,
            label: 'Decisões',
          ),
        ),
        PopupMenuDivider(),
        PopupMenuItem<_ProfessorQuickAction>(
          value: _ProfessorQuickAction.logout,
          child: _QuickMenuRow(
            icon: Icons.logout_rounded,
            label: 'Sair',
            danger: true,
          ),
        ),
      ],
      child: Container(
        height: 48,
        padding: const EdgeInsets.symmetric(horizontal: BlackGoldSpace.md),
        decoration: BoxDecoration(
          gradient: BlackGoldEffects.goldGradient,
          borderRadius: BorderRadius.circular(BlackGoldRadius.control),
          boxShadow: BlackGoldEffects.goldGlow,
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            Icon(Icons.grid_view_rounded, color: Colors.black, size: 19),
            SizedBox(width: BlackGoldSpace.xs),
            Text(
              'Mais',
              style: TextStyle(
                color: Colors.black,
                fontSize: 13,
                fontWeight: FontWeight.w900,
              ),
            ),
            SizedBox(width: 3),
            Icon(Icons.keyboard_arrow_up_rounded, color: Colors.black, size: 18),
          ],
        ),
      ),
    );
  }
}

class _QuickMenuRow extends StatelessWidget {
  const _QuickMenuRow({
    required this.icon,
    required this.label,
    this.danger = false,
  });

  final IconData icon;
  final String label;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final Color color = danger ? AppColors.danger : AppColors.text;
    return Row(
      children: <Widget>[
        Icon(
          icon,
          color: danger ? AppColors.danger : AppColors.goldSoft,
          size: 19,
        ),
        const SizedBox(width: BlackGoldSpace.sm),
        Text(
          label,
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.w700,
          ),
        ),
      ],
    );
  }
}
