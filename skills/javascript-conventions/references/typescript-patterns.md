# TypeScript Patterns

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
  }
}
// Compiler errors if a variant is unhandled (with --strict).
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
// satisfies: validates type WITHOUT widening — preserves literal inference
const config = {
  port: 3000,
  host: "localhost",
} satisfies ServerConfig;
// config.port is number (literal), not unknown

// as: type assertion — OVERRIDES inference, can hide bugs
const config = { port: 3000 } as ServerConfig; // AVOID
```

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

## Strict Config Checklist

```jsonc
// tsconfig.json — enable all of these
{
  "compilerOptions": {
    "strict": true,              // enables all strict checks
    "noUncheckedIndexedAccess": true,  // arrays/records return T | undefined
    "exactOptionalPropertyTypes": true, // distinguish undefined from missing
    "noImplicitOverride": true   // require override keyword
  }
}
```
