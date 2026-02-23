# React 19 Patterns

> Framework-dependent behavior. Server Components are default in **Next.js App Router** and **Remix v2+** only. In **Vite + React**, all components are client components and `"use client"` is unnecessary.

---

## 1. Server vs Client Component Decision Tree

| Framework | Default type | `"use client"` needed? | `"use server"` available? |
|-----------|-------------|------------------------|--------------------------|
| **Next.js App Router** | Server Component | Yes — hooks, events, browser APIs | Yes |
| **Remix v2+** | Server Component | Yes — hooks, events, browser APIs | Yes |
| **Vite + React** | Client Component | Never needed | No (no server runtime) |
| **Astro + React** | Island (client) | No — Astro handles via `client:*` | No |

**Add `"use client"` (Next.js/Remix only)** when using: `useState`, `useReducer`, `useEffect`, `useRef`, `useContext`, event handlers (`onClick`, `onChange`), browser APIs (`window`, `document`, `localStorage`), or third-party libs that use any of the above.

**Minimize client boundaries** — push `"use client"` to interactive leaves:

```
ServerLayout                    <- server (no directive)
  ServerHeader                  <- server
    ClientSearchBar             <- "use client" (useState)
  ServerContent                 <- server (data fetching)
    ClientLikeButton            <- "use client" (onClick)
```

Pass Server Components as `children` to Client Components when composition requires it.

---

## 2. Server Actions

Mark async functions with `"use server"` to create server-executable endpoints. The framework handles serialization and network transport.

**Separate file (recommended):**

```ts
// app/actions.ts
"use server";
export async function createPost(formData: FormData) {
  await db.posts.create({ title: formData.get("title") as string });
  revalidatePath("/posts");
}
```

**Inline (single-use):** Place `"use server"` inside the async function body within a Server Component.

**Progressive enhancement:** `<form action={serverAction}>` works without JavaScript — browser submits as standard POST. With JS loaded, React intercepts for seamless SPA behavior.

**Constraints:** Must be async. Arguments/returns must be serializable. Only available in Next.js/Remix — not Vite SPAs.

---

## 3. useActionState

```ts
const [state, formAction, isPending] = useActionState(actionFn, initialState);
```

- `actionFn(previousState, formData)` — returns new state
- `isPending` — `true` while action is in flight

```tsx
"use client";
import { useActionState } from "react";
import { updateProfile } from "@/app/actions";

export function ProfileForm() {
  const [state, formAction, isPending] = useActionState(updateProfile, { message: "" });
  return (
    <form action={formAction}>
      <input name="name" required />
      {state.errors?.name && <p className="text-red-500">{state.errors.name[0]}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Saving..." : "Save"}
      </button>
      {state.message && <p>{state.message}</p>}
    </form>
  );
}
```

Server-side: validate with Zod, return `{ message, errors }` shape. Return field-level errors for inline display.

---

## 4. use() Hook

Read Promises or Context during render. Unlike other hooks, callable inside conditionals and loops.

```tsx
import { use, Suspense } from "react";

function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise); // suspends until resolved
  return comments.map((c) => <p key={c.id}>{c.text}</p>);
}

// Wrap in Suspense + ErrorBoundary
<ErrorBoundary fallback={<p>Failed to load.</p>}>
  <Suspense fallback={<p>Loading...</p>}>
    <Comments commentsPromise={commentsPromise} />
  </Suspense>
</ErrorBoundary>
```

**Conditional context:** `use(SomeContext)` works inside `if` blocks where `useContext` cannot.

| Scenario | Use `use()`? | Alternative |
|----------|-------------|-------------|
| Server Component passes promise to Client Component | Yes | -- |
| Reading context conditionally | Yes | `useContext` cannot |
| SPA data fetching (Vite + React) | **No** | TanStack Query / SWR |
| Promise created during render | **No** | Lift or cache the promise |

`use()` unwraps promises created outside the component. It does NOT replace data-fetching libraries. For SPA caching, deduplication, and revalidation, use TanStack Query.

---

## 5. useOptimistic

```ts
const [optimisticState, addOptimistic] = useOptimistic(actualState, updateFn);
```

- `updateFn(currentState, optimisticValue)` — returns state to display immediately
- React reverts to `actualState` automatically when the transition completes

```tsx
"use client";
import { useOptimistic, startTransition } from "react";

export function LikeButton({ liked, count }: { liked: boolean; count: number }) {
  const [optimistic, setOptimistic] = useOptimistic(
    { liked, count },
    (current, newLiked: boolean) => ({
      liked: newLiked,
      count: current.count + (newLiked ? 1 : -1),
    })
  );

  function handleClick() {
    startTransition(async () => {
      setOptimistic(!optimistic.liked);
      try {
        await toggleLike(); // Server Action
      } catch {
        toast.error("Action failed."); // optimistic state reverts automatically
      }
    });
  }

  return <button onClick={handleClick}>{optimistic.liked ? "Unlike" : "Like"} ({optimistic.count})</button>;
}
```

**Rollback:** If the server action throws or `actualState` does not change, the optimistic value is discarded and UI snaps back to the real state.

---

## 6. Suspense and Streaming

**Suspense boundaries** control loading UI for components that suspend (`use()`, `React.lazy`, Suspense-aware libraries). Match granularity to the user experience — group content that should appear together.

**Streaming SSR (Next.js/Remix):** Server renders available content and streams Suspense fallbacks. Each section replaces its fallback independently as data resolves.

```tsx
// Server Component — page.tsx
export default function Dashboard() {
  return (
    <main>
      <h1>Dashboard</h1>
      <Suspense fallback={<StatsSkeleton />}>
        <Stats />         {/* streams independently */}
      </Suspense>
      <Suspense fallback={<ChartSkeleton />}>
        <RevenueChart />  {/* streams independently */}
      </Suspense>
    </main>
  );
}
```

**Always pair with Error Boundaries.** Error Boundary wraps Suspense — order matters:

```tsx
<ErrorBoundary fallback={<ErrorCard />}>
  <Suspense fallback={<Skeleton />}>
    <AsyncComponent />
  </Suspense>
</ErrorBoundary>
```

---

## 7. Decision Matrix

| Scenario | Pattern | Framework | Key API |
|----------|---------|-----------|---------|
| Form submission + validation | Server Actions + `useActionState` | Next.js, Remix | `useActionState` |
| Data fetching (SPA) | TanStack Query / SWR | Vite + React | `useQuery` |
| Data fetching (SSR) | Server Component `async/await` | Next.js, Remix | -- |
| Async data to client component | `use()` + Suspense | Next.js, Remix | `use` |
| Optimistic UI (server) | `useOptimistic` + Server Action | Next.js, Remix | `useOptimistic` |
| Optimistic UI (SPA) | TanStack Query `onMutate` | Vite + React | `useMutation` |
| Loading states (streaming) | Suspense boundaries | Next.js, Remix | `<Suspense>` |
| Loading states (SPA) | TanStack Query `isPending` | Vite + React | `useQuery` |
| Error recovery (async) | Error Boundary + Suspense | All | `react-error-boundary` |
| Conditional context | `use(Context)` | All | `use` |

---

## 8. Anti-Patterns

**Unnecessary `"use client"` everywhere.** In Next.js/Remix, adding it to every component defeats Server Components — only add to interactive leaves. In Vite + React, the directive is entirely unnecessary.

**useEffect for data fetching in Server Component apps:**

```tsx
// WRONG in Next.js App Router — fetch in a Server Component instead
"use client";
useEffect(() => { fetch("/api/users").then(r => r.json()).then(setUsers); }, []);
```

Fetch in Server Components with `async/await` or use `use()` with Suspense. In Vite SPAs, `useEffect` fetching works but TanStack Query is preferred for caching and revalidation.

**Missing Error Boundaries.** Every `<Suspense>` wrapping async content needs an Error Boundary. Without one, rejected promises crash the tree up to the nearest ancestor boundary (often root).

**Creating promises during render:**

```tsx
// WRONG — new promise every render, infinite suspend loop
const data = use(fetch("/api/data").then(r => r.json()));
```

Create promises outside the component (Server Component, event handler, cached function) and pass as props.

**Mixing server and client state.** Never read databases or filesystem in `"use client"` components. Keep server data in Server Components, pass serializable results down.
