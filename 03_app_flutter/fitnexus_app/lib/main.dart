import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

import 'app/fitnexus_app.dart';
import 'core/config/supabase_config.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();

  await Supabase.initialize(
    url: FitNexusSupabaseConfig.url,
    publishableKey: FitNexusSupabaseConfig.publishableKey,
  );

  runApp(const FitNexusApp());
}
