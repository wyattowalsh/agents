import type { AuthInfo } from "@modelcontextprotocol/server";

import {
  LOCAL_THINGS_CREDENTIAL_CLASS,
  LOCAL_THINGS_RESOURCE,
  REMOTE_THINGS_CREDENTIAL_CLASS,
  REMOTE_THINGS_RESOURCE,
  THINGS_SCOPES,
  type ThingsCredentialClass,
  type ThingsResource,
} from "./constants.js";
import type {
  ProtocolAuthIdentity,
  ThingsScope,
} from "./types.js";

const VALID_SCOPES = new Set<string>(THINGS_SCOPES);

function validIdentityText(value: unknown): value is string {
  return (
    typeof value === "string" &&
    value.length > 0 &&
    value.trim() === value &&
    !/[\u0000-\u001f\u007f]/u.test(value)
  );
}

function resourceIdentity(
  authInfo: AuthInfo,
):
  | {
      readonly resource: ThingsResource;
      readonly credentialClass: ThingsCredentialClass;
    }
  | undefined {
  const resource = authInfo.resource?.href;
  if (resource === LOCAL_THINGS_RESOURCE) {
    return {
      resource,
      credentialClass: LOCAL_THINGS_CREDENTIAL_CLASS,
    };
  }
  if (resource === REMOTE_THINGS_RESOURCE) {
    return {
      resource,
      credentialClass: REMOTE_THINGS_CREDENTIAL_CLASS,
    };
  }
  return undefined;
}

export function protocolAuthIdentity(
  authInfo: AuthInfo | undefined,
): ProtocolAuthIdentity | undefined {
  if (
    authInfo === undefined ||
    !validIdentityText(authInfo.token) ||
    !validIdentityText(authInfo.clientId) ||
    !validIdentityText(authInfo.extra?.principal)
  ) {
    return undefined;
  }
  const resource = resourceIdentity(authInfo);
  if (
    resource === undefined ||
    authInfo.extra?.credentialClass !== resource.credentialClass ||
    authInfo.scopes.length === 0 ||
    new Set(authInfo.scopes).size !== authInfo.scopes.length
  ) {
    return undefined;
  }
  const scopes = new Set<ThingsScope>();
  for (const scope of authInfo.scopes) {
    if (!VALID_SCOPES.has(scope)) {
      return undefined;
    }
    scopes.add(scope as ThingsScope);
  }
  return {
    authInfo,
    principal: authInfo.extra.principal as string,
    clientId: authInfo.clientId,
    resource: resource.resource,
    credentialClass: resource.credentialClass,
    scopes,
  };
}

export function hasExactCatalogScopes(
  identity: ProtocolAuthIdentity,
): boolean {
  return (
    identity.scopes.size === THINGS_SCOPES.length &&
    THINGS_SCOPES.every((scope) => identity.scopes.has(scope))
  );
}

export function methodRequiresCatalogAuthorization(method: unknown): boolean {
  return (
    method === "server/discover" ||
    method === "tools/list" ||
    method === "initialize"
  );
}
