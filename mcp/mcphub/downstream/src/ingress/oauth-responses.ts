import { THINGS_ISSUER } from "../policy/oauth-policy.js";

type AuthorizationRedirectPayload =
  | Readonly<{ code: string; state: string }>
  | Readonly<{ error: string; state?: string }>;

function bounded(value: string): boolean {
  return value.length > 0 && value.length <= 2_048 && !/[\u0000-\u001f\u007f]/u.test(value);
}

/** The sole RFC 9207 authorization response serializer. */
export function issuerBoundAuthorizationRedirect(
  approvedRedirectUri: string,
  payload: AuthorizationRedirectPayload,
): URL {
  const target = new URL(approvedRedirectUri);
  if (target.protocol !== "https:" || target.username !== "" || target.password !== "") {
    throw new Error("authorization_redirect_invalid");
  }
  target.hash = "";
  target.search = "";
  target.searchParams.set("iss", THINGS_ISSUER);
  if ("code" in payload) {
    if (!bounded(payload.code) || !bounded(payload.state)) {
      throw new Error("authorization_response_invalid");
    }
    target.searchParams.set("code", payload.code);
    target.searchParams.set("state", payload.state);
  } else {
    if (!bounded(payload.error)) throw new Error("authorization_response_invalid");
    target.searchParams.set("error", payload.error);
    if (payload.state !== undefined) {
      if (!bounded(payload.state)) throw new Error("authorization_response_invalid");
      target.searchParams.set("state", payload.state);
    }
  }
  return target;
}

