# TypeScript Patterns

Use this reference when the active task touches TypeScript source,
`tsconfig.json`, public type contracts, or type tests.

## TSConfig Baseline

For new TypeScript projects, prefer `strict: true`. It enables the strict
family of checks and may gain additional strictness in future TypeScript
versions, so apply it intentionally on existing codebases.

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "verbatimModuleSyntax": true
  }
}
```

### Strictness Tiers

| Tier | Options | Use When |
|------|---------|----------|
| Baseline | `strict: true` | New TS projects and repos already using strict mode |
| Data safety | `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes` | Arrays, records, env maps, config objects, and API payloads |
| Class safety | `noImplicitOverride` | Class hierarchies or framework classes |
| Module clarity | `verbatimModuleSyntax` | ESM/CJS boundaries, bundlers, or emitted JS must match source intent |

Do not weaken strictness to hide errors. If enabling stricter options creates
large churn, recommend a staged migration with owned follow-up.

## Module Resolution

Choose module settings by runtime target:

| Target | Preferred Direction |
|--------|---------------------|
| Bundled frontend/app code | `moduleResolution: "bundler"` when the bundler owns resolution |
| Modern Node.js runtime output | `module`/`moduleResolution` `node16` or `nodenext` as appropriate |
| Framework-owned TS config | Extend the framework preset and avoid fighting its compiler assumptions |

Use the package's `"type"` field, file extensions, and build tool before
changing module settings. Do not mix ESM and CommonJS through assertions or
compiler flags without documenting the runtime reason.

## Discriminated Unions

Use a shared literal property (`kind`, `type`, `status`) to enable exhaustive narrowing.

```typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number };

function area(s: Shape): number {
  switch (s.kind) {
    case "circle":
      return Math.PI * s.radius ** 2;
    case "rect":
      return s.width * s.height;
    default: {
      const _exhaustive: never = s;
      return _exhaustive;
    }
  }
}
```

### State Machine Pattern

```typescript
type RequestState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "success"; data: Response }
  | { status: "error"; error: Error };
```

## Type Guards

Prefer `unknown` at untrusted boundaries, then narrow with runtime checks.

```typescript
// User-defined type guard
function isString(val: unknown): val is string {
  return typeof val === "string";
}

// Assertion function (throws on failure)
function assertDefined<T>(val: T | undefined): asserts val is T {
  if (val === undefined) throw new Error("Expected defined value");
}
```

## `satisfies` vs `as`

```typescript
// satisfies validates shape without widening away useful inference.
const config = {
  port: 3000,
  host: "localhost",
} satisfies ServerConfig;

// as overrides inference and can hide bugs.
const config = { port: 3000 } as ServerConfig; // AVOID
```

Use `satisfies` for configuration objects, route maps, lookup tables, and
fixture objects where key coverage matters and literal inference is valuable.
Reserve `as` for narrow interop boundaries where runtime evidence is already
checked or the third-party type is incomplete.

## Utility Type Cheat Sheet

| Utility | Effect |
|---------|--------|
| `Partial<T>` | All properties optional |
| `Required<T>` | All properties required |
| `Pick<T, K>` | Subset of properties |
| `Omit<T, K>` | Exclude properties |
| `Record<K, V>` | Object type with key type K and value type V |
| `Readonly<T>` | All properties readonly |
| `ReturnType<F>` | Infer function return type |
| `Parameters<F>` | Infer function parameter tuple |
| `Awaited<T>` | Unwrap Promise type |
| `NonNullable<T>` | Exclude null and undefined |
| `Extract<T, U>` | Members of T assignable to U |
| `Exclude<T, U>` | Members of T not assignable to U |

## Mapped Types

```typescript
// Make all properties optional and nullable
type Patchable<T> = { [K in keyof T]?: T[K] | null };

// Filter to string properties only
type StringKeys<T> = {
  [K in keyof T as T[K] extends string ? K : never]: T[K];
};
```

## Template Literal Types

```typescript
type EventName = `on${Capitalize<"click" | "focus" | "blur">}`;
// "onClick" | "onFocus" | "onBlur"

type Route = `/${string}`;
```

## Type Testing

Use type tests when public helpers, library APIs, or generated types rely on
compile-time behavior.

```typescript
expectTypeOf(result).toEqualTypeOf<Expected>();

// Negative tests should fail if the contract becomes too loose.
// @ts-expect-error invalid status must stay rejected
handleState({ status: "done" });
```

Prefer `@ts-expect-error` over `@ts-ignore`; it fails when the expected error
disappears.

## Runtime Boundary Pattern

Static types do not validate external data. Parse untrusted JSON, env vars,
request bodies, and file content with runtime checks before treating them as
typed values.

```typescript
function readPort(value: unknown): number {
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throw new Error("Expected integer port");
  }
  return value;
}
```
