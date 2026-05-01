# Common Memory Leaks

## Uncleared Event Listeners

Listeners attached to `window`, `document`, or long-lived objects can retain callback closures and referenced objects. Remove listeners when components unmount or when the listener is no longer needed.

## Detached DOM Nodes

A detached DOM node is removed from the document but still referenced by JavaScript. This is a useful leak signal, but not always a bug. Some applications intentionally cache detached trees. Ask before nulling references.

## Unintentional Globals

Variables declared without `let`, `const`, or `var` in non-strict mode, or objects attached to `window`, can remain reachable for the page lifetime.

## Closures

Closures can retain large objects from outer scope. Null large values when done or refactor to avoid capturing them.

## Unbounded Caches

Arrays, maps, and objects used as caches must have lifecycle or size limits. Prefer bounded caches or weak collections when keys are objects.
