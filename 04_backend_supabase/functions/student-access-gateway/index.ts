import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const CORS_BASE = {
  "access-control-allow-headers": "authorization, x-client-info, apikey, content-type",
  "access-control-allow-methods": "GET, OPTIONS",
  "access-control-max-age": "600",
};

const ALLOWED_BROWSER_ORIGINS = new Set([
  "https://projetoscosanostra.github.io",
  "http://localhost",
  "http://127.0.0.1",
]);

// RFC 5737 TEST-NET-3 sentinel. It is intentionally not a real user/network address.
// The runtime probe returns only whether the platform-owned candidate equals this known
// client-supplied sentinel. The raw candidate is never returned, stored or logged.
const SPOOF_SENTINEL = "203.0.113.77";

function corsHeaders(req: Request): Record<string, string> {
  const origin = req.headers.get("origin")?.trim() ?? "";
  const allowed = ALLOWED_BROWSER_ORIGINS.has(origin)
    || origin.startsWith("http://localhost:")
    || origin.startsWith("http://127.0.0.1:");

  return allowed
    ? { ...CORS_BASE, "access-control-allow-origin": origin, vary: "Origin" }
    : CORS_BASE;
}

function json(req: Request, status: number, body: Record<string, unknown>): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { ...JSON_HEADERS, ...corsHeaders(req) },
  });
}

function plausibleNetworkOrigin(value: string | null): boolean {
  if (!value) return false;
  const normalized = value.trim();
  if (normalized.length < 3 || normalized.length > 64) return false;

  const ipv4 = normalized.split(".");
  if (ipv4.length === 4) {
    return ipv4.every((part) => {
      if (!/^\d{1,3}$/.test(part)) return false;
      const number = Number(part);
      return Number.isInteger(number) && number >= 0 && number <= 255;
    });
  }

  return normalized.includes(":") && /^[0-9a-fA-F:.]+$/.test(normalized);
}

Deno.serve((req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(req) });
  }

  // Stage 26 is deliberately a runtime metadata probe, not the student gateway cutover.
  // It returns only booleans. It never returns, stores or logs a client IP, bearer token,
  // forwarded-header value, request body or arbitrary payload.
  if (req.method === "GET") {
    const cloudflareOrigin = req.headers.get("cf-connecting-ip");
    const cloudflareRay = req.headers.get("cf-ray");

    return json(req, 200, {
      ok: true,
      mode: "origin_probe_not_student_gateway_cutover",
      network_origin_source_candidate: "cf-connecting-ip",
      network_origin_candidate_available: plausibleNetworkOrigin(cloudflareOrigin),
      candidate_equals_known_client_spoof_sentinel:
        cloudflareOrigin?.trim() === SPOOF_SENTINEL,
      cloudflare_ray_available: Boolean(cloudflareRay?.trim()),
      x_forwarded_for_present_but_untrusted: Boolean(req.headers.get("x-forwarded-for")),
      x_real_ip_present_but_untrusted: Boolean(req.headers.get("x-real-ip")),
      raw_network_origin_returned: false,
      request_body_read: false,
      student_rpc_forwarding_enabled: false,
      launch_gate_authority: false,
    });
  }

  return json(req, 503, {
    ok: false,
    error: "STUDENT_GATEWAY_NOT_CUTOVER",
    mode: "origin_probe_not_student_gateway_cutover",
  });
});
