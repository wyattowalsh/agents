import type {
  IncomingMessage,
  RequestListener,
  ServerResponse,
} from "node:http";

import { decideIngressRoute } from "../ingress/route-policy.js";

export type LocalControlPlaneMiddleware = (
  request: IncomingMessage,
  response: ServerResponse,
  next: () => void,
) => void;

export type LocalControlPlaneApplication = RequestListener &
  Readonly<{
    use(middleware: LocalControlPlaneMiddleware): unknown;
  }>;

function unavailable(response: ServerResponse): void {
  response.statusCode = 503;
  response.setHeader("cache-control", "no-store");
  response.setHeader("content-length", "0");
  response.end();
}

export function createOwnedLocalThingsInterceptor(
  getListener: () => RequestListener | undefined,
): LocalControlPlaneMiddleware {
  return (request, response, next) => {
    const decision = decideIngressRoute({
      kind: "local-bearer",
      method: request.method,
      target: request.url,
    });
    if (decision.action === "delegate-local-control-plane") {
      next();
      return;
    }
    const listener = getListener();
    if (listener === undefined) {
      unavailable(response);
      return;
    }
    listener(request, response);
  };
}

export function installOwnedLocalThingsInterceptor(
  application: LocalControlPlaneApplication,
  getListener: () => RequestListener | undefined,
): void {
  application.use(createOwnedLocalThingsInterceptor(getListener));
}
