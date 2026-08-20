import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const CORS_BASE = {
  "access-control-allow-headers": "authorization, x-client-info, apikey, content-type",
  "access-control-allow-methods": "GET, POST, OPTIONS",
  "access-control-max-age": "600",
};

const ALLOWED_BROWSER_ORIGINS = new Set([
  "https://projetoscosanostra.github.io",
  "http://localhost",
  "http://127.0.0.1",
]);

const SPOOF_SENTINEL = "203.0.113.77";
const MAX_BODY_BYTES = 16_384;
const RATE_LIMIT_RPC = "check_student_access_network_rate_limit_v1";

const ROUTE_TO_RPC = {
  get_workout: "get_student_workout_v2",
  start_workout: "start_student_workout_v2",
  set_completion: "set_student_exercise_completion_v2",
  get_feedback_context: "get_student_feedback_context_v2",
  submit_feedback: "submit_student_workout_feedback_v2",
} as const;

type StudentAction = keyof typeof ROUTE_TO_RPC;
type JsonObject = Record<string, unknown>;
type BackendCredential = {
  apiKey: string;
  authorization?: string;
};

type RpcResult = {
  ok: boolean;
  status: number;
  data: unknown;
};

function corsHeaders(req: Request): Record<string, string> {
  const origin = req.headers.get("origin")?.trim() ?? "";
  const allowed = ALLOWED_BROWSER_ORIGINS.has(origin)
    || origin.startsWith("http://localhost:")
    || origin.startsWith("http://127.0.0.1:");

  return allowed
    ? { ...CORS_BASE, "access-control-allow-origin": origin, vary: "Origin" }
    : CORS_BASE;
}

function json(req: Request, status: number, body: unknown): Response {
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

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isStudentAction(value: unknown): value is StudentAction {
  return typeof value === "string" && Object.hasOwn(ROUTE_TO_RPC, value);
}

function backendCredential(): BackendCredential | null {
  const secretKeysRaw = Deno.env.get("SUPABASE_SECRET_KEYS");
  if (secretKeysRaw) {
    try {
      const parsed = JSON.parse(secretKeysRaw) as Record<string, unknown>;
      const secretKey = parsed.default;
      if (typeof secretKey === "string" && secretKey.startsWith("sb_secret_")) {
        return { apiKey: secretKey };
      }
    } catch {
      return null;
    }
  }

  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  if (legacy?.trim()) {
    return {
      apiKey: legacy,
      authorization: `Bearer ${legacy}`,
    };
  }

  return null;
}

async function callRpc(
  baseUrl: string,
  credential: BackendCredential,
  rpc: string,
  params: JsonObject,
): Promise<RpcResult> {
  const headers: Record<string, string> = {
    apikey: credential.apiKey,
    "content-type": "application/json",
    accept: "application/json",
  };
  if (credential.authorization) {
    headers.authorization = credential.authorization;
  }

  try {
    const response = await fetch(`${baseUrl}/rest/v1/rpc/${rpc}`, {
      method: "POST",
      headers,
      body: JSON.stringify(params),
    });

    let data: unknown = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }

    return { ok: response.ok, status: response.status, data };
  } catch {
    return { ok: false, status: 0, data: null };
  }
}

function requireString(payload: JsonObject, key: string): string | null {
  const value = payload[key];
  return typeof value === "string" ? value : null;
}

function buildRpcParams(action: StudentAction, payload: JsonObject): JsonObject | null {
  const token = requireString(payload, "token");
  if (token === null) return null;

  if (action === "get_workout" || action === "get_feedback_context") {
    return { p_token: token };
  }

  const commandId = requireString(payload, "command_id");
  if (commandId === null) return null;

  if (action === "start_workout") {
    return { p_token: token, p_command_id: commandId };
  }

  const sessionId = requireString(payload, "session_id");
  if (sessionId === null) return null;

  if (action === "set_completion") {
    const exerciseId = requireString(payload, "exercise_id");
    const completed = payload.completed;
    if (exerciseId === null || typeof completed !== "boolean") return null;
    return {
      p_token: token,
      p_session_id: sessionId,
      p_exercise_id: exerciseId,
      p_completed: completed,
      p_command_id: commandId,
    };
  }

  const perceivedExertion = payload.perceived_exertion;
  const painScore = payload.pain_score;
  const energyScore = payload.energy_score;
  const painLocation = payload.pain_location;
  const note = payload.note;
  if (
    !Number.isInteger(perceivedExertion)
    || !Number.isInteger(painScore)
    || !Number.isInteger(energyScore)
    || !(painLocation === null || typeof painLocation === "string")
    || !(note === null || typeof note === "string")
  ) {
    return null;
  }

  return {
    p_token: token,
    p_session_id: sessionId,
    p_perceived_exertion: perceivedExertion,
    p_pain_score: painScore,
    p_energy_score: energyScore,
    p_pain_location: painLocation,
    p_note: note,
    p_command_id: commandId,
  };
}

async function handleStudentPost(req: Request): Promise<Response> {
  const cloudflareOrigin = req.headers.get("cf-connecting-ip");
  if (!plausibleNetworkOrigin(cloudflareOrigin)) {
    return json(req, 503, { ok: false, error: "STUDENT_NETWORK_ORIGIN_UNAVAILABLE" });
  }

  const contentLength = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
    return json(req, 413, { ok: false, error: "STUDENT_GATEWAY_BODY_TOO_LARGE" });
  }

  let bodyText = "";
  try {
    bodyText = await req.text();
  } catch {
    return json(req, 400, { ok: false, error: "STUDENT_GATEWAY_BODY_INVALID" });
  }
  if (new TextEncoder().encode(bodyText).byteLength > MAX_BODY_BYTES) {
    return json(req, 413, { ok: false, error: "STUDENT_GATEWAY_BODY_TOO_LARGE" });
  }

  let payload: unknown;
  try {
    payload = JSON.parse(bodyText);
  } catch {
    return json(req, 400, { ok: false, error: "STUDENT_GATEWAY_BODY_INVALID" });
  }
  if (!isObject(payload) || !isStudentAction(payload.action)) {
    return json(req, 400, { ok: false, error: "STUDENT_GATEWAY_ACTION_INVALID" });
  }

  const baseUrl = Deno.env.get("SUPABASE_URL")?.replace(/\/$/, "") ?? "";
  const credential = backendCredential();
  if (!baseUrl || credential === null) {
    return json(req, 503, { ok: false, error: "STUDENT_GATEWAY_BACKEND_AUTH_UNAVAILABLE" });
  }

  // Security order invariant: the durable network-origin limiter executes before any
  // possession-token validation or student v2 RPC. The token is never logged or echoed.
  const rateLimit = await callRpc(baseUrl, credential, RATE_LIMIT_RPC, {
    p_network_origin: cloudflareOrigin!.trim(),
    p_operation: payload.action,
  });
  if (!rateLimit.ok || !isObject(rateLimit.data)) {
    return json(req, 503, { ok: false, error: "STUDENT_NETWORK_RATE_LIMIT_UNAVAILABLE" });
  }
  if (rateLimit.data.error === "STUDENT_NETWORK_RATE_LIMITED") {
    const retryAfter = Number(rateLimit.data.retry_after_seconds);
    return json(req, 429, {
      ok: false,
      error: "STUDENT_NETWORK_RATE_LIMITED",
      retry_after_seconds: Number.isFinite(retryAfter) ? retryAfter : 60,
    });
  }
  if (rateLimit.data.ok !== true) {
    return json(req, 503, { ok: false, error: "STUDENT_NETWORK_RATE_LIMIT_UNAVAILABLE" });
  }

  const rpcParams = buildRpcParams(payload.action, payload);
  if (rpcParams === null) {
    return json(req, 400, { ok: false, error: "STUDENT_GATEWAY_PAYLOAD_INVALID" });
  }

  const studentRpc = await callRpc(
    baseUrl,
    credential,
    ROUTE_TO_RPC[payload.action],
    rpcParams,
  );
  if (!studentRpc.ok || studentRpc.data === null) {
    return json(req, 502, { ok: false, error: "STUDENT_GATEWAY_UPSTREAM_FAILED" });
  }

  return json(req, 200, studentRpc.data);
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(req) });
  }

  if (req.method === "GET") {
    const cloudflareOrigin = req.headers.get("cf-connecting-ip");
    const cloudflareRay = req.headers.get("cf-ray");

    return json(req, 200, {
      ok: true,
      mode: "stage28_gateway_candidate_repository_source",
      network_origin_source_candidate: "cf-connecting-ip",
      network_origin_candidate_available: plausibleNetworkOrigin(cloudflareOrigin),
      candidate_equals_known_client_spoof_sentinel:
        cloudflareOrigin?.trim() === SPOOF_SENTINEL,
      cloudflare_ray_available: Boolean(cloudflareRay?.trim()),
      x_forwarded_for_present_but_untrusted: Boolean(req.headers.get("x-forwarded-for")),
      x_real_ip_present_but_untrusted: Boolean(req.headers.get("x-real-ip")),
      raw_network_origin_returned: false,
      request_body_read: false,
      network_origin_rate_limit_enabled: true,
      student_rpc_forwarding_enabled: true,
      launch_gate_authority: false,
    });
  }

  if (req.method === "POST") {
    return await handleStudentPost(req);
  }

  return json(req, 405, {
    ok: false,
    error: "STUDENT_GATEWAY_METHOD_NOT_ALLOWED",
  });
});
