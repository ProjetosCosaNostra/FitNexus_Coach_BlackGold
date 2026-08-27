import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

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
    return Scaffold(
      backgroundColor: const Color(0xFF050505),
      appBar: AppBar(
        backgroundColor: const Color(0xFF050505),
        foregroundColor: Colors.white,
        title: const Text('Atendimento e privacidade'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 20, 20, 40),
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 860),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  const _ContactHeader(),
                  const SizedBox(height: 22),
                  _OfficialChannelCard(onCopyEmail: () => _copyEmail(context)),
                  const SizedBox(height: 18),
                  const _RequestGuidanceCard(),
                  const SizedBox(height: 18),
                  const _SafetyCard(),
                  const SizedBox(height: 18),
                  const _ProtocolStatusCard(),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _ContactHeader extends StatelessWidget {
  const _ContactHeader();

  @override
  Widget build(BuildContext context) {
    return const Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          'Canal oficial do FitNexus Coach BlackGold',
          key: ValueKey<String>('public-contact-title'),
          style: TextStyle(
            color: Color(0xFFFFD45A),
            fontSize: 28,
            fontWeight: FontWeight.w900,
          ),
        ),
        SizedBox(height: 10),
        Text(
          'Use este canal para suporte ao produto, privacidade e dados pessoais, cobrança e assuntos de segurança relacionados ao serviço.',
          style: TextStyle(color: Color(0xFFD6D6D6), fontSize: 16, height: 1.45),
        ),
      ],
    );
  }
}

class _OfficialChannelCard extends StatelessWidget {
  final VoidCallback onCopyEmail;

  const _OfficialChannelCard({required this.onCopyEmail});

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
              color: Colors.white,
              fontSize: 17,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 14),
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
          _Bullet('Informe no assunto se é suporte, cobrança, privacidade/dados ou segurança.'),
          _Bullet('Descreva o pedido de forma objetiva e informe o e-mail usado na conta, quando houver.'),
          _Bullet('Para pedidos relacionados a dados pessoais, explique o que você precisa: acesso, correção, exportação ou exclusão, conforme aplicável.'),
          _Bullet('Guarde a mensagem enviada e as respostas recebidas como registro do atendimento.'),
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
        style: TextStyle(color: Color(0xFFD6D6D6), fontSize: 15, height: 1.45),
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
        style: TextStyle(color: Color(0xFFD6D6D6), fontSize: 15, height: 1.45),
      ),
    );
  }
}

class _Panel extends StatelessWidget {
  final IconData icon;
  final String title;
  final Widget child;

  const _Panel({required this.icon, required this.title, required this.child});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: const Color(0xFF111111),
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFF3D3420)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            children: <Widget>[
              Icon(icon, color: const Color(0xFFE1B92F)),
              const SizedBox(width: 10),
              Expanded(
                child: Text(
                  title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 17,
                    fontWeight: FontWeight.w900,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          child,
        ],
      ),
    );
  }
}

class _Bullet extends StatelessWidget {
  final String text;

  const _Bullet(this.text);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Padding(
            padding: EdgeInsets.only(top: 3),
            child: Icon(Icons.circle, size: 7, color: Color(0xFFE1B92F)),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              text,
              style: const TextStyle(color: Color(0xFFD6D6D6), fontSize: 15, height: 1.42),
            ),
          ),
        ],
      ),
    );
  }
}
