import type { AuthInfo } from "@modelcontextprotocol/server";

import type { ThingsOAuthService } from "../../oauth/service.js";
import { OFFLINE_ACCESS_SCOPE } from "../../policy/oauth-policy.js";
import {
  LOCAL_THINGS_CREDENTIAL_CLASS,
  LOCAL_THINGS_RESOURCE,
  REMOTE_THINGS_CREDENTIAL_CLASS,
  REMOTE_THINGS_RESOURCE,
  THINGS_SCOPES,
} from "../../protocol/constants.js";
import {
  extractSingleBearer,
  requireExactBearer,
} from "./request-security.js";

export function localBearerAuthInfo(
  rawHeaders: readonly string[],
  expectedToken: string,
): AuthInfo {
  const token = extractSingleBearer(rawHeaders);
  requireExactBearer(token, expectedToken);
  return {
    token,
    clientId: "mcphub-local-control-plane",
    scopes: [...THINGS_SCOPES],
    resource: new URL(LOCAL_THINGS_RESOURCE),
    extra: {
      credentialClass: LOCAL_THINGS_CREDENTIAL_CLASS,
      principal: "local:loopback-bearer",
    },
  };
}

export function remoteOAuthAuthInfo(
  rawHeaders: readonly string[],
  oauthService: ThingsOAuthService,
): AuthInfo {
  const token = extractSingleBearer(rawHeaders);
  const claims = oauthService.authorizeCatalog(token, REMOTE_THINGS_RESOURCE);
  const thingsScopes = claims.scopes.filter(
    (scope): scope is (typeof THINGS_SCOPES)[number] => scope !== OFFLINE_ACCESS_SCOPE,
  );
  return {
    token,
    clientId: claims.clientId,
    scopes: thingsScopes,
    resource: new URL(REMOTE_THINGS_RESOURCE),
    extra: {
      credentialClass: REMOTE_THINGS_CREDENTIAL_CLASS,
      principal: `sha256:${claims.principalHash}`,
    },
  };
}
