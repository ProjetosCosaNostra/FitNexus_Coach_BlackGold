import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../shared/fitnexus_ui.dart';

class PublicContactPage extends StatelessWidget {
  const PublicContactPage({super.key});

  static const String publicEmail = 'projetoscosanostra@gmail.com';

  Future<void> _copyEmail(BuildContext context) async {
    await Clipboard.setData(const ClipboardData(text: publicEmail));
    if (!context.mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('E-mail oficial copiado.')),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FitShell(
      maxWidth: 900,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const FitPageTitle(
            eyebrow: 'Atendimento e privacidade',
            title: 'Canal oficial do FitNexus Coach BlackGold',
            description:
                'Suporte ao produto, privacidade e dados pessoais, cobrança e assuntos de segurança relacionados ao serviço.',
          ),
          const SizedBox(height: BlackGoldSpace.xl),
          _OfficialChannelCard(onCopyEmail: () => _copyEmail(context)),
          const SizedBox(height: BlackGoldSpace.md),
          const _RequestGuidanceCard(),
          const SizedBox(height: BlackGoldSpace.md),
          const _SafetyCard(),
          const SizedBox(height: BlackGoldSpace.md),
          const _ProtocolStatusCard(),
          const SizedBox.shrink(
            key: ValueKey<String>('public-contact-title'),
          ),
        ],
      ),
    );
  }
}

class _OfficialChannelCard extends StatelessWidget {
  const _OfficialChannelCard({required this.onCopyEmail});

  final VoidCallback onCopyEmail;

  @override
  Widget build(BuildContext context) {
    return _Panel(
      icon: Icons.alternate_email_rounded,
      title: 'E-mail oficial público',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SelectableText(
            PublicContactPage.publicEmail,
            key: ValueKey<String>('public-contact-email'),
            style: TextStyle(
              color: AppColors.text,
              fontSize: 17,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.md),
          OutlinedButton.icon(
            onPressed: onCopyEmail,
            icon: const Icon(Icons.copy_rounded, size: 18),
            label: const Text('Copiar e-mail'),
          ),
        ],
      ),
    );
  }
}

class _RequestGuidanceCard extends StatelessWidget {
  const _RequestGuidanceCard();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      icon: Icons.fact_check_outlined,
      title: 'Como enviar sua solicitação',
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          _Bullet(
            'Informe no assunto se é suporte, cobrança, privacidade/dados ou segurança.',
          ),
          _Bullet(
            'Descreva o pedido de forma objetiva e informe o e-mail usado na conta, quando houver.',
          ),
          _Bullet(
            'Para pedidos relacionados a dados pessoais, explique o que você precisa: acesso, correção, exportação ou exclusão, conforme aplicável.',
          ),
          _Bullet(
            'Guarde a mensagem enviada e as respostas recebidas como registro do atendimento.',
          ),
        ],
      ),
    );
  }
}

class _SafetyCard extends StatelessWidget {
  const _SafetyCard();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      icon: Icons.security_rounded,
      title: 'Proteja seus dados',
      child: Text(
        'Não envie senha, token, chave de API, código de autenticação ou documento sensível sem uma instrução específica e segura do atendimento.',
        style: TextStyle(
          color: AppColors.muted,
          fontSize: 14,
          height: 1.45,
        ),
      ),
    );
  }
}

class _ProtocolStatusCard extends StatelessWidget {
  const _ProtocolStatusCard();

  @override
  Widget build(BuildContext context) {
    return const _Panel(
      icon: Icons.receipt_long_rounded,
      title: 'Status do protocolo automático',
      child: Text(
        'Este endereço é o canal público autorizado. A automação de triagem, numeração de protocolo e acompanhamento ainda depende da implantação operacional e de evidência em produção; esta tela não declara esse gate como concluído.',
        key: ValueKey<String>('public-contact-protocol-boundary'),
        style: TextStyle(
          color: AppColors.muted,
          fontSize: 14,
          height: 1.45,
        ),
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  const _Panel({
    required this.icon,
    required this.title,
    required this.child,
  });

  final IconData icon;
  final String title;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: FitCard(
        padding: const EdgeInsets.all(BlackGoldSpace.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Row(
              children: <Widget>[
                Container(
                  width: 36,
                  height: 36,
                  alignment: Alignment.center,
                  decoration: BoxDecoration(
                    color: AppColors.gold.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(BlackGoldRadius.control),
                    border: Border.all(
                      color: AppColors.gold.withValues(alpha: 0.34),
                      width: BlackGoldStroke.hairline,
                    ),
                  ),
                  child: Icon(icon, color: AppColors.goldSoft, size: 19),
                ),
                const SizedBox(width: BlackGoldSpace.sm),
                Expanded(
                  child: Text(
                    title,
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                ),
              ],
            ),
            const SizedBox(height: BlackGoldSpace.md),
            child,
          ],
        ),
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  const _Bullet(this.text);

  final String text;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: BlackGoldSpace.sm),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Padding(
            padding: EdgeInsets.only(top: 5),
            child: Icon(
              Icons.circle,
              size: 6,
              color: AppColors.gold,
            ),
          ),
          const SizedBox(width: BlackGoldSpace.sm),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(
                color: AppColors.muted,
                fontSize: 14,
                height: 1.42,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
