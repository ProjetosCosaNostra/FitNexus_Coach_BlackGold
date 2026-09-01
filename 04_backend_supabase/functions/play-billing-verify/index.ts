import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const JSON_HEADERS = {
  "content-type": "application/json; charset=utf-8",
  "cache-control": "no-store",
};

const PACKAGE_NAME = "br.com.lafamigliaplayworks.fitnexuscoach";
const PRODUCT_IDS = new Set([
  "fitnexus_solo",
  "fitnexus_pro",
  "fitnexus_studio",
]);
const ANDROID_PUBLISHER_SCOPE = "https://www.googleapis.com/auth/androidpublisher";

type JsonObject = Record<string, unknown>;

type ServiceCredential = {
  apiKey: string;
  authorization?: string;
};

type GoogleServiceAccount = {
  client_email: string;
  private_key: string;
  token_uri?: string;
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

function requiredString(value: unknown): string | null {
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
  if (!legacy) return null;
  return { apiKey: legacy, authorization: `Bearer ${legacy}` };
}

function base64Url(bytes: Uint8Array): string {
  let binary = "";
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary)
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
}

function base64UrlJson(value: unknown): string {
  return base64Url(new TextEncoder().encode(JSON.stringify(value)));
}

function pemToBytes(pem: string): Uint8Array {
  const normalized = pem
    .replace("-----BEGIN PRIVATE KEY-----", "")
    .replace("-----END PRIVATE KEY-----", "")
    .replace(/\s+/g, "");
  const binary = atob(normalized);
  const bytes = new Uint8Array(binary.length);
  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }
  return bytes;
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

function serviceAccount(): GoogleServiceAccount | null {
  const raw = Deno.env.get("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")?.trim();
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Record<string, unknown>;
    const clientEmail = requiredString(value.client_email);
    const privateKey = requiredString(value.private_key);
    const tokenUri = requiredString(value.token_uri) ?? "https://oauth2.googleapis.com/token";
    if (!clientEmail || !privateKey || !tokenUri.startsWith("https://")) return null;
    return {
      client_email: clientEmail,
      private_key: privateKey,
      token_uri: tokenUri,
    };
  } catch {
    return null;
  }
}

async function googleAccessToken(account: GoogleServiceAccount): Promise<string | null> {
  const now = Math.floor(Date.now() / 1000);
  const tokenUri = account.token_uri ?? "https://oauth2.googleapis.com/token";
  const encodedHeader = base64UrlJson({ alg: "RS256", typ: "JWT" });
  const encodedClaims = base64UrlJson({
    iss: account.client_email,
    scope: ANDROID_PUBLISHER_SCOPE,
    aud: tokenUri,
    iat: now,
    exp: now + 3600,
  });
  const signingInput = `${encodedHeader}.${encodedClaims}`;

  const privateKeyBytes = pemToBytes(account.private_key);
  const keyBuffer = new Uint8Array(privateKeyBytes.byteLength);
  keyBuffer.set(privateKeyBytes);
  const key = await crypto.subtle.importKey(
    "pkcs8",
    keyBuffer.buffer,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const inputBytes = new TextEncoder().encode(signingInput);
  const inputBuffer = new Uint8Array(inputBytes.byteLength);
  inputBuffer.set(inputBytes);
  const signature = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    key,
    inputBuffer.buffer,
  );
  const assertion = `${signingInput}.${base64Url(new Uint8Array(signature))}`;

  const response = await fetch(tokenUri, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion,
    }),
  });
  if (!response.ok) return null;
  const body: unknown = await response.json();
  if (!isObject(body)) return null;
  return requiredString(body.access_token);
}

async function authenticatedUserId(req: Request, supabaseUrl: string): Promise<string | null> {
  const authorization = req.headers.get("authorization")?.trim() ?? "";
  const anonKey = Deno.env.get("SUPABASE_ANON_KEY")?.trim();
  if (!authorization.toLowerCase().startsWith("bearer ") || !anonKey) return null;
  try {
    const response = await fetch(`${supabaseUrl}/auth/v1/user`, {
      headers: {
        authorization,
        apikey: anonKey,
      },
    });
    if (!response.ok) return null;
    const body: unknown = await response.json();
    return isObject(body) ? requiredString(body.id) : null;
  } catch {
    return null;
  }
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

function latestExpiry(lineItems: unknown[]): string | null {
  let latest: Date | null = null;
  for (const raw of lineItems) {
    if (!isObject(raw)) continue;
    const expiry = requiredString(raw.expiryTime);
    if (!expiry) continue;
    const parsed = new Date(expiry);
    if (Number.isNaN(parsed.getTime())) continue;
    if (latest == null || parsed > latest) latest = parsed;
  }
  return latest?.toISOString() ?? null;
}

function hasAutoRenewingPlan(lineItems: unknown[]): boolean {
  return lineItems.some((raw) => isObject(raw) && isObject(raw.autoRenewingPlan));
}

Deno.serve(async (req: Request): Promise<Response> => {
  if (req.method !== "POST") {
    return json(405, { ok: false, error: "METHOD_NOT_ALLOWED" });
  }

  const contentLength = Number(req.headers.get("content-length") ?? "0");
  if (Number.isFinite(contentLength) && contentLength > 16_384) {
    return json(413, { ok: false, error: "REQUEST_TOO_LARGE" });
  }

  let payload: unknown;
  try {
    payload = await req.json();
  } catch {
    return json(400, { ok: false, error: "INVALID_JSON" });
  }
  if (!isObject(payload)) return json(400, { ok: false, error: "INVALID_REQUEST" });

  const organizationId = requiredString(payload.organization_id);
  const packageName = requiredString(payload.package_name);
  const productId = requiredString(payload.product_id);
  const purchaseToken = requiredString(payload.purchase_token);
  const purchaseId = requiredString(payload.purchase_id);

  if (!organizationId || !packageName || !productId || !purchaseToken) {
    return json(400, { ok: false, error: "PLAY_VERIFICATION_FIELDS_REQUIRED" });
  }
  if (packageName !== PACKAGE_NAME) {
    return json(400, { ok: false, error: "PLAY_PACKAGE_NAME_INVALID" });
  }
  if (!PRODUCT_IDS.has(productId)) {
    return json(400, { ok: false, error: "PLAY_PRODUCT_ID_INVALID" });
  }
  if (purchaseToken.length < 16 || purchaseToken.length > 4096) {
    return json(400, { ok: false, error: "PLAY_PURCHASE_TOKEN_INVALID" });
  }

  const supabaseUrl = Deno.env.get("SUPABASE_URL")?.trim();
  const service = serviceCredential();
  const googleAccount = serviceAccount();
  if (!supabaseUrl || !service) {
    return json(503, { ok: false, error: "PLAY_SERVER_AUTHORITY_UNAVAILABLE" });
  }
  if (!googleAccount) {
    return json(503, {
      ok: false,
      error: "GOOGLE_PLAY_SERVICE_ACCOUNT_PENDING",
      entitlement_active: false,
    });
  }

  const userId = await authenticatedUserId(req, supabaseUrl);
  if (!userId) return json(401, { ok: false, error: "AUTH_REQUIRED" });

  let accessToken: string | null = null;
  try {
    accessToken = await googleAccessToken(googleAccount);
  } catch {
    accessToken = null;
  }
  if (!accessToken) {
    return json(503, { ok: false, error: "GOOGLE_PLAY_OAUTH_FAILED" });
  }

  const verificationUrl =
    `https://androidpublisher.googleapis.com/androidpublisher/v3/applications/${encodeURIComponent(packageName)}`
    + `/purchases/subscriptionsv2/tokens/${encodeURIComponent(purchaseToken)}`;

  let playResponse: Response;
  try {
    playResponse = await fetch(verificationUrl, {
      headers: {
        authorization: `Bearer ${accessToken}`,
        accept: "application/json",
      },
    });
  } catch {
    return json(503, { ok: false, error: "GOOGLE_PLAY_API_NETWORK_FAILURE" });
  }

  const rawResponse = await playResponse.text();
  let playData: unknown = null;
  try {
    playData = JSON.parse(rawResponse);
  } catch {
    playData = null;
  }
  if (!playResponse.ok || !isObject(playData)) {
    return json(playResponse.status === 404 ? 400 : 503, {
      ok: false,
      error: playResponse.status === 404
        ? "GOOGLE_PLAY_PURCHASE_NOT_FOUND"
        : "GOOGLE_PLAY_API_VERIFICATION_FAILED",
    });
  }

  const lineItems = Array.isArray(playData.lineItems)
    ? playData.lineItems as unknown[]
    : <unknown>[];
  if (lineItems.length === 0) {
    return json(400, { ok: false, error: "GOOGLE_PLAY_SUBSCRIPTION_LINE_ITEMS_MISSING" });
  }
  const productMatch = lineItems.some(
    (raw) => isObject(raw) && requiredString(raw.productId) === productId,
  );
  if (!productMatch) {
    return json(409, { ok: false, error: "GOOGLE_PLAY_PRODUCT_TOKEN_MISMATCH" });
  }

  const externalAccountIdentifiers = isObject(playData.externalAccountIdentifiers)
    ? playData.externalAccountIdentifiers
    : null;
  const playAccountId = externalAccountIdentifiers
    ? requiredString(externalAccountIdentifiers.obfuscatedExternalAccountId)
    : null;
  if (!playAccountId || playAccountId !== userId) {
    return json(409, { ok: false, error: "GOOGLE_PLAY_ACCOUNT_BINDING_MISMATCH" });
  }

  const subscriptionState = requiredString(playData.subscriptionState);
  const expiryTime = latestExpiry(lineItems);
  const startTime = requiredString(playData.startTime);
  if (!subscriptionState || !expiryTime) {
    return json(400, { ok: false, error: "GOOGLE_PLAY_SUBSCRIPTION_STATE_INCOMPLETE" });
  }

  const tokenHash = await sha256Hex(purchaseToken);
  const responseHash = await sha256Hex(rawResponse);
  const serviceHeaders: Record<string, string> = { apikey: service.apiKey };
  if (service.authorization) serviceHeaders.authorization = service.authorization;

  const applied = await rpc(
    supabaseUrl,
    "apply_google_play_subscription_verification",
    {
      p_organization_id: organizationId,
      p_user_id: userId,
      p_product_id: productId,
      p_purchase_token_sha256: tokenHash,
      p_purchase_id: purchaseId,
      p_subscription_state: subscriptionState,
      p_start_time: startTime,
      p_expiry_time: expiryTime,
      p_auto_renewing: hasAutoRenewingPlan(lineItems),
      p_raw_response_sha256: responseHash,
    },
    serviceHeaders,
  );

  if (!applied.ok || !isObject(applied.data)) {
    return json(503, {
      ok: false,
      error: "GOOGLE_PLAY_ENTITLEMENT_APPLY_FAILED",
    });
  }

  return json(200, {
    ok: true,
    product_id: productId,
    subscription_state: subscriptionState,
    entitlement_active: applied.data.entitlement_active === true,
    status: applied.data.status ?? null,
    expiry_time: applied.data.expiry_time ?? expiryTime,
    verification_authority: "google_play_developer_api",
    raw_purchase_token_returned: false,
  });
});
