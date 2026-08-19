import 'dart:async';

import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

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
            _message = 'Conta criada. Confirme o e-mail enviado pelo FitNexus e depois entre com sua senha.';
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
    final String email = (_pendingConfirmationEmail ?? _emailController.text).trim();
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
      labelStyle: const TextStyle(color: FitColors.muted),
      filled: true,
      fillColor: FitColors.cardSoft,
      suffixIcon: suffixIcon,
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: FitColors.border),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: FitColors.gold, width: 1.4),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: Colors.redAccent),
      ),
      focusedErrorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: Colors.redAccent, width: 1.4),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return FitShell(
      maxWidth: 680,
      child: FitCard(
        padding: const EdgeInsets.all(30),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              const SectionLabel('Acesso seguro'),
              const SizedBox(height: 12),
              Text(
                _registerMode ? 'Crie seu espaço profissional' : 'Entre no FitNexus',
                style: const TextStyle(
                  color: FitColors.text,
                  fontSize: 34,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                _registerMode
                    ? 'Sua conta já nasce isolada por organização, com autenticação e regras de acesso no banco.'
                    : 'Acesse seu painel, seus alunos e seus treinos com sessão protegida pelo Supabase Auth.',
                style: const TextStyle(color: FitColors.muted, height: 1.45),
              ),
              const SizedBox(height: 22),
              Row(
                children: <Widget>[
                  Expanded(
                    child: _ModeButton(
                      label: 'Entrar',
                      selected: !_registerMode,
                      onTap: () => _setMode(false),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: _ModeButton(
                      label: 'Criar conta',
                      selected: _registerMode,
                      onTap: () => _setMode(true),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 22),
              if (_registerMode) ...<Widget>[
                TextFormField(
                  controller: _nameController,
                  enabled: !_busy,
                  textInputAction: TextInputAction.next,
                  style: const TextStyle(color: FitColors.text),
                  decoration: _decoration('Seu nome'),
                  validator: (String? value) => _required(value, 'seu nome'),
                ),
                const SizedBox(height: 12),
                TextFormField(
                  controller: _organizationController,
                  enabled: !_busy,
                  textInputAction: TextInputAction.next,
                  style: const TextStyle(color: FitColors.text),
                  decoration: _decoration('Academia, studio ou nome profissional'),
                  validator: (String? value) => _required(value, 'o nome do seu espaço'),
                ),
                const SizedBox(height: 12),
              ],
              TextFormField(
                controller: _emailController,
                enabled: !_busy,
                keyboardType: TextInputType.emailAddress,
                textInputAction: TextInputAction.next,
                autofillHints: const <String>[AutofillHints.email],
                style: const TextStyle(color: FitColors.text),
                decoration: _decoration('E-mail'),
                validator: _validateEmail,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _passwordController,
                enabled: !_busy,
                obscureText: _obscurePassword,
                textInputAction: TextInputAction.done,
                autofillHints: <String>[
                  _registerMode ? AutofillHints.newPassword : AutofillHints.password,
                ],
                onFieldSubmitted: (_) => _submit(),
                style: const TextStyle(color: FitColors.text),
                decoration: _decoration(
                  'Senha',
                  suffixIcon: IconButton(
                    onPressed: _busy
                        ? null
                        : () => setState(() => _obscurePassword = !_obscurePassword),
                    icon: Icon(
                      _obscurePassword ? Icons.visibility_rounded : Icons.visibility_off_rounded,
                      color: FitColors.gold,
                    ),
                  ),
                ),
                validator: _validatePassword,
              ),
              if (_message != null) ...<Widget>[
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: _messageIsError
                        ? Colors.redAccent.withValues(alpha: 0.10)
                        : FitColors.gold.withValues(alpha: 0.10),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: _messageIsError ? Colors.redAccent : FitColors.gold,
                    ),
                  ),
                  child: Text(
                    _message!,
                    style: TextStyle(
                      color: _messageIsError ? Colors.redAccent : FitColors.goldSoft,
                      height: 1.4,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 22),
              GoldButton(
                label: _busy
                    ? 'Processando...'
                    : _registerMode
                        ? 'Criar minha conta'
                        : 'Entrar no painel',
                icon: _registerMode ? Icons.person_add_alt_1_rounded : Icons.login_rounded,
                onTap: _busy ? null : _submit,
              ),
              if (_pendingConfirmationEmail != null) ...<Widget>[
                const SizedBox(height: 10),
                TextButton.icon(
                  onPressed: _busy ? null : _resendConfirmation,
                  icon: const Icon(Icons.mark_email_unread_rounded),
                  label: const Text('Reenviar confirmação'),
                ),
              ],
              const SizedBox(height: 14),
              const Text(
                'O aplicativo usa apenas a chave pública do projeto. Permissões reais são decididas pelo login, pelos grants e pelo RLS no Postgres.',
                style: TextStyle(color: FitColors.muted, fontSize: 12, height: 1.45),
              ),
            ],
          ),
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
      borderRadius: BorderRadius.circular(16),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 180),
        padding: const EdgeInsets.symmetric(vertical: 14),
        alignment: Alignment.center,
        decoration: BoxDecoration(
          color: selected ? FitColors.gold : FitColors.cardSoft,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: selected ? FitColors.gold : FitColors.border),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: selected ? Colors.black : FitColors.text,
            fontWeight: FontWeight.w900,
          ),
        ),
      ),
    );
  }
}
