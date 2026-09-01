import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const CHECKOUT_EVENTS = new Set([
  "CHECKOUT_CREATED",
  "CHECKOUT_PAID",
  "CHECKOUT_CANCELED",
  "CHECKOUT_EXPIRED",
]);

const SUBSCRIPTION_EVENTS = new Set([
  "SUBSCRIPTION_CREATED",
  "SUBSCRIPTION_UPDATED",
  "SUBSCRIPTION_INACTIVATED",
  "SUBSCRIPTION_DELETED",
]);

const STATEFUL_PAYMENT_EVENTS = new Set([
  "PAYMENT_CONFIRMED",
  "PAYMENT_RECEIVED",
  "PAYMENT_OVERDUE",
  "PAYMENT_REFUNDED",
  "PAYMENT_CHARGEBACK_REQUESTED",
  "PAYMENT_CREDIT_CARD_CAPTURE_REFUSED",
  "PAYMENT_REPROVED_BY_RISK_ANALYSIS",
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

function optionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
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
  providerSubscriptionRef: string | null,
): Promise<void> {
  await rpc(
    supabaseUrl,
    "mark_billing_webhook_receipt",
    {
      p_provider_code: "asaas",
      p_provider_event_id: providerEventId,
      p_processing_status: processingStatus,
      p_organization_id: organizationId,
      p_provider_subscription_ref: providerSubscriptionRef,
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

  const providerEventId = optionalString(payload.id) ?? "";
  const eventType = (optionalString(payload.event) ?? "").toUpperCase();
  if (!providerEventId || !eventType) {
    return json(400, { ok: false, error: "WEBHOOK_EVENT_ID_AND_TYPE_REQUIRED" });
  }

  const checkout = isObject(payload.checkout) ? payload.checkout : null;
  const subscription = isObject(payload.subscription) ? payload.subscription : null;
  const payment = isObject(payload.payment) ? payload.payment : null;

  const providerCheckoutRef = checkout ? optionalString(checkout.id) : null;
  const checkoutCustomerRef = checkout ? optionalString(checkout.customer) : null;
  const subscriptionRefFromSubscription = subscription
    ? optionalString(subscription.id)
    : null;
  const subscriptionRefFromPayment = payment
    ? optionalString(payment.subscription)
    : null;
  const providerSubscriptionRef = subscriptionRefFromSubscription
    ?? subscriptionRefFromPayment;
  const subscriptionCustomerRef = subscription
    ? optionalString(subscription.customer)
    : null;
  const providerCycle = subscription ? optionalString(subscription.cycle) : null;
  const nextDueDate = subscription ? optionalString(subscription.nextDueDate) : null;
  const paymentDueDate = payment ? optionalString(payment.dueDate) : null;

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
      p_provider_subscription_ref: providerSubscriptionRef,
    },
    serviceHeaders,
  );

  if (!receipt.ok) {
    return json(503, { ok: false, error: "WEBHOOK_RECEIPT_PERSIST_FAILED" });
  }

  let applied: { ok: boolean; status: number; data: unknown } | null = null;
  let resourceRef: string | null = null;

  if (CHECKOUT_EVENTS.has(eventType)) {
    if (!providerCheckoutRef) {
      await markReceipt(
        supabaseUrl,
        serviceHeaders,
        providerEventId,
        "failed",
        null,
        null,
      );
      return json(503, { ok: false, error: "CHECKOUT_ID_REQUIRED", retryable: true });
    }
    resourceRef = providerCheckoutRef;
    applied = await rpc(
      supabaseUrl,
      "apply_billing_checkout_webhook_event",
      {
        p_provider_code: "asaas",
        p_provider_checkout_ref: providerCheckoutRef,
        p_provider_event_id: providerEventId,
        p_event_type: eventType,
        p_payload_sha256: payloadSha256,
        p_effective_at: new Date().toISOString(),
        p_provider_customer_ref: checkoutCustomerRef,
      },
      serviceHeaders,
    );
  } else if (eventType === "SUBSCRIPTION_CREATED") {
    if (!providerSubscriptionRef || !subscriptionCustomerRef || !providerCycle) {
      await markReceipt(
        supabaseUrl,
        serviceHeaders,
        providerEventId,
        "failed",
        null,
        providerSubscriptionRef,
      );
      return json(503, {
        ok: false,
        error: "SUBSCRIPTION_BINDING_FIELDS_REQUIRED",
        retryable: true,
      });
    }
    resourceRef = providerSubscriptionRef;
    applied = await rpc(
      supabaseUrl,
      "bind_billing_provider_subscription",
      {
        p_provider_code: "asaas",
        p_provider_subscription_ref: providerSubscriptionRef,
        p_provider_customer_ref: subscriptionCustomerRef,
        p_provider_event_id: providerEventId,
        p_payload_sha256: payloadSha256,
        p_provider_cycle: providerCycle,
        p_next_due_date: nextDueDate,
      },
      serviceHeaders,
    );
  } else if (SUBSCRIPTION_EVENTS.has(eventType)) {
    if (!providerSubscriptionRef) {
      await markReceipt(
        supabaseUrl,
        serviceHeaders,
        providerEventId,
        "failed",
        null,
        null,
      );
      return json(503, {
        ok: false,
        error: "SUBSCRIPTION_ID_REQUIRED",
        retryable: true,
      });
    }
    resourceRef = providerSubscriptionRef;
    applied = await rpc(
      supabaseUrl,
      "apply_billing_subscription_lifecycle_event",
      {
        p_provider_code: "asaas",
        p_provider_subscription_ref: providerSubscriptionRef,
        p_provider_event_id: providerEventId,
        p_event_type: eventType,
        p_payload_sha256: payloadSha256,
        p_payment_due_date: null,
        p_next_due_date: nextDueDate,
      },
      serviceHeaders,
    );
  } else if (STATEFUL_PAYMENT_EVENTS.has(eventType)) {
    if (!providerSubscriptionRef) {
      // The account may legitimately receive unrelated non-subscription
      // payments through the same webhook endpoint. Persist and ignore them.
      await markReceipt(
        supabaseUrl,
        serviceHeaders,
        providerEventId,
        "ignored",
        null,
        null,
      );
      return json(200, {
        ok: true,
        ignored: true,
        reason: "PAYMENT_NOT_LINKED_TO_SUBSCRIPTION",
        event_id: providerEventId,
        event_type: eventType,
      });
    }
    resourceRef = providerSubscriptionRef;
    applied = await rpc(
      supabaseUrl,
      "apply_billing_subscription_lifecycle_event",
      {
        p_provider_code: "asaas",
        p_provider_subscription_ref: providerSubscriptionRef,
        p_provider_event_id: providerEventId,
        p_event_type: eventType,
        p_payload_sha256: payloadSha256,
        p_payment_due_date: paymentDueDate,
        p_next_due_date: null,
      },
      serviceHeaders,
    );
  } else {
    await markReceipt(
      supabaseUrl,
      serviceHeaders,
      providerEventId,
      "ignored",
      null,
      providerSubscriptionRef,
    );
    return json(200, {
      ok: true,
      ignored: true,
      reason: "EVENT_NOT_REQUIRED_BY_FITNEXUS",
      event_id: providerEventId,
      event_type: eventType,
    });
  }

  if (!applied.ok || !isObject(applied.data)) {
    await markReceipt(
      supabaseUrl,
      serviceHeaders,
      providerEventId,
      "failed",
      null,
      providerSubscriptionRef,
    );
    return json(503, {
      ok: false,
      error: "BILLING_WEBHOOK_RECONCILIATION_FAILED",
      event_type: eventType,
      retryable: true,
    });
  }

  const organizationId = optionalString(applied.data.organization_id);
  const ignored = applied.data.ignored === true;
  await markReceipt(
    supabaseUrl,
    serviceHeaders,
    providerEventId,
    ignored ? "ignored" : "applied",
    organizationId,
    providerSubscriptionRef,
  );

  return json(200, {
    ok: true,
    event_id: providerEventId,
    event_type: eventType,
    resource_ref: resourceRef,
    organization_id: organizationId,
    processing_status: ignored ? "ignored" : "applied",
    idempotency_authority: "provider_event_id",
    browser_callback_can_activate_subscription: false,
    recurring_financial_authority: "provider_webhook",
  });
});
