import assert from "node:assert/strict";
import test from "node:test";

import type { IncomingMessage } from "node:http";

import {
  acceptedSocketIdentity,
  extractSingleBearer,
  IngressSecurityError,
  rejectForwardingHeaders,
  requireExactBearer,
} from "../../src/security/ingress/request-security.js";

function request(localPort: number, remoteAddress = "127.0.0.1"): IncomingMessage {
  return {
    socket: {
      localAddress: "127.0.0.1",
      localPort,
      remoteAddress,
    },
  } as unknown as IncomingMessage;
}

test("extracts one strict bearer value", () => {
  assert.equal(extractSingleBearer(["Authorization", "Bearer opaque-token"]), "opaque-token");
});

test("rejects an absent bearer", () => {
  assert.throws(() => extractSingleBearer([]), IngressSecurityError);
});

test("rejects duplicate authorization fields", () => {
  assert.throws(
    () => extractSingleBearer(["Authorization", "Bearer a", "authorization", "Bearer b"]),
    IngressSecurityError,
  );
});

test("rejects comma-folded authorization credentials", () => {
  assert.throws(
    () => extractSingleBearer(["Authorization", "Bearer a, Bearer b"]),
    IngressSecurityError,
  );
});

test("compares an exact configured bearer", () => {
  assert.doesNotThrow(() => requireExactBearer("opaque", "opaque"));
});

test("rejects wrong and placeholder configured bearers", () => {
  assert.throws(() => requireExactBearer("opaque", "wrong"), IngressSecurityError);
  assert.throws(
    () => requireExactBearer("opaque", "replace-with-local-bearer-token"),
    IngressSecurityError,
  );
});

test("rejects caller-controlled forwarding identity headers", () => {
  assert.throws(
    () => rejectForwardingHeaders(["X-Forwarded-Port", "46683"]),
    IngressSecurityError,
  );
});

test("accepts unrelated ordinary headers", () => {
  assert.doesNotThrow(() => rejectForwardingHeaders(["Content-Type", "application/json"]));
});

test("derives local and remote credential classes only from accepted sockets", () => {
  assert.equal(acceptedSocketIdentity(request(46683), "local-bearer").listenerId, "local-bearer-46683");
  assert.equal(acceptedSocketIdentity(request(46684), "remote-oauth").listenerId, "oauth-loopback-46684");
});

test("rejects listener-port and peer-address substitution", () => {
  assert.throws(() => acceptedSocketIdentity(request(46684), "local-bearer"), IngressSecurityError);
  assert.throws(
    () => acceptedSocketIdentity(request(46684, "203.0.113.2"), "remote-oauth"),
    IngressSecurityError,
  );
});

