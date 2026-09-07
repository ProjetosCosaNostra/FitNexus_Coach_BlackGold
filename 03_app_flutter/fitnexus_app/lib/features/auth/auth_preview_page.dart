import 'dart:async';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import '../../core/theme/app_colors.dart';
import '../../core/theme/blackgold_tokens.dart';
import '../growth/public_funnel_telemetry.dart';
import '../shared/fitnexus_ui.dart';
import 'auth_service.dart';

class AuthPreviewPage extends StatefulWidget {
  const AuthPreviewPage({
    super.key,
    this.initialRegisterMode = false,
  });

  final bool initialRegisterMode;

  @override
  State<AuthPreviewPage> createState() => _AuthPreviewPageState();
}

class _AuthPreviewPageState extends State<AuthPreviewPage> {
  final GlobalKey<FormState> _formKey = GlobalKey<FormState>();
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _organizationController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  bool _registerMode = false;
  bool _busy = false;
  bool _obscurePassword = true;
  String? _message;
  bool _messageIsError = false;
  String? _pendingConfirmationEmail;

  @override
  void initState() {
    super.initState();
    _registerMode = widget.initialRegisterMode;
    if (_registerMode) {
      unawaited(PublicFunnelTelemetry.instance.captureSignupStarted());
    }
    if (AuthService.instance.currentSession != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) => _finishAuthenticatedFlow());
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _organizationController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  void _setMode(bool register) {
    if (_busy) return;
    if (register && !_registerMode) {
      unawaited(PublicFunnelTelemetry.instance.captureSignupStarted());
    }
    setState(() {
      _registerMode = register;
      _message = null;
      _messageIsError = false;
    });
  }

  String? _required(String? value, String label) {
    if (value == null || value.trim().isEmpty) {
      return 'Informe $label.';
    }
    return null;
  }

  String? _validateEmail(String? value) {
    final String? requiredMessage = _required(value, 'seu e-mail');
    if (requiredMessage != null) return requiredMessage;
    final String email = value!.trim();
    if (!email.contains('@') || !email.contains('.')) {
      return 'Informe um e-mail válido.';
    }
    return null;
  }

  String? _validatePassword(String? value) {
    final String? requiredMessage = _required(value, 'sua senha');
    if (requiredMessage != null) return requiredMessage;
    if (value!.length < 8) {
      return 'Use pelo menos 8 caracteres.';
    }
    return null;
  }

  String _friendlyError(Object error) {
    if (error is AuthException) return error.message;
    if (error is PostgrestException) return error.message;
    return 'Não foi possível concluir agora. Tente novamente.';
  }

  Future<void> _submit() async {
    if (_busy) return;
    if (!(_formKey.currentState?.validate() ?? false)) return;

    setState(() {
      _busy = true;
      _message = null;
      _messageIsError = false;
    });

    try {
      if (_registerMode) {
        final AuthResponse response = await AuthService.instance.signUpProfessor(
          fullName: _nameController.text,
          organizationName: _organizationController.text,
          email: _emailController.text,
          password: _passwordController.text,
        );

        if (response.session == null) {
          setState(() {
            _pendingConfirmationEmail = _emailController.text.trim();
            _message =
                'Conta criada. Confirme o e-mail enviado pelo FitNexus e depois entre com sua senha.';
            _messageIsError = false;
            _registerMode = false;
          });
          return;
        }

        await AuthService.instance.ensureProfessorOrganization(
          preferredName: _organizationController.text,
        );
        await _goToProfessor();
      } else {
        await AuthService.instance.signIn(
          email: _emailController.text,
          password: _passwordController.text,
        );
        await _finishAuthenticatedFlow();
      }
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = _friendlyError(error);
        _messageIsError = true;
      });
    } finally {
      if (mounted) {
        setState(() => _busy = false);
      }
    }
  }

  Future<void> _finishAuthenticatedFlow() async {
    try {
      await AuthService.instance.ensureProfessorOrganization();
      await _goToProfessor();
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = _friendlyError(error);
        _messageIsError = true;
      });
    }
  }

  Future<void> _goToProfessor() async {
    if (!mounted) return;
    Navigator.of(context).pushNamedAndRemoveUntil(
      '/professor',
      (Route<dynamic> route) => false,
    );
  }

  Future<void> _resendConfirmation() async {
    final String email =
        (_pendingConfirmationEmail ?? _emailController.text).trim();
    if (email.isEmpty || _busy) return;

    setState(() {
      _busy = true;
      _message = null;
    });

    try {
      await AuthService.instance.resendSignUpConfirmation(email);
      if (!mounted) return;
      setState(() {
        _message = 'Novo e-mail de confirmação enviado.';
        _messageIsError = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _message = _friendlyError(error);
        _messageIsError = true;
      });
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  InputDecoration _decoration(String label, {Widget? suffixIcon}) {
    return InputDecoration(
      labelText: label,
      suffixIcon: suffixIcon,
    );
  }

  @override
  Widget build(BuildContext context) {
    return FitShell(
      maxWidth: 1040,
      child: LayoutBuilder(
        builder: (BuildContext context, BoxConstraints constraints) {
          final bool desktop = constraints.maxWidth >= 820;
          final Widget form = _buildForm(context);

          if (!desktop) {
            return FitCard(
              highlight: true,
              padding: const EdgeInsets.all(BlackGoldSpace.lg),
              child: form,
            );
          }

          return FitCard(
            highlight: true,
            padding: EdgeInsets.zero,
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: <Widget>[
                const Expanded(
                  flex: 9,
                  child: _AuthBrandPanel(),
                ),
                Container(
                  width: 1,
                  color: AppColors.borderGold.withValues(alpha: 0.46),
                ),
                Expanded(
                  flex: 11,
                  child: Padding(
                    padding: const EdgeInsets.all(BlackGoldSpace.xxl),
                    child: form,
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildForm(BuildContext context) {
    return Form(
      key: _formKey,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const SectionLabel('Acesso seguro'),
          const SizedBox(height: BlackGoldSpace.sm),
          Text(
            _registerMode ? 'Crie seu espaço profissional' : 'Entre no FitNexus',
            style: Theme.of(context).textTheme.headlineLarge,
          ),
          const SizedBox(height: BlackGoldSpace.xs),
          Text(
            _registerMode
                ? 'Comece com a mesma experiência BlackGold do painel: organização isolada, autenticação e acesso protegido.'
                : 'Acesse alunos, treinos, evolução e decisões em um único sistema profissional.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: BlackGoldSpace.lg),
          Row(
            children: <Widget>[
              Expanded(
                child: _ModeButton(
                  label: 'Entrar',
                  selected: !_registerMode,
                  onTap: () => _setMode(false),
                ),
              ),
              const SizedBox(width: BlackGoldSpace.xs),
              Expanded(
                child: _ModeButton(
                  label: 'Criar conta',
                  selected: _registerMode,
                  onTap: () => _setMode(true),
                ),
              ),
            ],
          ),
          const SizedBox(height: BlackGoldSpace.lg),
          if (_registerMode) ...<Widget>[
            TextFormField(
              controller: _nameController,
              enabled: !_busy,
              textInputAction: TextInputAction.next,
              decoration: _decoration('Seu nome'),
              validator: (String? value) => _required(value, 'seu nome'),
            ),
            const SizedBox(height: BlackGoldSpace.sm),
            TextFormField(
              controller: _organizationController,
              enabled: !_busy,
              textInputAction: TextInputAction.next,
              decoration: _decoration('Academia, studio ou nome profissional'),
              validator: (String? value) =>
                  _required(value, 'o nome do seu espaço'),
            ),
            const SizedBox(height: BlackGoldSpace.sm),
          ],
          TextFormField(
            controller: _emailController,
            enabled: !_busy,
            keyboardType: TextInputType.emailAddress,
            textInputAction: TextInputAction.next,
            autofillHints: const <String>[AutofillHints.email],
            decoration: _decoration('E-mail'),
            validator: _validateEmail,
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          TextFormField(
            controller: _passwordController,
            enabled: !_busy,
            obscureText: _obscurePassword,
            textInputAction: TextInputAction.done,
            autofillHints: <String>[
              _registerMode
                  ? AutofillHints.newPassword
                  : AutofillHints.password,
            ],
            onFieldSubmitted: (_) => _submit(),
            decoration: _decoration(
              'Senha',
              suffixIcon: IconButton(
                onPressed: _busy
                    ? null
                    : () => setState(
                          () => _obscurePassword = !_obscurePassword,
                        ),
                icon: Icon(
                  _obscurePassword
                      ? Icons.visibility_rounded
                      : Icons.visibility_off_rounded,
                  color: AppColors.gold,
                ),
              ),
            ),
            validator: _validatePassword,
          ),
          if (_message != null) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.md),
            _StatusMessage(
              text: _message!,
              isError: _messageIsError,
            ),
          ],
          const SizedBox(height: BlackGoldSpace.lg),
          SizedBox(
            width: double.infinity,
            child: GoldButton(
              label: _busy
                  ? 'Processando...'
                  : _registerMode
                      ? 'Criar minha conta'
                      : 'Entrar no painel',
              icon: _registerMode
                  ? Icons.person_add_alt_1_rounded
                  : Icons.login_rounded,
              onTap: _busy ? null : _submit,
            ),
          ),
          if (_pendingConfirmationEmail != null) ...<Widget>[
            const SizedBox(height: BlackGoldSpace.xs),
            TextButton.icon(
              onPressed: _busy ? null : _resendConfirmation,
              icon: const Icon(Icons.mark_email_unread_rounded),
              label: const Text('Reenviar confirmação'),
            ),
          ],
          const SizedBox(height: BlackGoldSpace.md),
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const Icon(
                Icons.verified_user_outlined,
                color: AppColors.goldSoft,
                size: 16,
              ),
              const SizedBox(width: BlackGoldSpace.xs),
              Expanded(
                child: Text(
                  'Sessão protegida pelo Supabase Auth. Permissões reais continuam decididas pelos grants e pelo RLS no Postgres.',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _AuthBrandPanel extends StatelessWidget {
  const _AuthBrandPanel();

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(minHeight: 590),
      padding: const EdgeInsets.all(BlackGoldSpace.xxl),
      decoration: const BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: <Color>[
            Color(0xFF151107),
            Color(0xFF080807),
            Color(0xFF020202),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          const Icon(
            Icons.fitness_center_rounded,
            color: AppColors.goldSoft,
            size: 34,
          ),
          const Spacer(),
          const Text(
            'SUA EVOLUÇÃO',
            style: TextStyle(
              color: AppColors.goldSoft,
              fontSize: 11,
              fontWeight: FontWeight.w900,
              letterSpacing: 2.1,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          Text.rich(
            TextSpan(
              children: <InlineSpan>[
                const TextSpan(text: 'Tudo sob\n'),
                TextSpan(
                  text: 'controle.',
                  style: TextStyle(color: AppColors.goldSoft),
                ),
              ],
            ),
            style: Theme.of(context).textTheme.displayMedium,
          ),
          const SizedBox(height: BlackGoldSpace.md),
          const Text(
            'Alunos, treinos, nutrição, progresso e decisões inteligentes com a mesma linguagem visual do painel BlackGold.',
            style: TextStyle(
              color: AppColors.muted,
              fontSize: 14,
              height: 1.5,
            ),
          ),
          const SizedBox(height: BlackGoldSpace.xxl),
          const _SecurityRow(
            icon: Icons.shield_outlined,
            text: 'Acesso seguro e isolado por organização',
          ),
          const SizedBox(height: BlackGoldSpace.sm),
          const _SecurityRow(
            icon: Icons.auto_awesome_outlined,
            text: 'Experiência premium consistente em todas as telas',
          ),
        ],
      ),
    );
  }
}

class _SecurityRow extends StatelessWidget {
  const _SecurityRow({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Icon(icon, color: AppColors.gold, size: 18),
        const SizedBox(width: BlackGoldSpace.xs),
        Expanded(
          child: Text(
            text,
            style: const TextStyle(
              color: AppColors.text,
              fontSize: 12,
              height: 1.35,
              fontWeight: FontWeight.w600,
            ),
          ),
        ),
      ],
    );
  }
}

class _StatusMessage extends StatelessWidget {
  const _StatusMessage({required this.text, required this.isError});

  final String text;
  final bool isError;

  @override
  Widget build(BuildContext context) {
    final Color accent = isError ? AppColors.danger : AppColors.gold;
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(BlackGoldSpace.sm),
      decoration: BoxDecoration(
        color: accent.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(BlackGoldRadius.control),
        border: Border.all(
          color: accent.withValues(alpha: 0.72),
          width: BlackGoldStroke.hairline,
        ),
      ),
      child: Text(
        text,
        style: TextStyle(
          color: isError ? AppColors.danger : AppColors.goldSoft,
          height: 1.4,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}

class _ModeButton extends StatelessWidget {
  const _ModeButton({
    required this.label,
    required this.selected,
    required this.onTap,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(BlackGoldRadius.control),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 160),
        padding: const EdgeInsets.symmetric(vertical: 13),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: selected
              ? AppColors.gold
              : AppColors.cardRaised.withValues(alpha: 0.92),
          borderRadius: BorderRadius.circular(BlackGoldRadius.control),
          border: Border.all(
            color: selected ? AppColors.gold : AppColors.borderGold,
            width: BlackGoldStroke.regular,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.black : AppColors.text,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    );
  }
}
