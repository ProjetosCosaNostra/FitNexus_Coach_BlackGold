class GrowthAttributionTouch {
  const GrowthAttributionTouch({
    required this.source,
    required this.medium,
    required this.campaign,
    required this.term,
    required this.content,
    required this.landingPath,
  });

  final String? source;
  final String? medium;
  final String? campaign;
  final String? term;
  final String? content;
  final String landingPath;

  static GrowthAttributionTouch? fromUri(Uri uri) {
    String? read(String key, int maxLength) {
      final String raw = (uri.queryParameters[key] ?? '').trim();
      if (raw.isEmpty) return null;
      return raw.length <= maxLength ? raw : raw.substring(0, maxLength);
    }

    final String? source = read('utm_source', 100);
    final String? medium = read('utm_medium', 100);
    final String? campaign = read('utm_campaign', 160);
    final String? term = read('utm_term', 160);
    final String? content = read('utm_content', 160);

    if (<String?>[source, medium, campaign, term, content]
        .every((String? value) => value == null)) {
      return null;
    }

    final String path = uri.path.trim().isEmpty ? '/' : uri.path.trim();
    final String safePath = path.startsWith('/') ? path : '/';

    return GrowthAttributionTouch(
      source: source,
      medium: medium,
      campaign: campaign,
      term: term,
      content: content,
      landingPath: safePath.length <= 500 ? safePath : safePath.substring(0, 500),
    );
  }

  String get fingerprint => <String?>[
        source,
        medium,
        campaign,
        term,
        content,
        landingPath,
      ].map((String? value) => value ?? '').join('|');

  Map<String, dynamic> rpcParams(String organizationId) => <String, dynamic>{
        'p_organization_id': organizationId,
        'p_source': source,
        'p_medium': medium,
        'p_campaign': campaign,
        'p_term': term,
        'p_content': content,
        'p_landing_path': landingPath,
        'p_referrer_host': null,
      };
}
