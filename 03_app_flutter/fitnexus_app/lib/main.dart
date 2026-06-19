import 'package:flutter/material.dart';

void main() {
  runApp(const FitNexusApp());
}

class FitNexusApp extends StatelessWidget {
  const FitNexusApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'FitNexus Coach BlackGold',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        fontFamily: 'Arial',
        scaffoldBackgroundColor: const Color(0xFF070707),
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFFD4AF37),
          brightness: Brightness.dark,
        ),
      ),
      home: const HomePage(),
    );
  }
}

class AppColors {
  static const black = Color(0xFF070707);
  static const blackSoft = Color(0xFF111111);
  static const card = Color(0xFF171717);
  static const gold = Color(0xFFD4AF37);
  static const goldSoft = Color(0xFFFFD76A);
  static const text = Color(0xFFF5F5F5);
  static const muted = Color(0xFFB8B8B8);
  static const border = Color(0xFF3A2F13);
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final isMobile = width < 800;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: RadialGradient(
            center: Alignment.topRight,
            radius: 1.2,
            colors: [
              Color(0xFF3A2F13),
              AppColors.black,
              AppColors.black,
            ],
          ),
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: EdgeInsets.symmetric(
              horizontal: isMobile ? 20 : 64,
              vertical: 24,
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const _TopBar(),
                const SizedBox(height: 70),
                isMobile
                    ? const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          _HeroText(),
                          SizedBox(height: 32),
                          _PreviewPanel(),
                        ],
                      )
                    : const Row(
                        crossAxisAlignment: CrossAxisAlignment.center,
                        children: [
                          Expanded(child: _HeroText()),
                          SizedBox(width: 48),
                          Expanded(child: _PreviewPanel()),
                        ],
                      ),
                const SizedBox(height: 70),
                const _SectionTitle(
                  title: 'O que o FitNexus entrega',
                  subtitle:
                      'Um sistema SaaS para transformar treinos em uma experiência digital profissional.',
                ),
                const SizedBox(height: 24),
                const _FeatureGrid(),
                const SizedBox(height: 70),
                const _FounderOffer(),
                const SizedBox(height: 40),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _TopBar extends StatelessWidget {
  const _TopBar();

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 44,
          height: 44,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(14),
            gradient: const LinearGradient(
              colors: [AppColors.goldSoft, AppColors.gold],
            ),
            boxShadow: [
              BoxShadow(
                color: AppColors.gold.withOpacity(0.25),
                blurRadius: 24,
                offset: const Offset(0, 8),
              ),
            ],
          ),
          child: const Icon(
            Icons.fitness_center,
            color: Colors.black,
          ),
        ),
        const SizedBox(width: 14),
        const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'FitNexus Coach',
              style: TextStyle(
                color: AppColors.text,
                fontSize: 20,
                fontWeight: FontWeight.w800,
              ),
            ),
            Text(
              'BlackGold SaaS Fitness',
              style: TextStyle(
                color: AppColors.muted,
                fontSize: 12,
              ),
            ),
          ],
        ),
        const Spacer(),
        _SmallButton(
          text: 'Entrar',
          filled: false,
          onTap: () {},
        ),
        const SizedBox(width: 10),
        _SmallButton(
          text: 'Criar conta',
          filled: true,
          onTap: () {},
        ),
      ],
    );
  }
}

class _HeroText extends StatelessWidget {
  const _HeroText();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
          decoration: BoxDecoration(
            color: AppColors.gold.withOpacity(0.12),
            borderRadius: BorderRadius.circular(999),
            border: Border.all(color: AppColors.border),
          ),
          child: const Text(
            'Web/PWA agora • Android depois • SaaS escalável',
            style: TextStyle(
              color: AppColors.goldSoft,
              fontSize: 13,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
        const SizedBox(height: 28),
        const Text(
          'Treinos digitais profissionais para personal, professor e academia.',
          style: TextStyle(
            color: AppColors.text,
            fontSize: 52,
            height: 1.05,
            fontWeight: FontWeight.w900,
            letterSpacing: -1.4,
          ),
        ),
        const SizedBox(height: 22),
        const Text(
          'Pare de entregar treino por papel, PDF ou WhatsApp bagunçado. '
          'Com o FitNexus, o aluno recebe o treino no celular, marca exercícios concluídos, '
          'registra carga e acompanha sua evolução.',
          style: TextStyle(
            color: AppColors.muted,
            fontSize: 18,
            height: 1.55,
          ),
        ),
        const SizedBox(height: 32),
        Wrap(
          spacing: 14,
          runSpacing: 14,
          children: [
            _HeroButton(
              text: 'Começar teste grátis',
              icon: Icons.rocket_launch,
              filled: true,
              onTap: () {},
            ),
            _HeroButton(
              text: 'Ver demonstração',
              icon: Icons.play_circle_outline,
              filled: false,
              onTap: () {},
            ),
          ],
        ),
      ],
    );
  }
}

class _PreviewPanel extends StatelessWidget {
  const _PreviewPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 520),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.blackSoft.withOpacity(0.92),
        borderRadius: BorderRadius.circular(28),
        border: Border.all(color: AppColors.border),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.55),
            blurRadius: 40,
            offset: const Offset(0, 24),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              CircleAvatar(
                radius: 22,
                backgroundColor: AppColors.gold,
                child: Icon(Icons.person, color: Colors.black),
              ),
              SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Aluno: Mariana Alves',
                      style: TextStyle(
                        color: AppColors.text,
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                      ),
                    ),
                    Text(
                      'Treino A — Inferiores',
                      style: TextStyle(
                        color: AppColors.muted,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(Icons.qr_code_2, color: AppColors.goldSoft),
            ],
          ),
          const SizedBox(height: 22),
          const _MetricRow(),
          const SizedBox(height: 20),
          const _ExerciseItem(
            name: 'Agachamento livre',
            detail: '4 séries • 10 a 12 repetições • descanso 60s',
            done: true,
          ),
          const _ExerciseItem(
            name: 'Leg press',
            detail: '4 séries • 12 repetições • carga moderada',
            done: false,
          ),
          const _ExerciseItem(
            name: 'Cadeira extensora',
            detail: '3 séries • 12 a 15 repetições • controle total',
            done: false,
          ),
          const SizedBox(height: 20),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.gold.withOpacity(0.1),
              borderRadius: BorderRadius.circular(18),
              border: Border.all(color: AppColors.border),
            ),
            child: const Row(
              children: [
                Icon(Icons.timer, color: AppColors.goldSoft),
                SizedBox(width: 10),
                Expanded(
                  child: Text(
                    'Cronômetro de descanso pronto para o próximo exercício.',
                    style: TextStyle(color: AppColors.text),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _MetricRow extends StatelessWidget {
  const _MetricRow();

  @override
  Widget build(BuildContext context) {
    return const Row(
      children: [
        Expanded(
          child: _MetricCard(label: 'Treinos', value: '12'),
        ),
        SizedBox(width: 10),
        Expanded(
          child: _MetricCard(label: 'Conclusão', value: '86%'),
        ),
        SizedBox(width: 10),
        Expanded(
          child: _MetricCard(label: 'Carga', value: '+8kg'),
        ),
      ],
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String label;
  final String value;

  const _MetricCard({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withOpacity(0.06)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            style: const TextStyle(
              color: AppColors.goldSoft,
              fontSize: 20,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(
              color: AppColors.muted,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class _ExerciseItem extends StatelessWidget {
  final String name;
  final String detail;
  final bool done;

  const _ExerciseItem({
    required this.name,
    required this.detail,
    required this.done,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.card,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: done ? AppColors.gold.withOpacity(0.55) : Colors.white.withOpacity(0.06),
        ),
      ),
      child: Row(
        children: [
          Icon(
            done ? Icons.check_circle : Icons.radio_button_unchecked,
            color: done ? AppColors.goldSoft : AppColors.muted,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    color: AppColors.text,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  detail,
                  style: const TextStyle(
                    color: AppColors.muted,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SectionTitle extends StatelessWidget {
  final String title;
  final String subtitle;

  const _SectionTitle({
    required this.title,
    required this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: AppColors.text,
            fontSize: 34,
            fontWeight: FontWeight.w900,
          ),
        ),
        const SizedBox(height: 10),
        Text(
          subtitle,
          style: const TextStyle(
            color: AppColors.muted,
            fontSize: 16,
          ),
        ),
      ],
    );
  }
}

class _FeatureGrid extends StatelessWidget {
  const _FeatureGrid();

  @override
  Widget build(BuildContext context) {
    final width = MediaQuery.of(context).size.width;
    final columns = width > 1100 ? 4 : width > 700 ? 2 : 1;

    final features = [
      const _FeatureCard(
        icon: Icons.app_registration,
        title: 'Painel do profissional',
        text: 'Cadastro de alunos, criação de treinos e organização da rotina.',
      ),
      const _FeatureCard(
        icon: Icons.phone_android,
        title: 'App do aluno',
        text: 'Treino no celular com exercícios, carga, descanso e conclusão.',
      ),
      const _FeatureCard(
        icon: Icons.qr_code,
        title: 'Link e QR Code',
        text: 'Entrega simples para cada aluno acessar seu treino rapidamente.',
      ),
      const _FeatureCard(
        icon: Icons.insights,
        title: 'Histórico e evolução',
        text: 'Base preparada para relatórios, acompanhamento e IA futura.',
      ),
    ];

    return GridView.count(
      crossAxisCount: columns,
      crossAxisSpacing: 16,
      mainAxisSpacing: 16,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      childAspectRatio: columns == 1 ? 2.8 : 1.25,
      children: features,
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String text;

  const _FeatureCard({
    required this.icon,
    required this.title,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        color: AppColors.blackSoft.withOpacity(0.9),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: Colors.white.withOpacity(0.07)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: AppColors.goldSoft, size: 30),
          const SizedBox(height: 18),
          Text(
            title,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 18,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 10),
          Text(
            text,
            style: const TextStyle(
              color: AppColors.muted,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _FounderOffer extends StatelessWidget {
  const _FounderOffer();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          colors: [
            Color(0xFF1B1608),
            Color(0xFF0D0D0D),
          ],
        ),
        border: Border.all(color: AppColors.border),
      ),
      child: Wrap(
        spacing: 24,
        runSpacing: 20,
        alignment: WrapAlignment.spaceBetween,
        crossAxisAlignment: WrapCrossAlignment.center,
        children: [
          const SizedBox(
            width: 620,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Plano fundador',
                  style: TextStyle(
                    color: AppColors.goldSoft,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
                SizedBox(height: 8),
                Text(
                  'Comece com treinos digitais e evolua para uma plataforma completa.',
                  style: TextStyle(
                    color: AppColors.text,
                    fontSize: 28,
                    fontWeight: FontWeight.w900,
                  ),
                ),
                SizedBox(height: 10),
                Text(
                  'Primeira versão focada em personal/professor individual. '
                  'Academias, IA e equipamentos entram como módulos futuros.',
                  style: TextStyle(
                    color: AppColors.muted,
                    fontSize: 15,
                    height: 1.5,
                  ),
                ),
              ],
            ),
          ),
          _HeroButton(
            text: 'Entrar na lista de espera',
            icon: Icons.arrow_forward,
            filled: true,
            onTap: () {},
          ),
        ],
      ),
    );
  }
}

class _HeroButton extends StatelessWidget {
  final String text;
  final IconData icon;
  final bool filled;
  final VoidCallback onTap;

  const _HeroButton({
    required this.text,
    required this.icon,
    required this.filled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ElevatedButton.icon(
      onPressed: onTap,
      icon: Icon(icon),
      label: Text(text),
      style: ElevatedButton.styleFrom(
        backgroundColor: filled ? AppColors.gold : Colors.transparent,
        foregroundColor: filled ? Colors.black : AppColors.goldSoft,
        side: BorderSide(
          color: filled ? AppColors.gold : AppColors.border,
        ),
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 18),
        textStyle: const TextStyle(
          fontWeight: FontWeight.w900,
          fontSize: 15,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(999),
        ),
      ),
    );
  }
}

class _SmallButton extends StatelessWidget {
  final String text;
  final bool filled;
  final VoidCallback onTap;

  const _SmallButton({
    required this.text,
    required this.filled,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return TextButton(
      onPressed: onTap,
      style: TextButton.styleFrom(
        backgroundColor: filled ? AppColors.gold : Colors.transparent,
        foregroundColor: filled ? Colors.black : AppColors.text,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(999),
          side: BorderSide(
            color: filled ? AppColors.gold : AppColors.border,
          ),
        ),
      ),
      child: Text(
        text,
        style: const TextStyle(fontWeight: FontWeight.w800),
      ),
    );
  }
}
