import { readdir, readFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { afterEach, describe, expect, it, vi } from "vitest";

const PROTOCOL_SOURCE = join(
  dirname(fileURLToPath(import.meta.url)),
  "../../src/protocol",
);

describe("public SDK isolation", () => {
  afterEach(() => {
    vi.doUnmock("@modelcontextprotocol/sdk");
    vi.resetModules();
  });

  it("imports only @modelcontextprotocol/server from the public protocol lane", async () => {
    const files = (await readdir(PROTOCOL_SOURCE))
      .filter((name) => name.endsWith(".ts"))
      .sort();
    const sources = await Promise.all(
      files.map(async (name) => ({
        name,
        source: await readFile(join(PROTOCOL_SOURCE, name), "utf8"),
      })),
    );
    const privateImports = sources.filter(({ source }) =>
      source.includes("@modelcontextprotocol/sdk"),
    );
    const publicImports = sources
      .flatMap(({ source }) =>
        [...source.matchAll(/from\s+["'](@modelcontextprotocol\/[^"']+)["']/gu)].map(
          (match) => match[1],
        ),
      )
      .filter((value): value is string => value !== undefined);

    expect(privateImports).toEqual([]);
    expect(new Set(publicImports)).toEqual(
      new Set(["@modelcontextprotocol/server"]),
    );
  });

  it("does not resolve the private v1 SDK while loading the public protocol lane", async () => {
    const v1Factory = vi.fn(() => {
      throw new Error("private_v1_sdk_loaded_by_public_protocol");
    });
    vi.doMock("@modelcontextprotocol/sdk", v1Factory);

    const protocol = await import("../../src/protocol/index.js");

    expect(protocol.MODERN_PROTOCOL_VERSION).toBe("2026-07-28");
    expect(v1Factory).not.toHaveBeenCalled();
  });
});
