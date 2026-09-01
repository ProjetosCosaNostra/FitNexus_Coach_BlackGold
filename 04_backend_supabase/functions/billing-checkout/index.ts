import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const CORS_BASE = {
  "access-control-allow-headers": "authorization, x-client-info, apikey, content-type",
  "access-control-allow-methods": "POST, OPTIONS",
  "access-control-max-age": "600",
};

const ALLOWED_BROWSER_ORIGINS = new Set([
  "https://projetoscosanostra.github.io",
  "http://localhost",
  "http://127.0.0.1",
]);

const ALLOWED_PLANS = new Set(["solo", "pro", "studio"]);
const ALLOWED_INTERVALS = new Set(["month", "year"]);
const PLAN_NAMES: Record<string, string> = {
  solo: "FitNexus Coach Solo",
  pro: "FitNexus Coach Pro",
  studio: "FitNexus Studio",
};

type JsonObject = Record<string, unknown>;

type ServiceCredential = {
  apiKey: string;
  authorization?: string;
};

type AsaasEnvironment = {
  baseUrl: string;
  environment: "sandbox" | "production";
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

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function requiredString(payload: JsonObject, key: string): string | null {
  const value = payload[key];
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

function errorCode(data: unknown): string {
  if (!isObject(data)) return "BILLING_BACKEND_REQUEST_FAILED";
  const message = typeof data.message === "string" ? data.message : "";
  if (message) return message;
  const hint = typeof data.hint === "string" ? data.hint : "";
  return hint || "BILLING_BACKEND_REQUEST_FAILED";
}

function asaasEnvironment(): AsaasEnvironment | null {
  const raw = (Deno.env.get("ASAAS_ENVIRONMENT") ?? "sandbox").trim().toLowerCase();
  if (raw === "sandbox") {
    return { baseUrl: "https://api-sandbox.asaas.com/v3", environment: "sandbox" };
  }
  if (raw === "production") {
    return { baseUrl: "https://api.asaas.com/v3", environment: "production" };
  }
  return null;
}

function validAsaasKeyForEnvironment(
  apiKey: string,
  environment: "sandbox" | "production",
): boolean {
  return environment === "production"
    ? apiKey.startsWith("$aact_prod_")
    : apiKey.startsWith("$aact_hmlg_");
}

function callbackBaseUrl(): string | null {
  const raw = Deno.env.get("FITNEXUS_BILLING_CALLBACK_BASE_URL")?.trim();
  if (!raw) return null;
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:") return null;
    return url.toString().replace(/\/$/, "");
  } catch {
    return null;
  }
}

function asAsaasDateTime(value: Date): string {
  const pad = (number: number) => String(number).padStart(2, "0");
  return `${value.getUTCFullYear()}-${pad(value.getUTCMonth() + 1)}-${pad(value.getUTCDate())} ${pad(value.getUTCHours())}:${pad(value.getUTCMinutes())}:${pad(value.getUTCSeconds())}`;
}

function addCalendarMonthsUtc(source: Date, months: number): Date {
  const result = new Date(source.getTime());
  const originalDay = result.getUTCDate();
  result.setUTCDate(1);
  result.setUTCMonth(result.getUTCMonth() + months);
  const lastDay = new Date(Date.UTC(
    result.getUTCFullYear(),
    result.getUTCMonth() + 1,
    0,
  )).getUTCDate();
  result.setUTCDate(Math.min(originalDay, lastDay));
  return result;
}

function resolveHostedCheckoutUrl(
  data: JsonObject,
  checkoutId: string,
  environment: "sandbox" | "production",
): string | null {
  const rawLink = typeof data.link === "string" ? data.link.trim() : "";
  if (rawLink) {
    try {
      const parsed = new URL(rawLink);
      const trustedHost = parsed.hostname === "asaas.com"
        || parsed.hostname.endsWith(".asaas.com");
      if (parsed.protocol === "https:" && trustedHost) {
        return parsed.toString();
      }
    } catch {
      return null;
    }
  }

  const encodedId = encodeURIComponent(checkoutId);
  return environment === "sandbox"
    ? `https://sandbox.asaas.com/checkoutSession/show/${encodedId}`
    : `https://asaas.com/checkoutSession/show?id=${encodedId}`;
}

async function handlePost(req: Request): Promise<Response> {
  const authorization = req.headers.get("authorization")?.trim() ?? "";
  if (!authorization.toLowerCase().startsWith("bearer ")) {
    return json(req, 401, { ok: false, error: "AUTH_REQUIRED" });
  }

  const contentLength = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > 4_096) {
    return json(req, 413, { ok: false, error: "REQUEST_TOO_LARGE" });
  }

  let payload: unknown;
  try {
    payload = await req.json();
  } catch {
    return json(req, 400, { ok: false, error: "INVALID_JSON" });
  }
  if (!isObject(payload)) {
    return json(req, 400, { ok: false, error: "INVALID_REQUEST" });
  }

  const organizationId = requiredString(payload, "organization_id");
  const planCode = requiredString(payload, "plan_code");
  const billingInterval = requiredString(payload, "billing_interval");
  if (!organizationId || !planCode || !billingInterval) {
    return json(req, 400, { ok: false, error: "CHECKOUT_FIELDS_REQUIRED" });
  }
  if (!/^[0-9a-fA-F-]{36}$/.test(organizationId)) {
    return json(req, 400, { ok: false, error: "INVALID_ORGANIZATION_ID" });
  }
  if (!ALLOWED_PLANS.has(planCode)) {
    return json(req, 400, { ok: false, error: "INVALID_PLAN_CODE" });
  }
  if (!ALLOWED_INTERVALS.has(billingInterval)) {
    return json(req, 400, { ok: false, error: "INVALID_BILLING_INTERVAL" });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL")?.trim();
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY")?.trim();
  const service = serviceCredential();
  if (!supabaseUrl || !anonKey || !service) {
    return json(req, 503, { ok: false, error: "BILLING_SERVER_AUTHORITY_UNAVAILABLE" });
  }

  const intentResult = await rpc(
    supabaseUrl,
    "create_billing_checkout_intent",
    {
      p_organization_id: organizationId,
      p_plan_code: planCode,
      p_billing_interval: billingInterval,
    },
    { apikey: anonKey, authorization },
  );

  if (!intentResult.ok || !isObject(intentResult.data)) {
    return json(req, intentResult.status === 0 ? 503 : Math.max(intentResult.status, 400), {
      ok: false,
      error: errorCode(intentResult.data),
    });
  }

  const intent = intentResult.data;
  const checkoutIntentId = typeof intent.checkout_intent_id === "string"
    ? intent.checkout_intent_id
    : null;
  const providerCode = typeof intent.provider_code === "string" ? intent.provider_code : null;
  const amountMinor = typeof intent.amount_minor === "number"
    ? Math.trunc(intent.amount_minor)
    : null;
  const existingCheckoutUrl = typeof intent.checkout_url === "string"
    ? intent.checkout_url
    : null;

  if (!checkoutIntentId || providerCode !== "asaas") {
    return json(req, 409, { ok: false, error: "BILLING_PROVIDER_AUTHORITY_INVALID" });
  }
  if (existingCheckoutUrl?.startsWith("https://")) {
    return json(req, 200, {
      ok: true,
      checkout_intent_id: checkoutIntentId,
      provider_code: providerCode,
      plan_code: planCode,
      billing_interval: billingInterval,
      checkout_url: existingCheckoutUrl,
      idempotent_replay: true,
    });
  }
  if (!amountMinor || amountMinor <= 0) {
    return json(req, 409, { ok: false, error: "SERVER_PRICE_AUTHORITY_MISSING" });
  }

  const environment = asaasEnvironment();
  const asaasApiKey = Deno.env.get("ASAAS_API_KEY")?.trim();
  const callbackBase = callbackBaseUrl();
  if (!environment || !asaasApiKey || !callbackBase) {
    return json(req, 503, {
      ok: false,
      error: "BILLING_PROVIDER_EXTERNAL_CREDENTIAL_PENDING",
    });
  }
  if (!validAsaasKeyForEnvironment(asaasApiKey, environment.environment)) {
    return json(req, 503, {
      ok: false,
      error: "ASAAS_ENVIRONMENT_CREDENTIAL_MISMATCH",
    });
  }

  const nextDueDate = addCalendarMonthsUtc(
    new Date(),
    billingInterval === "year" ? 12 : 1,
  );
  const cycle = billingInterval === "year" ? "YEARLY" : "MONTHLY";
  const planName = PLAN_NAMES[planCode] ?? `FitNexus ${planCode}`;

  const asaasPayload = {
    billingTypes: ["CREDIT_CARD"],
    chargeTypes: ["RECURRENT"],
    minutesToExpire: 60,
    externalReference: checkoutIntentId,
    callback: {
      successUrl: `${callbackBase}/billing/success`,
      cancelUrl: `${callbackBase}/billing/canceled`,
      expiredUrl: `${callbackBase}/billing/expired`,
    },
    items: [
      {
        externalReference: `${planCode}:${billingInterval}`,
        name: planName,
        description: billingInterval === "year"
          ? "Assinatura anual FitNexus Coach BlackGold"
          : "Assinatura mensal FitNexus Coach BlackGold",
        quantity: 1,
        value: Number((amountMinor / 100).toFixed(2)),
      },
    ],
    subscription: {
      cycle,
      nextDueDate: asAsaasDateTime(nextDueDate),
    },
  };

  let asaasResponse: Response;
  try {
    asaasResponse = await fetch(`${environment.baseUrl}/checkouts`, {
      method: "POST",
      headers: {
        accept: "application/json",
        "content-type": "application/json",
        "user-agent": `FitNexus/0.9 billing-checkout (${environment.environment})`,
        access_token: asaasApiKey,
      },
      body: JSON.stringify(asaasPayload),
    });
  } catch {
    return json(req, 503, { ok: false, error: "ASAAS_CHECKOUT_NETWORK_FAILURE" });
  }

  let asaasData: unknown = null;
  try {
    asaasData = await asaasResponse.json();
  } catch {
    asaasData = null;
  }

  if (!asaasResponse.ok || !isObject(asaasData)) {
    return json(req, asaasResponse.status >= 400 ? asaasResponse.status : 502, {
      ok: false,
      error: "ASAAS_CHECKOUT_CREATE_FAILED",
    });
  }

  const providerCheckoutRef = typeof asaasData.id === "string" ? asaasData.id.trim() : "";
  if (!providerCheckoutRef) {
    return json(req, 502, { ok: false, error: "ASAAS_CHECKOUT_RESPONSE_INVALID" });
  }
  const checkoutUrl = resolveHostedCheckoutUrl(
    asaasData,
    providerCheckoutRef,
    environment.environment,
  );
  if (!checkoutUrl) {
    return json(req, 502, { ok: false, error: "ASAAS_CHECKOUT_LINK_INVALID" });
  }

  const serviceHeaders: Record<string, string> = { apikey: service.apiKey };
  if (service.authorization) serviceHeaders.authorization = service.authorization;
  const expiresAt = new Date(Date.now() + 60 * 60 * 1000).toISOString();
  const attachResult = await rpc(
    supabaseUrl,
    "attach_billing_provider_checkout",
    {
      p_checkout_intent_id: checkoutIntentId,
      p_provider_checkout_ref: providerCheckoutRef,
      p_checkout_url: checkoutUrl,
      p_expires_at: expiresAt,
    },
    serviceHeaders,
  );

  if (!attachResult.ok) {
    return json(req, attachResult.status === 0 ? 503 : Math.max(attachResult.status, 400), {
      ok: false,
      error: errorCode(attachResult.data),
    });
  }

  return json(req, 200, {
    ok: true,
    checkout_intent_id: checkoutIntentId,
    provider_code: providerCode,
    plan_code: planCode,
    billing_interval: billingInterval,
    checkout_url: checkoutUrl,
    environment: environment.environment,
    idempotent_replay: false,
    payment_confirmation_authority: "webhook",
  });
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders(req) });
  }
  if (req.method !== "POST") {
    return json(req, 405, { ok: false, error: "METHOD_NOT_ALLOWED" });
  }
  return await handlePost(req);
});
