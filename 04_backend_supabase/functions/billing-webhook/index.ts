import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const SUPPORTED_CHECKOUT_EVENTS = new Set([
  "CHECKOUT_CREATED",
  "CHECKOUT_PAID",
  "CHECKOUT_CANCELED",
  "CHECKOUT_EXPIRED",
]);

type JsonObject = Record<string, unknown>;

type ServiceCredential = {
  apiKey: string;
  authorization?: string;
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

function serviceCredential(): ServiceCredential | null {
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

  const legacy = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")?.trim();
  if (legacy) {
    return {
      apiKey: legacy,
      authorization: `Bearer ${legacy}`,
    };
  }

  return null;
}

function secureEqual(left: string, right: string): boolean {
  const encoder = new TextEncoder();
  const leftBytes = encoder.encode(left);
  const rightBytes = encoder.encode(right);
  if (leftBytes.length !== rightBytes.length) return false;
  let mismatch = 0;
  for (let index = 0; index < leftBytes.length; index += 1) {
    mismatch |= leftBytes[index] ^ rightBytes[index];
  }
  return mismatch === 0;
}

async function sha256Hex(bytes: Uint8Array): Promise<string> {
  // Deno 2.9's WebCrypto typings require an ArrayBuffer-backed view rather
  // than Uint8Array<ArrayBufferLike>. Copying is intentional and bounded by
  // the webhook payload limit below.
  const digestInput = new Uint8Array(bytes.byteLength);
  digestInput.set(bytes);
  const digest = await crypto.subtle.digest("SHA-256", digestInput.buffer);
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

async function rpc(
  baseUrl: string,
  rpcName: string,
  params: JsonObject,
  headers: Record<string, string>,
): Promise<{ ok: boolean; status: number; data: unknown }> {
  try {
    const response = await fetch(`${baseUrl}/rest/v1/rpc/${rpcName}`, {
      method: "POST",
      headers: {
        ...headers,
        "content-type": "application/json",
        accept: "application/json",
      },
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

async function markReceipt(
  supabaseUrl: string,
  headers: Record<string, string>,
  providerEventId: string,
  processingStatus: "applied" | "ignored" | "failed",
  organizationId: string | null,
): Promise<void> {
  await rpc(
    supabaseUrl,
    "mark_billing_webhook_receipt",
    {
      p_provider_code: "asaas",
      p_provider_event_id: providerEventId,
      p_processing_status: processingStatus,
      p_organization_id: organizationId,
      p_provider_subscription_ref: null,
    },
    headers,
  );
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return json(405, { ok: false, error: "METHOD_NOT_ALLOWED" });
  }

  const expectedToken = Deno.env.get("ASAAS_WEBHOOK_AUTH_TOKEN")?.trim() ?? "";
  const receivedToken = req.headers.get("asaas-access-token")?.trim() ?? "";
  if (expectedToken.length < 32 || !secureEqual(expectedToken, receivedToken)) {
    return json(401, { ok: false, error: "WEBHOOK_AUTH_INVALID" });
  }

  const contentLength = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > 262_144) {
    return json(413, { ok: false, error: "WEBHOOK_PAYLOAD_TOO_LARGE" });
  }

  let rawBytes: Uint8Array;
  try {
    rawBytes = new Uint8Array(await req.arrayBuffer());
  } catch {
    return json(400, { ok: false, error: "WEBHOOK_BODY_READ_FAILED" });
  }
  if (rawBytes.length === 0 || rawBytes.length > 262_144) {
    return json(rawBytes.length === 0 ? 400 : 413, {
      ok: false,
      error: rawBytes.length === 0 ? "WEBHOOK_BODY_EMPTY" : "WEBHOOK_PAYLOAD_TOO_LARGE",
    });
  }

  let payload: unknown;
  try {
    payload = JSON.parse(new TextDecoder().decode(rawBytes));
  } catch {
    return json(400, { ok: false, error: "INVALID_JSON" });
  }
  if (!isObject(payload)) {
    return json(400, { ok: false, error: "INVALID_WEBHOOK_PAYLOAD" });
  }

  const providerEventId = typeof payload.id === "string" ? payload.id.trim() : "";
  const eventType = typeof payload.event === "string" ? payload.event.trim() : "";
  const checkout = isObject(payload.checkout) ? payload.checkout : null;
  const providerCheckoutRef = checkout && typeof checkout.id === "string"
    ? checkout.id.trim()
    : "";
  const providerCustomerRef = checkout && typeof checkout.customer === "string"
    ? checkout.customer.trim()
    : null;

  if (!providerEventId || !eventType) {
    return json(400, { ok: false, error: "WEBHOOK_EVENT_ID_AND_TYPE_REQUIRED" });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL")?.trim();
  const service = serviceCredential();
  if (!supabaseUrl || !service) {
    return json(503, { ok: false, error: "BILLING_SERVER_AUTHORITY_UNAVAILABLE" });
  }
  const serviceHeaders: Record<string, string> = { apikey: service.apiKey };
  if (service.authorization) serviceHeaders.authorization = service.authorization;

  const payloadSha256 = await sha256Hex(rawBytes);
  const receipt = await rpc(
    supabaseUrl,
    "record_billing_webhook_receipt",
    {
      p_provider_code: "asaas",
      p_provider_event_id: providerEventId,
      p_event_type: eventType,
      p_payload_sha256: payloadSha256,
      p_auth_verified: true,
      p_organization_id: null,
      p_provider_subscription_ref: null,
    },
    serviceHeaders,
  );

  if (!receipt.ok) {
    return json(503, { ok: false, error: "WEBHOOK_RECEIPT_PERSIST_FAILED" });
  }

  // Unknown future events are persisted and ignored. This prevents schema
  // additions by the provider from interrupting the webhook queue.
  if (!SUPPORTED_CHECKOUT_EVENTS.has(eventType)) {
    await markReceipt(
      supabaseUrl,
      serviceHeaders,
      providerEventId,
      "ignored",
      null,
    );
    return json(200, {
      ok: true,
      ignored: true,
      event_id: providerEventId,
      event_type: eventType,
    });
  }

  if (!providerCheckoutRef) {
    await markReceipt(
      supabaseUrl,
      serviceHeaders,
      providerEventId,
      "failed",
      null,
    );
    return json(400, { ok: false, error: "CHECKOUT_ID_REQUIRED" });
  }

  const applied = await rpc(
    supabaseUrl,
    "apply_billing_checkout_webhook_event",
    {
      p_provider_code: "asaas",
      p_provider_checkout_ref: providerCheckoutRef,
      p_provider_event_id: providerEventId,
      p_event_type: eventType,
      p_payload_sha256: payloadSha256,
      p_effective_at: new Date().toISOString(),
      p_provider_customer_ref: providerCustomerRef,
    },
    serviceHeaders,
  );

  if (!applied.ok || !isObject(applied.data)) {
    await markReceipt(
      supabaseUrl,
      serviceHeaders,
      providerEventId,
      "failed",
      null,
    );
    // Non-2xx intentionally asks Asaas to retry. The receipt makes the retry
    // idempotent and auditable.
    return json(503, {
      ok: false,
      error: "CHECKOUT_WEBHOOK_RECONCILIATION_FAILED",
      retryable: true,
    });
  }

  const organizationId = typeof applied.data.organization_id === "string"
    ? applied.data.organization_id
    : null;
  const ignored = applied.data.ignored === true;
  await markReceipt(
    supabaseUrl,
    serviceHeaders,
    providerEventId,
    ignored ? "ignored" : "applied",
    organizationId,
  );

  return json(200, {
    ok: true,
    event_id: providerEventId,
    event_type: eventType,
    checkout_id: providerCheckoutRef,
    organization_id: organizationId,
    processing_status: ignored ? "ignored" : "applied",
    idempotency_authority: "provider_event_id",
    browser_callback_can_activate_subscription: false,
  });
});
