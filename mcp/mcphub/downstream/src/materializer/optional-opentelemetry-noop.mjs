function createNoopSpan() {
  const span = {
    end() {},
    setAttribute() {},
    setStatus() {},
    recordException() {},
    updateName() {
      return span;
    },
  };
  return span;
}

const noopSpan = createNoopSpan();
const noopTracer = {
  startActiveSpan(_name, ...rest) {
    return rest.at(-1)(noopSpan);
  },
};

export const SpanStatusCode = Object.freeze({ UNSET: 0, OK: 1, ERROR: 2 });
export const trace = Object.freeze({
  getTracer() {
    return noopTracer;
  },
  getActiveSpan() {},
});
