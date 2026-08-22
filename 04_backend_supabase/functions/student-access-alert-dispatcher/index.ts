import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const PROVIDER = "telegram_bot_api";
const TELEGRAM_BASE_URL = "https://api.telegram.org";
const CLAIM_RPC = "claim_student_access_alert_delivery_v1";
const RECORD_RPC = "record_student_access_alert_delivery_v1";
const PROOF_MARKER = "fitnexus-stage34-alert-delivery-proof-v1";
const DISPATCH_HEADER = "x-fitnexus-alert-dispatch-token";
const MAX_BODY_BYTES = 2048;
const MAX_MESSAGE_CHARS = 2000;

const ALLOWED_SIGNAL_TYPES = new Set([
  "rate_limit_burst",
  "command_replay_burst",
  "token_rotation_burst",
  "network_rate_limit_burst",
]);
const ALLOWED_SEVERITIES = new Set(["high", "critical"]);
const ALLOWED_OPERATIONS = new Set([
  "get_workout",
  "start_workout",
  "set_completion",
  "get_feedback_context",
  "submit_feedback",
]);

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

function json(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: JSON_HEADERS,
  });
}

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
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

async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(value),
  );
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function secretsEqual(left: string, right: string): Promise<boolean> {
  if (!left || !right) return false;
  const [leftDigest, rightDigest] = await Promise.all([
    sha256Hex(left),
    sha256Hex(right),
  ]);
  return leftDigest === rightDigest;
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

function safeString(
  value: unknown,
  allowed: Set<string>,
): string | null {
  if (typeof value !== "string" || !allowed.has(value)) return null;
  return value;
}

function safeInteger(value: unknown): number | null {
  return typeof value === "number" && Number.isSafeInteger(value) && value >= 0
    ? value
    : null;
}

function safeTimestamp(value: unknown): string | null {
  if (typeof value !== "string" || value.length < 20 || value.length > 40) return null;
  const parsed = Date.parse(value);
  return Number.isFinite(parsed) ? new Date(parsed).toISOString() : null;
}

function buildMessage(claim: JsonObject): string | null {
  const signalId = safeInteger(claim.signal_id);
  const signalType = safeString(claim.signal_type, ALLOWED_SIGNAL_TYPES);
  const severity = safeString(claim.severity, ALLOWED_SEVERITIES);
  const operation = safeString(claim.operation, ALLOWED_OPERATIONS);
  const eventCount = safeInteger(claim.event_count);
  const windowStartedAt = safeTimestamp(claim.window_started_at);
  const firstSeenAt = safeTimestamp(claim.first_seen_at);
  const lastSeenAt = safeTimestamp(claim.last_seen_at);
  const proofMarker = claim.controlled_proof_marker;
  const proofValue = proofMarker === null
    ? "false"
    : proofMarker === PROOF_MARKER
    ? PROOF_MARKER
    : null;

  if (
    signalId === null || signalType === null || severity === null ||
    operation === null || eventCount === null || windowStartedAt === null ||
    firstSeenAt === null || lastSeenAt === null || proofValue === null
  ) {
    return null;
  }

  const message = [
    "FitNexus Coach BlackGold — alerta de segurança",
    "system: FitNexus Coach BlackGold",
    "environment: production",
    `signal_id: ${signalId}`,
    `signal_type: ${signalType}`,
    `severity: ${severity}`,
    `operation: ${operation}`,
    `event_count: ${eventCount}`,
    `window_started_at: ${windowStartedAt}`,
    `first_seen_at: ${firstSeenAt}`,
    `last_seen_at: ${lastSeenAt}`,
    `controlled_proof_marker: ${proofValue}`,
  ].join("\n");

  return message.length <= MAX_MESSAGE_CHARS ? message : null;
}

async function recordOutcome(
  baseUrl: string,
  credential: BackendCredential,
  claimToken: string,
  outcome: "delivered" | "failed" | "unknown",
  providerMessageId: number | null,
  errorCode: string | null,
): Promise<boolean> {
  const result = await callRpc(baseUrl, credential, RECORD_RPC, {
    p_claim_token: claimToken,
    p_outcome: outcome,
    p_provider_message_id: providerMessageId,
    p_error_code: errorCode,
  });
  return result.ok && isObject(result.data) && result.data.ok === true;
}

Deno.serve(async (req: Request) => {
  if (req.method !== "POST") {
    return json(405, { ok: false, error: "ALERT_DISPATCH_METHOD_NOT_ALLOWED" });
  }

  const configuredDispatchSecret =
    Deno.env.get("STUDENT_ACCESS_ALERT_DISPATCH_TOKEN")?.trim() ?? "";
  const suppliedDispatchSecret = req.headers.get(DISPATCH_HEADER)?.trim() ?? "";
  if (!configuredDispatchSecret ||
      !(await secretsEqual(configuredDispatchSecret, suppliedDispatchSecret))) {
    return json(401, { ok: false, error: "ALERT_DISPATCH_UNAUTHORIZED" });
  }

  const contentLength = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
    return json(413, { ok: false, error: "ALERT_DISPATCH_BODY_TOO_LARGE" });
  }

  let proofMarker: string | null = null;
  if (contentLength > 0) {
    let bodyText = "";
    try {
      bodyText = await req.text();
    } catch {
      return json(400, { ok: false, error: "ALERT_DISPATCH_BODY_INVALID" });
    }
    if (new TextEncoder().encode(bodyText).byteLength > MAX_BODY_BYTES) {
      return json(413, { ok: false, error: "ALERT_DISPATCH_BODY_TOO_LARGE" });
    }
    if (bodyText.trim()) {
      let parsed: unknown;
      try {
        parsed = JSON.parse(bodyText);
      } catch {
        return json(400, { ok: false, error: "ALERT_DISPATCH_BODY_INVALID" });
      }
      if (!isObject(parsed)) {
        return json(400, { ok: false, error: "ALERT_DISPATCH_BODY_INVALID" });
      }
      const rawMarker = parsed.controlled_proof_marker;
      if (rawMarker !== undefined && rawMarker !== null) {
        if (rawMarker !== PROOF_MARKER) {
          return json(400, { ok: false, error: "ALERT_PROOF_MARKER_INVALID" });
        }
        proofMarker = PROOF_MARKER;
      }
      const allowedKeys = new Set(["controlled_proof_marker"]);
      if (Object.keys(parsed).some((key) => !allowedKeys.has(key))) {
        return json(400, { ok: false, error: "ALERT_DISPATCH_BODY_FIELD_FORBIDDEN" });
      }
    }
  }

  const baseUrl = Deno.env.get("SUPABASE_URL")?.replace(/\/$/, "") ?? "";
  const credential = backendCredential();
  const telegramToken =
    Deno.env.get("STUDENT_ACCESS_ALERT_TELEGRAM_BOT_TOKEN")?.trim() ?? "";
  const telegramChatId =
    Deno.env.get("STUDENT_ACCESS_ALERT_TELEGRAM_CHAT_ID")?.trim() ?? "";
  if (!baseUrl || credential === null || !telegramToken || !telegramChatId) {
    return json(503, { ok: false, error: "ALERT_DISPATCH_RUNTIME_CONFIG_UNAVAILABLE" });
  }

  const destinationFingerprint = await sha256Hex(
    `fitnexus-alert-destination-v1:${telegramChatId}`,
  );
  const claim = await callRpc(baseUrl, credential, CLAIM_RPC, {
    p_destination_fingerprint: destinationFingerprint,
    p_controlled_proof_marker: proofMarker,
  });
  if (!claim.ok || !isObject(claim.data) || claim.data.ok !== true) {
    return json(503, { ok: false, error: "ALERT_CLAIM_UNAVAILABLE" });
  }
  if (claim.data.claimed !== true) {
    return json(200, { ok: true, delivered: false, reason: "NO_ELIGIBLE_SIGNAL" });
  }

  const claimToken = claim.data.claim_token;
  const attemptNumber = safeInteger(claim.data.attempt_number);
  if (typeof claimToken !== "string" || claimToken.length !== 36 || attemptNumber === null) {
    return json(503, { ok: false, error: "ALERT_CLAIM_RECEIPT_INVALID" });
  }

  const message = buildMessage(claim.data);
  if (message === null) {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "failed",
      null,
      "ALERT_CLAIM_PAYLOAD_INVALID",
    );
    return json(503, { ok: false, error: "ALERT_CLAIM_PAYLOAD_INVALID" });
  }

  let providerResponse: Response;
  try {
    providerResponse = await fetch(
      `${TELEGRAM_BASE_URL}/bot${telegramToken}/sendMessage`,
      {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({
          chat_id: telegramChatId,
          text: message,
          disable_web_page_preview: true,
        }),
      },
    );
  } catch {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "unknown",
      null,
      "TELEGRAM_NETWORK_DELIVERY_UNKNOWN",
    );
    return json(502, { ok: false, error: "ALERT_PROVIDER_DELIVERY_UNKNOWN" });
  }

  let providerData: unknown = null;
  try {
    providerData = await providerResponse.json();
  } catch {
    providerData = null;
  }

  if (providerResponse.status !== 200) {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "failed",
      null,
      "TELEGRAM_HTTP_NON_200",
    );
    return json(502, { ok: false, error: "ALERT_PROVIDER_REJECTED" });
  }
  if (!isObject(providerData) || providerData.ok !== true) {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "failed",
      null,
      "TELEGRAM_RESPONSE_NOT_OK",
    );
    return json(502, { ok: false, error: "ALERT_PROVIDER_REJECTED" });
  }

  const result = providerData.result;
  if (!isObject(result)) {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "unknown",
      null,
      "TELEGRAM_SUCCESS_RECEIPT_INVALID",
    );
    return json(502, { ok: false, error: "ALERT_PROVIDER_RECEIPT_INVALID" });
  }
  const messageId = safeInteger(result.message_id);
  const chat = result.chat;
  if (messageId === null || messageId <= 0 || !isObject(chat) || chat.id === undefined) {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "unknown",
      null,
      "TELEGRAM_SUCCESS_RECEIPT_INVALID",
    );
    return json(502, { ok: false, error: "ALERT_PROVIDER_RECEIPT_INVALID" });
  }
  if (String(chat.id) !== telegramChatId) {
    await recordOutcome(
      baseUrl,
      credential,
      claimToken,
      "unknown",
      null,
      "TELEGRAM_DESTINATION_MISMATCH",
    );
    return json(502, { ok: false, error: "ALERT_PROVIDER_DESTINATION_MISMATCH" });
  }

  const recorded = await recordOutcome(
    baseUrl,
    credential,
    claimToken,
    "delivered",
    messageId,
    null,
  );
  if (!recorded) {
    // Provider delivery succeeded, but durable receipt confirmation did not. Never retry
    // automatically from this response; the pending claim will fail closed to UNKNOWN.
    return json(503, {
      ok: false,
      error: "ALERT_PROVIDER_DELIVERED_RECEIPT_PERSISTENCE_UNCONFIRMED",
    });
  }

  return json(200, {
    ok: true,
    delivered: true,
    provider: PROVIDER,
    signal_id: claim.data.signal_id,
    attempt_number: attemptNumber,
    provider_message_id: messageId,
    controlled_proof_marker: proofMarker ?? false,
  });
});
