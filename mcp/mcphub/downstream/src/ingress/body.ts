import type { IncomingMessage } from "node:http";

import { IngressSecurityError } from "../security/ingress/request-security.js";

export async function readBoundedBody(
  request: IncomingMessage,
  maximumBytes: number,
): Promise<Uint8Array | undefined> {
  if (!Number.isSafeInteger(maximumBytes) || maximumBytes < 1) {
    throw new IngressSecurityError("body_limit_invalid", 500);
  }
  const contentLength = request.headers["content-length"];
  if (contentLength !== undefined) {
    if (!/^(0|[1-9][0-9]*)$/u.test(contentLength)) {
      throw new IngressSecurityError("content_length_invalid", 400);
    }
    if (Number(contentLength) > maximumBytes) {
      throw new IngressSecurityError("body_too_large", 413);
    }
  }

  const chunks: Buffer[] = [];
  let total = 0;
  for await (const value of request) {
    const chunk = Buffer.isBuffer(value) ? value : Buffer.from(value as Uint8Array);
    total += chunk.byteLength;
    if (total > maximumBytes) {
      throw new IngressSecurityError("body_too_large", 413);
    }
    chunks.push(chunk);
  }
  return total === 0 ? undefined : Buffer.concat(chunks, total);
}
