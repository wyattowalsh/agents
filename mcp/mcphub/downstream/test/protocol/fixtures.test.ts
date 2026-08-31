import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
  FROZEN_ERROR_MATRIX_CASES,
  PROTOCOL_CONFORMANCE_CASE_IDS,
  canonicalSha256,
  createThingsProtocolHandler,
} from "../../src/protocol/index.js";
import {
  RecordingProvider,
  authOptions,
  makeSyntheticContract,
  responseJson,
} from "./helpers.js";

interface WireFixture {
  readonly headers: Readonly<Record<string, string>>;
  readonly body: Readonly<Record<string, unknown>>;
}

async function fixture(name: string): Promise<unknown> {
  const directory = dirname(fileURLToPath(import.meta.url));
  const candidates = [
    resolve(directory, "../../fixtures/protocol", name),
    resolve(directory, "../../../fixtures/protocol", name),
  ];
  for (const candidate of candidates) {
    try {
      return JSON.parse(await readFile(candidate, "utf8")) as unknown;
    } catch (error) {
      if (
        error === null ||
        typeof error !== "object" ||
        !("code" in error) ||
        error.code !== "ENOENT"
      ) {
        throw error;
      }
    }
  }
  throw new Error(`protocol_fixture_not_found:${name}`);
}

function request(value: WireFixture): Request {
  return new Request("http://127.0.0.1:46683/mcp/things", {
    method: "POST",
    headers: { ...value.headers },
    body: JSON.stringify(value.body),
  });
}

describe("frozen protocol fixtures", () => {
  it.each([
    ["modern-discover.request.json", "modern-discover.response.json"],
    ["legacy-initialize.request.json", "legacy-initialize.response.json"],
  ])("matches %s to the exact SDK response fixture", async (requestName, responseName) => {
    const { projection, snapshot } = await makeSyntheticContract();
    const handler = await createThingsProtocolHandler(
      new RecordingProvider(snapshot),
      projection,
    );
    const requestFixture = (await fixture(requestName)) as WireFixture;
    const expected = await fixture(responseName);
    const response = await handler.fetch(
      request(requestFixture),
      authOptions(),
    );

    expect(response.status).toBe(200);
    expect(await responseJson(response)).toEqual(expected);
  });

  it("freezes the complete fail-closed error mapping", async () => {
    const matrix = (await fixture("error-matrix.json")) as {
      readonly schemaVersion: number;
      readonly cases: readonly {
        readonly id: string;
        readonly status: number;
        readonly code: number;
        readonly sdkDispatch: boolean;
        readonly providerDispatch: boolean;
      }[];
    };
    expect(matrix.schemaVersion).toBe(1);
    expect(matrix.cases).toEqual(FROZEN_ERROR_MATRIX_CASES);
    expect(matrix.cases.map((entry) => entry.id)).toEqual([
      "method-mismatch",
      "name-mismatch",
      "missing-client-capabilities",
      "unsupported-version",
      "unknown-modern-method",
      "parse-error",
    ]);
    expect(new Set(matrix.cases.map((entry) => entry.code))).toEqual(
      new Set([-32020, -32021, -32022, -32601, -32700]),
    );
    expect(
      matrix.cases
        .filter((entry) => entry.providerDispatch)
        .map((entry) => entry.id),
    ).toEqual([]);
  });

  it("binds the report fixture to every passed case and both matrix digests", async () => {
    const report = (await fixture("conformance-report.json")) as {
      readonly execution: {
        readonly status: string;
        readonly caseCount: number;
        readonly passedCaseCount: number;
        readonly caseIds: readonly string[];
        readonly cases: readonly {
          readonly id: string;
          readonly status: string;
          readonly httpStatus: number;
          readonly jsonRpcCode: number | null;
          readonly sdkDispatchCount: number;
          readonly providerDispatchCount: number;
          readonly resultSha256: string;
        }[];
        readonly sdkDispatchCount: number;
        readonly providerDispatchCount: number;
        readonly errorMatrixSha256: string;
        readonly errorMatrixResultsSha256: string;
        readonly resultBundleSha256: string;
      };
    };
    const execution = report.execution;
    expect(execution).toMatchObject({
      status: "passed",
      caseCount: 22,
      passedCaseCount: 22,
      caseIds: PROTOCOL_CONFORMANCE_CASE_IDS,
      sdkDispatchCount: 6,
      providerDispatchCount: 1,
    });
    expect(execution.cases.map((entry) => entry.id)).toEqual(
      PROTOCOL_CONFORMANCE_CASE_IDS,
    );
    expect(execution.cases.every((entry) => entry.status === "passed")).toBe(
      true,
    );
    expect(execution.errorMatrixSha256).toBe(
      canonicalSha256({ schemaVersion: 1, cases: FROZEN_ERROR_MATRIX_CASES }),
    );
    const actualMatrix = FROZEN_ERROR_MATRIX_CASES.map((expected) => {
      const actual = execution.cases.find((entry) => entry.id === expected.id);
      if (actual === undefined) {
        throw new Error(`protocol_case_missing:${expected.id}`);
      }
      return {
        id: actual.id,
        httpStatus: actual.httpStatus,
        jsonRpcCode: actual.jsonRpcCode,
        sdkDispatchCount: actual.sdkDispatchCount,
        providerDispatchCount: actual.providerDispatchCount,
      };
    });
    expect(execution.errorMatrixResultsSha256).toBe(
      canonicalSha256(actualMatrix),
    );
    expect(execution.resultBundleSha256).toBe(
      canonicalSha256(execution.cases),
    );
  });
});
