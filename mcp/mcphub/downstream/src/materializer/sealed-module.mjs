import { canonicalJson, sha256Bytes } from "./canonical.mjs";
import { parseAst } from "rolldown/parseAst";

const FORBIDDEN_BUILTIN_IMPORTS = Object.freeze(["node:module", "node:process", "node:vm"]);
const FORBIDDEN_COMPUTED_PROPERTIES = Object.freeze([
  "Function",
  "constructor",
  "createRequire",
  "dlopen",
  "eval",
  "getBuiltinModule",
  "process",
  "register",
  "registerHooks",
  "require",
]);
const REGEX_PREFIX_KEYWORDS = new Set(["await", "case", "delete", "in", "instanceof", "of", "return", "throw", "typeof", "void", "yield"]);
const REQUIRED_CODE_GENERATION_FLAG = "--disallow-code-generation-from-strings";
const FORBIDDEN_CODE_GENERATION_FLAG = "--no-disallow-code-generation-from-strings";
const SAFE_PROCESS_BINDINGS = new Set(["buffer", "tty_wrap"]);
const HOST_PROCESS_BINDING = typeof process.binding === "function" ? process.binding.bind(process) : null;
let runtimeBoundaryInstalled = false;

export const SEALED_MODULE_POLICY = Object.freeze({
  schemaVersion: 1,
  descriptorBytes: true,
  buildAstAttestation: "authoritative",
  launchLexicalScanner: "defense-in-depth",
  launchConstructorBindingAst: true,
  staticImports: "node:-only",
  forbiddenBuiltinImports: FORBIDDEN_BUILTIN_IMPORTS,
  dynamicImports: false,
  importMeta: false,
  commonJsResolution: false,
  mutableBuiltinResolution: false,
  nativeLoading: false,
  directEvalOrFunction: false,
  inlineFunctionConstructor: false,
  functionConstructorExtraction: false,
  computedProcessAccess: false,
  reflectedProcessOrGlobalAccess: false,
  dangerousConstantGlobalAccess: false,
  runtimeCodeGenerationFromStrings: false,
  runtimeCodeGenerationCanary: true,
  runtimeProcessBuiltinResolution: false,
  runtimeProcessBindingAllowlist: Object.freeze([...SAFE_PROCESS_BINDINGS].sort()),
  reexportResolution: false,
});

export const SEALED_MODULE_POLICY_SHA256 = sha256Bytes(
  Buffer.from(canonicalJson(SEALED_MODULE_POLICY), "utf8"),
);

function invariant(condition, message) {
  if (!condition) throw new Error(message);
}

export function assertRuntimeCapabilityEnvironment({ execArgv = process.execArgv } = {}) {
  invariant(Array.isArray(execArgv) && execArgv.every((argument) => typeof argument === "string"), "downstream runtime execArgv is invalid");
  const normalizedFlags = execArgv.map((argument) => argument.replaceAll("_", "-"));
  invariant(
    normalizedFlags.includes(REQUIRED_CODE_GENERATION_FLAG),
    `downstream runtime requires ${REQUIRED_CODE_GENERATION_FLAG}`,
  );
  invariant(
    !normalizedFlags.includes(FORBIDDEN_CODE_GENERATION_FLAG),
    `downstream runtime forbids ${FORBIDDEN_CODE_GENERATION_FLAG}`,
  );
  let canaryError = null;
  try {
    Function("return 1");
  } catch (error) {
    canaryError = error;
  }
  invariant(
    canaryError instanceof EvalError && /Code generation from strings disallowed/.test(canaryError.message),
    "downstream runtime string code generation canary is enabled",
  );
}

export function installRuntimeCapabilityBoundary({ runtimeProcess = process } = {}) {
  assertRuntimeCapabilityEnvironment();
  if (runtimeBoundaryInstalled) return Object.freeze({ installed: false, processBindings: SAFE_PROCESS_BINDINGS.size });
  invariant(runtimeProcess === process, "downstream runtime process identity mismatch");
  invariant(HOST_PROCESS_BINDING !== null, "downstream runtime process.binding is unavailable");
  const deny = () => {
    throw new Error("downstream runtime capability is forbidden");
  };
  const safeBinding = (name) => {
    invariant(typeof name === "string" && SAFE_PROCESS_BINDINGS.has(name), "downstream runtime process.binding capability is forbidden");
    return HOST_PROCESS_BINDING(name);
  };
  for (const [name, value] of [
    ["_linkedBinding", deny],
    ["binding", safeBinding],
    ["dlopen", deny],
    ["getBuiltinModule", deny],
    ["mainModule", undefined],
  ]) {
    const descriptor = Object.getOwnPropertyDescriptor(runtimeProcess, name);
    invariant(descriptor === undefined || descriptor.configurable, `downstream runtime cannot harden process.${name}`);
    Object.defineProperty(runtimeProcess, name, {
      configurable: false,
      enumerable: descriptor?.enumerable ?? false,
      value,
      writable: false,
    });
  }
  runtimeBoundaryInstalled = true;
  return Object.freeze({ installed: true, processBindings: SAFE_PROCESS_BINDINGS.size });
}

// Preserve executable bytes and blank strings, comments, and template text. Template
// expressions are recursively scanned, so `${import(target)}` remains executable.
function executableMask(source) {
  const mask = Array.from({ length: source.length }, () => " ");

  function skipQuoted(index, terminator) {
    index += 1;
    while (index < source.length) {
      if (source[index] === "\\") index += 2;
      else if (source[index] === terminator) return index + 1;
      else index += 1;
    }
    throw new Error("entry bundle has an unterminated literal");
  }

  function skipBlockComment(index) {
    const end = source.indexOf("*/", index + 2);
    invariant(end !== -1, "entry bundle has an unterminated comment");
    return end + 2;
  }

  function scanTemplate(index) {
    index += 1;
    while (index < source.length) {
      if (source[index] === "\\") {
        index += 2;
      } else if (source[index] === "`") {
        return index + 1;
      } else if (source[index] === "$" && source[index + 1] === "{") {
        index = scanCode(index + 2, true);
      } else {
        index += 1;
      }
    }
    throw new Error("entry bundle has an unterminated template literal");
  }

  function skipRegex(index) {
    index += 1;
    let inClass = false;
    while (index < source.length) {
      const character = source[index];
      if (character === "\\") {
        index += 2;
      } else if (character === "[" && !inClass) {
        inClass = true;
        index += 1;
      } else if (character === "]" && inClass) {
        inClass = false;
        index += 1;
      } else if (character === "/" && !inClass) {
        index += 1;
        while (index < source.length && /[A-Za-z]/.test(source[index])) index += 1;
        return index;
      } else {
        invariant(character !== "\n" && character !== "\r", "entry bundle has an unterminated regular expression");
        index += 1;
      }
    }
    throw new Error("entry bundle has an unterminated regular expression");
  }

  function scanCode(start, templateExpression = false) {
    let index = start;
    let braceDepth = templateExpression ? 1 : 0;
    let canStartRegex = true;
    while (index < source.length) {
      const character = source[index];
      const next = source[index + 1];
      if (character === "/" && next === "/") {
        index += 2;
        while (index < source.length && source[index] !== "\n") index += 1;
        continue;
      }
      if (character === "/" && next === "*") {
        index = skipBlockComment(index);
        continue;
      }
      if (character === "'" || character === '"') {
        index = skipQuoted(index, character);
        canStartRegex = false;
        continue;
      }
      if (character === "`") {
        index = scanTemplate(index);
        canStartRegex = false;
        continue;
      }
      if (character === "/" && canStartRegex) {
        index = skipRegex(index);
        canStartRegex = false;
        continue;
      }
      if (/[A-Za-z_$]/.test(character)) {
        const identifierStart = index;
        while (index < source.length && /[A-Za-z0-9_$]/.test(source[index])) {
          mask[index] = source[index];
          index += 1;
        }
        const identifier = source.slice(identifierStart, index);
        canStartRegex = REGEX_PREFIX_KEYWORDS.has(identifier);
        continue;
      }
      if (/[0-9]/.test(character)) {
        while (index < source.length && /[0-9A-Fa-f_xXobn.eE+-]/.test(source[index])) {
          mask[index] = source[index];
          index += 1;
        }
        canStartRegex = false;
        continue;
      }
      if (templateExpression && character === "{") braceDepth += 1;
      if (templateExpression && character === "}") {
        braceDepth -= 1;
        if (braceDepth === 0) return index + 1;
      }
      mask[index] = character;
      if (!/\s/.test(character)) {
        canStartRegex = "([{=,:;!?&|+-*%^~<>".includes(character);
      }
      index += 1;
    }
    invariant(!templateExpression, "entry bundle has an unterminated template expression");
    return index;
  }

  scanCode(0);
  return mask.join("");
}

function codeIdentifiers(executable) {
  return [...executable.matchAll(/[A-Za-z_$][A-Za-z0-9_$]*/g)].map((match) => ({
    value: match[0],
    index: match.index,
  }));
}

function canonicalIdentifierEscapes(executable) {
  return executable.replace(/\\u(?:\{([0-9A-Fa-f]{1,6})\}|([0-9A-Fa-f]{4}))/g, (_match, braced, fixed) => (
    String.fromCodePoint(Number.parseInt(braced ?? fixed, 16))
  ));
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function assertNoKnownFunctionConstructorExtraction(source) {
  let ast;
  try {
    ast = parseAst(source, { lang: "js", sourceType: "module", astType: "js" }, "sealed-runtime-entry.mjs");
  } catch (error) {
    throw new Error("entry bundle AST parsing failed", { cause: error });
  }

  const nodeScopes = new WeakMap();
  const parents = new WeakMap();
  const nodes = [];
  const mutations = [];

  function createScope(parent, kind) {
    return { parent, kind, bindings: new Map() };
  }

  function nearestVarScope(scope) {
    let current = scope;
    while (current.parent !== null && current.kind !== "function" && current.kind !== "program") {
      current = current.parent;
    }
    return current;
  }

  function declare(scope, name, record) {
    const binding = scope.bindings.get(name) ?? { records: [] };
    binding.records.push(record);
    scope.bindings.set(name, binding);
  }

  function declarePattern(pattern, scope, record) {
    if (pattern?.type === "Identifier") {
      declare(scope, pattern.name, record);
      return;
    }
    if (pattern?.type === "RestElement") {
      declarePattern(pattern.argument, scope, { kind: "unknown", expression: null });
      return;
    }
    if (pattern?.type === "AssignmentPattern") {
      declarePattern(pattern.left, scope, { kind: "unknown", expression: pattern.right });
      return;
    }
    if (pattern?.type === "ArrayPattern") {
      for (const element of pattern.elements ?? []) {
        declarePattern(element, scope, { kind: "unknown", expression: null });
      }
      return;
    }
    if (pattern?.type === "ObjectPattern") {
      for (const property of pattern.properties ?? []) {
        if (property?.type === "RestElement") declarePattern(property.argument, scope, { kind: "unknown", expression: null });
        else if (property?.type === "Property") declarePattern(property.value, scope, { kind: "unknown", expression: null });
      }
    }
  }

  function childNodes(node) {
    const children = [];
    for (const value of Object.values(node)) {
      if (Array.isArray(value)) {
        for (const item of value) {
          if (item !== null && typeof item === "object" && typeof item.type === "string") children.push(item);
        }
      } else if (value !== null && typeof value === "object" && typeof value.type === "string") {
        children.push(value);
      }
    }
    return children;
  }

  function visitPatternExpressions(pattern, scope, parent) {
    if (pattern?.type === "AssignmentPattern") {
      visit(pattern.right, scope, pattern);
      visitPatternExpressions(pattern.left, scope, pattern);
      return;
    }
    if (pattern?.type === "RestElement") {
      visitPatternExpressions(pattern.argument, scope, pattern);
      return;
    }
    if (pattern?.type === "ArrayPattern") {
      for (const element of pattern.elements ?? []) visitPatternExpressions(element, scope, pattern);
      return;
    }
    if (pattern?.type === "ObjectPattern") {
      for (const property of pattern.properties ?? []) {
        if (property?.type === "Property") {
          if (property.computed) visit(property.key, scope, property);
          visitPatternExpressions(property.value, scope, property);
        } else if (property?.type === "RestElement") {
          visitPatternExpressions(property.argument, scope, property);
        }
      }
      return;
    }
    if (pattern !== null && typeof pattern === "object") {
      nodeScopes.set(pattern, scope);
      if (parent !== null) parents.set(pattern, parent);
    }
  }

  function visitFunction(node, scope, parent) {
    nodeScopes.set(node, scope);
    if (parent !== null) parents.set(node, parent);
    nodes.push(node);
    const functionScope = createScope(scope, "function");
    if (node.type === "FunctionExpression" && node.id?.type === "Identifier") {
      declare(functionScope, node.id.name, { kind: "function", expression: node });
    }
    for (const parameter of node.params ?? []) {
      declarePattern(parameter, functionScope, { kind: "unknown", expression: null });
      visitPatternExpressions(parameter, functionScope, node);
    }
    if (node.body?.type === "BlockStatement") {
      nodeScopes.set(node.body, functionScope);
      parents.set(node.body, node);
      nodes.push(node.body);
      for (const statement of node.body.body ?? []) visit(statement, functionScope, node.body);
    } else if (node.body) {
      visit(node.body, functionScope, node);
    }
  }

  function visit(node, scope, parent = null) {
    if (node === null || typeof node !== "object" || typeof node.type !== "string") return;
    nodeScopes.set(node, scope);
    if (parent !== null) parents.set(node, parent);
    nodes.push(node);

    if (node.type === "Program") {
      for (const statement of node.body ?? []) visit(statement, scope, node);
      return;
    }
    if (node.type === "FunctionDeclaration") {
      if (node.id?.type === "Identifier") declare(scope, node.id.name, { kind: "function", expression: node });
      visitFunction(node, scope, parent);
      return;
    }
    if (node.type === "FunctionExpression" || node.type === "ArrowFunctionExpression") {
      visitFunction(node, scope, parent);
      return;
    }
    if (node.type === "BlockStatement") {
      const blockScope = createScope(scope, "block");
      nodeScopes.set(node, blockScope);
      for (const statement of node.body ?? []) visit(statement, blockScope, node);
      return;
    }
    if (node.type === "VariableDeclaration") {
      const declarationScope = node.kind === "var" ? nearestVarScope(scope) : scope;
      for (const declaration of node.declarations ?? []) {
        nodeScopes.set(declaration, scope);
        parents.set(declaration, node);
        nodes.push(declaration);
        const record = { kind: "value", expression: declaration.init ?? null };
        declarePattern(declaration.id, declarationScope, record);
        visitPatternExpressions(declaration.id, scope, declaration);
        if (declaration.init) visit(declaration.init, scope, declaration);
      }
      return;
    }
    if (node.type === "ClassDeclaration") {
      if (node.id?.type === "Identifier") declare(scope, node.id.name, { kind: "function", expression: node });
      if (node.superClass) visit(node.superClass, scope, node);
      const classScope = createScope(scope, "block");
      if (node.id?.type === "Identifier") declare(classScope, node.id.name, { kind: "function", expression: node });
      visit(node.body, classScope, node);
      return;
    }
    if (node.type === "ClassExpression") {
      if (node.superClass) visit(node.superClass, scope, node);
      const classScope = createScope(scope, "block");
      if (node.id?.type === "Identifier") declare(classScope, node.id.name, { kind: "function", expression: node });
      visit(node.body, classScope, node);
      return;
    }
    if (node.type === "CatchClause") {
      const catchScope = createScope(scope, "block");
      declarePattern(node.param, catchScope, { kind: "unknown", expression: null });
      visitPatternExpressions(node.param, catchScope, node);
      visit(node.body, catchScope, node);
      return;
    }
    if (node.type === "ForStatement" || node.type === "ForInStatement" || node.type === "ForOfStatement" || node.type === "SwitchStatement") {
      const loopScope = createScope(scope, "block");
      for (const child of childNodes(node)) visit(child, loopScope, node);
      if ((node.type === "ForInStatement" || node.type === "ForOfStatement") && node.left?.type !== "VariableDeclaration") {
        mutations.push({ pattern: node.left, scope: loopScope, expression: node.right });
      }
      return;
    }
    if (node.type === "ImportDeclaration") {
      for (const specifier of node.specifiers ?? []) {
        if (specifier.local?.type === "Identifier") declare(scope, specifier.local.name, { kind: "unknown", expression: null });
      }
      return;
    }
    if (node.type === "AssignmentExpression") {
      mutations.push({ pattern: node.left, scope, expression: node.operator === "=" ? node.right : null });
    } else if (node.type === "UpdateExpression") {
      mutations.push({ pattern: node.argument, scope, expression: null });
    }
    for (const child of childNodes(node)) visit(child, scope, node);
  }

  const programScope = createScope(null, "program");
  visit(ast, programScope);

  function resolveBinding(name, scope) {
    let current = scope;
    while (current !== null) {
      const binding = current.bindings.get(name);
      if (binding !== undefined) return binding;
      current = current.parent;
    }
    return null;
  }

  function mutatedIdentifiers(pattern) {
    if (pattern?.type === "Identifier") return [pattern];
    if (pattern?.type === "RestElement") return mutatedIdentifiers(pattern.argument);
    if (pattern?.type === "AssignmentPattern") return mutatedIdentifiers(pattern.left);
    if (pattern?.type === "ArrayPattern") return (pattern.elements ?? []).flatMap(mutatedIdentifiers);
    if (pattern?.type === "ObjectPattern") {
      return (pattern.properties ?? []).flatMap((property) => (
        property?.type === "RestElement" ? mutatedIdentifiers(property.argument) : mutatedIdentifiers(property?.value)
      ));
    }
    return [];
  }

  for (const mutation of mutations) {
    for (const identifier of mutatedIdentifiers(mutation.pattern)) {
      const binding = resolveBinding(identifier.name, mutation.scope);
      if (binding !== null) binding.records.push({ kind: "assignment", expression: mutation.expression });
    }
  }

  function expressionMayBeFunction(expression, seen) {
    if (expression === null || typeof expression !== "object") return false;
    if (["ArrowFunctionExpression", "FunctionExpression", "ClassExpression"].includes(expression.type)) return true;
    if (expression.type === "Identifier") {
      const binding = resolveBinding(expression.name, nodeScopes.get(expression));
      return binding !== null && bindingMayBeFunction(binding, seen);
    }
    if (expression.type === "ChainExpression") return expressionMayBeFunction(expression.expression, seen);
    if (expression.type === "SequenceExpression") return expressionMayBeFunction(expression.expressions?.at(-1), seen);
    if (expression.type === "ConditionalExpression") {
      return expressionMayBeFunction(expression.consequent, seen) || expressionMayBeFunction(expression.alternate, seen);
    }
    if (expression.type === "LogicalExpression") {
      return expressionMayBeFunction(expression.left, seen) || expressionMayBeFunction(expression.right, seen);
    }
    return false;
  }

  function bindingMayBeFunction(binding, seen = new Set()) {
    if (seen.has(binding)) return false;
    const next = new Set(seen);
    next.add(binding);
    return binding.records.some((record) => (
      record.kind === "function" || expressionMayBeFunction(record.expression, next)
    ));
  }

  function expressionMayEqualString(expression, expected, seen) {
    if (expression === null || typeof expression !== "object") return false;
    if (expression.type === "Literal") return expression.value === expected;
    if (expression.type === "TemplateLiteral" && expression.expressions?.length === 0) {
      return (expression.quasis?.[0]?.value?.cooked ?? expression.quasis?.[0]?.value?.raw) === expected;
    }
    if (expression.type === "BinaryExpression" && expression.operator === "+") {
      const literalValue = (node, localSeen) => {
        if (node?.type === "Literal" && typeof node.value === "string") return node.value;
        if (node?.type === "Identifier") {
          const binding = resolveBinding(node.name, nodeScopes.get(node));
          if (binding === null || localSeen.has(binding)) return null;
          const values = binding.records.map((record) => literalValue(record.expression, new Set([...localSeen, binding]))).filter((value) => value !== null);
          return values.length > 0 && new Set(values).size === 1 ? values[0] : null;
        }
        if (node?.type === "BinaryExpression" && node.operator === "+") {
          const left = literalValue(node.left, localSeen);
          const right = literalValue(node.right, localSeen);
          return left === null || right === null ? null : left + right;
        }
        return null;
      };
      return literalValue(expression, seen) === expected;
    }
    if (expression.type === "Identifier") {
      const binding = resolveBinding(expression.name, nodeScopes.get(expression));
      if (binding === null || seen.has(binding)) return false;
      const next = new Set(seen);
      next.add(binding);
      return binding.records.some((record) => expressionMayEqualString(record.expression, expected, next));
    }
    if (expression.type === "ChainExpression") return expressionMayEqualString(expression.expression, expected, seen);
    if (expression.type === "SequenceExpression") return expressionMayEqualString(expression.expressions?.at(-1), expected, seen);
    if (expression.type === "ConditionalExpression" || expression.type === "LogicalExpression") {
      return expressionMayEqualString(expression.left ?? expression.consequent, expected, seen)
        || expressionMayEqualString(expression.right ?? expression.alternate, expected, seen);
    }
    return false;
  }

  function memberIsConstructor(node) {
    return node.computed
      ? expressionMayEqualString(node.property, "constructor", new Set())
      : node.property?.type === "Identifier" && node.property.name === "constructor";
  }

  function safeConstructorUse(node) {
    let subject = node;
    let parent = parents.get(subject);
    while (parent?.type === "ChainExpression" && parent.expression === subject) {
      subject = parent;
      parent = parents.get(subject);
    }
    const safeName = parent?.type === "MemberExpression"
      && parent.object === subject
      && parent.computed === false
      && parent.property?.type === "Identifier"
      && parent.property.name === "name";
    const safeComparison = parent?.type === "BinaryExpression"
      && ["===", "!==", "==", "!="].includes(parent.operator)
      && (parent.left === subject || parent.right === subject);
    return safeName || safeComparison;
  }

  for (const node of nodes) {
    if (
      node.type === "MemberExpression"
      && memberIsConstructor(node)
      && (node.object?.type === "CallExpression" || expressionMayBeFunction(node.object, new Set()))
      && !safeConstructorUse(node)
    ) {
      throw new Error(`entry bundle known function constructor extraction is forbidden at offset ${node.start ?? "unknown"}`);
    }
    if (node.type === "VariableDeclarator" && node.id?.type === "ObjectPattern" && expressionMayBeFunction(node.init, new Set())) {
      for (const property of node.id.properties ?? []) {
        if (property?.type === "Property" && (
          (!property.computed && (property.key?.name ?? property.key?.value) === "constructor")
          || (property.computed && expressionMayEqualString(property.key, "constructor", new Set()))
        )) {
          throw new Error(`entry bundle known function constructor destructuring is forbidden at offset ${property.start ?? "unknown"}`);
        }
      }
    }
  }
}

function decodeQuotedString(token) {
  const quote = token[0];
  invariant((quote === "'" || quote === '"') && token.at(-1) === quote, "invalid constant string token");
  let value = "";
  for (let index = 1; index < token.length - 1; index += 1) {
    const character = token[index];
    if (character !== "\\") {
      value += character;
      continue;
    }
    index += 1;
    invariant(index < token.length - 1, "invalid constant string escape");
    const escape = token[index];
    const simple = { b: "\b", f: "\f", n: "\n", r: "\r", t: "\t", v: "\v", "0": "\0" };
    if (Object.hasOwn(simple, escape)) {
      value += simple[escape];
    } else if (escape === "x") {
      const hex = token.slice(index + 1, index + 3);
      invariant(/^[0-9A-Fa-f]{2}$/.test(hex), "invalid constant hexadecimal escape");
      value += String.fromCodePoint(Number.parseInt(hex, 16));
      index += 2;
    } else if (escape === "u") {
      const braced = token[index + 1] === "{";
      const end = braced ? token.indexOf("}", index + 2) : index + 5;
      const hex = braced ? token.slice(index + 2, end) : token.slice(index + 1, end);
      invariant(end !== -1 && /^[0-9A-Fa-f]{1,6}$/.test(hex), "invalid constant Unicode escape");
      value += String.fromCodePoint(Number.parseInt(hex, 16));
      index = end;
    } else if (escape !== "\n") {
      value += escape;
    }
  }
  return value;
}

function splitConstantConcatenation(expression) {
  const parts = [];
  let start = 0;
  let quote = null;
  let templateDepth = 0;
  let parentheses = 0;
  for (let index = 0; index < expression.length; index += 1) {
    const character = expression[index];
    if (quote !== null) {
      if (character === "\\") index += 1;
      else if (quote === "`" && character === "$" && expression[index + 1] === "{") {
        templateDepth += 1;
        index += 1;
      } else if (quote === "`" && character === "}" && templateDepth > 0) {
        templateDepth -= 1;
      } else if (character === quote && templateDepth === 0) {
        quote = null;
      }
      continue;
    }
    if (character === "'" || character === '"' || character === "`") quote = character;
    else if (character === "(") parentheses += 1;
    else if (character === ")") parentheses -= 1;
    else if (character === "+" && parentheses === 0) {
      parts.push(expression.slice(start, index));
      start = index + 1;
    }
  }
  parts.push(expression.slice(start));
  return parts;
}

function constantString(expression) {
  let value = expression.trim();
  while (value.startsWith("(") && value.endsWith(")")) value = value.slice(1, -1).trim();
  const parts = splitConstantConcatenation(value);
  if (parts.length > 1) {
    const decoded = parts.map((part) => constantString(part));
    return decoded.every((part) => part !== null) ? decoded.join("") : null;
  }
  if ((value.startsWith("'") && value.endsWith("'")) || (value.startsWith('"') && value.endsWith('"'))) {
    try {
      return decodeQuotedString(value);
    } catch {
      return null;
    }
  }
  if (!value.startsWith("`") || !value.endsWith("`")) return null;
  let decoded = "";
  for (let index = 1; index < value.length - 1;) {
    if (value[index] === "\\") {
      try {
        decoded += decodeQuotedString(`"\\${value[index + 1]}"`);
      } catch {
        return null;
      }
      index += 2;
    } else if (value[index] === "$" && value[index + 1] === "{") {
      let depth = 1;
      let end = index + 2;
      while (end < value.length - 1 && depth > 0) {
        if (value[end] === "{") depth += 1;
        else if (value[end] === "}") depth -= 1;
        end += 1;
      }
      if (depth !== 0) return null;
      const replacement = constantString(value.slice(index + 2, end - 1));
      if (replacement === null) return null;
      decoded += replacement;
      index = end;
    } else {
      decoded += value[index];
      index += 1;
    }
  }
  return decoded;
}

function callArgumentExpressions(source, executable, openParenthesis) {
  invariant(executable[openParenthesis] === "(", "invalid call argument scan offset");
  const expressions = [];
  let start = openParenthesis + 1;
  let parentheses = 1;
  let brackets = 0;
  let braces = 0;
  for (let index = start; index < executable.length; index += 1) {
    const character = executable[index];
    if (character === "(") parentheses += 1;
    else if (character === ")") {
      parentheses -= 1;
      if (parentheses === 0) {
        expressions.push(source.slice(start, index));
        return expressions;
      }
    } else if (character === "[") brackets += 1;
    else if (character === "]") brackets -= 1;
    else if (character === "{") braces += 1;
    else if (character === "}") braces -= 1;
    else if (character === "," && parentheses === 1 && brackets === 0 && braces === 0) {
      expressions.push(source.slice(start, index));
      start = index + 1;
    }
  }
  return null;
}

function assertNoDangerousComputedProperties(source, executable) {
  const forbidden = new Set(FORBIDDEN_COMPUTED_PROPERTIES);
  for (let start = executable.indexOf("["); start !== -1; start = executable.indexOf("[", start + 1)) {
    let depth = 1;
    let end = start + 1;
    while (end < executable.length && depth > 0) {
      if (executable[end] === "[") depth += 1;
      else if (executable[end] === "]") depth -= 1;
      end += 1;
    }
    if (depth !== 0) continue;
    const property = constantString(source.slice(start + 1, end - 1));
    invariant(property === null || !forbidden.has(property), `entry bundle computed ${property} access is forbidden`);
  }
}

function assertNoComputedProcessOrGlobalAccess(source, executable) {
  const processAliases = new Set(["process"]);
  const globalAliases = new Set(["global", "globalThis"]);
  const reflectAliases = new Set(["Reflect"]);
  const reflectGetAliases = new Set();
  const processFactoryAliases = new Set();
  const globalFactoryAliases = new Set();
  const declaration = /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*([A-Za-z_$][A-Za-z0-9_$]*)\b/g;
  const callResultDeclaration = /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\(\s*\)/g;
  const arrowFactoryDeclaration = /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(?:async\s*)?(?:\(\s*\)|[A-Za-z_$][A-Za-z0-9_$]*)\s*=>\s*([A-Za-z_$][A-Za-z0-9_$]*)\b/g;
  const functionFactoryDeclaration = /\b(?:async\s+)?function\s*\*?\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\([^)]*\)\s*\{[^{}]*?\breturn\s+([A-Za-z_$][A-Za-z0-9_$]*)\b/g;
  const processMemberDeclaration = /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:\?\.)?\s*\.\s*process\b/g;
  const processDestructureDeclaration = /\b(?:const|let|var)\s*\{\s*process\s*:\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*\}\s*=\s*([A-Za-z_$][A-Za-z0-9_$]*)\b/g;
  const reflectGetDeclaration = /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*([A-Za-z_$][A-Za-z0-9_$]*)\s*(?:\?\.)?\s*\.\s*get\b/g;
  const reflectGetDestructureDeclaration = /\b(?:const|let|var)\s*\{\s*get\s*(?::\s*([A-Za-z_$][A-Za-z0-9_$]*))?\s*\}\s*=\s*([A-Za-z_$][A-Za-z0-9_$]*)\b/g;
  const declaredName = /\b(?:const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\b/g;
  const declaredNameCounts = new Map();
  for (const match of executable.matchAll(declaredName)) {
    declaredNameCounts.set(match[1], (declaredNameCounts.get(match[1]) ?? 0) + 1);
  }
  // Rolldown reuses short identifier spellings across lexical scopes. Keep the
  // launch-time scanner conservative without treating one alias declaration as
  // a global alias when the same spelling is declared elsewhere. The build AST
  // validator remains authoritative and scope-aware for every emitted access.
  const isUnambiguousAlias = (name) => (declaredNameCounts.get(name) ?? 0) <= 1;
  let changed = true;
  while (changed) {
    changed = false;
    declaration.lastIndex = 0;
    for (const match of executable.matchAll(declaration)) {
      if (isUnambiguousAlias(match[1]) && processAliases.has(match[2]) && !processAliases.has(match[1])) {
        processAliases.add(match[1]);
        changed = true;
      }
      if (isUnambiguousAlias(match[1]) && globalAliases.has(match[2]) && !globalAliases.has(match[1])) {
        globalAliases.add(match[1]);
        changed = true;
      }
      if (isUnambiguousAlias(match[1]) && reflectAliases.has(match[2]) && !reflectAliases.has(match[1])) {
        reflectAliases.add(match[1]);
        changed = true;
      }
    }
    arrowFactoryDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(arrowFactoryDeclaration)) {
      if (processAliases.has(match[2]) && !processFactoryAliases.has(match[1])) {
        processFactoryAliases.add(match[1]);
        changed = true;
      }
      if (globalAliases.has(match[2]) && !globalFactoryAliases.has(match[1])) {
        globalFactoryAliases.add(match[1]);
        changed = true;
      }
    }
    functionFactoryDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(functionFactoryDeclaration)) {
      if (processAliases.has(match[2]) && !processFactoryAliases.has(match[1])) {
        processFactoryAliases.add(match[1]);
        changed = true;
      }
      if (globalAliases.has(match[2]) && !globalFactoryAliases.has(match[1])) {
        globalFactoryAliases.add(match[1]);
        changed = true;
      }
    }
    callResultDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(callResultDeclaration)) {
      if (isUnambiguousAlias(match[1]) && processFactoryAliases.has(match[2]) && !processAliases.has(match[1])) {
        processAliases.add(match[1]);
        changed = true;
      }
      if (isUnambiguousAlias(match[1]) && globalFactoryAliases.has(match[2]) && !globalAliases.has(match[1])) {
        globalAliases.add(match[1]);
        changed = true;
      }
    }
    processMemberDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(processMemberDeclaration)) {
      if (isUnambiguousAlias(match[1]) && globalAliases.has(match[2]) && !processAliases.has(match[1])) {
        processAliases.add(match[1]);
        changed = true;
      }
    }
    processDestructureDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(processDestructureDeclaration)) {
      if (isUnambiguousAlias(match[1]) && globalAliases.has(match[2]) && !processAliases.has(match[1])) {
        processAliases.add(match[1]);
        changed = true;
      }
    }
    reflectGetDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(reflectGetDeclaration)) {
      if (isUnambiguousAlias(match[1]) && reflectAliases.has(match[2]) && !reflectGetAliases.has(match[1])) {
        reflectGetAliases.add(match[1]);
        changed = true;
      }
    }
    reflectGetDestructureDeclaration.lastIndex = 0;
    for (const match of executable.matchAll(reflectGetDestructureDeclaration)) {
      const alias = match[1] ?? "get";
      if (isUnambiguousAlias(alias) && reflectAliases.has(match[2]) && !reflectGetAliases.has(alias)) {
        reflectGetAliases.add(alias);
        changed = true;
      }
    }
  }
  for (const alias of processAliases) {
    const identifier = escapeRegExp(alias);
    const computedProcess = new RegExp(String.raw`\b${identifier}\s*(?:\?\.)?\s*\[`).exec(executable);
    invariant(
      computedProcess === null,
      `entry bundle computed process or global member access is forbidden for ${alias} at offset ${computedProcess?.index ?? "unknown"}: ${JSON.stringify(
        computedProcess === null
          ? ""
          : executable.slice(computedProcess.index, Math.min(executable.length, computedProcess.index + 160)),
      )}`,
    );
    invariant(
      !new RegExp(String.raw`\b${identifier}\s*(?:\?\.)?\s*\.\s*dlopen\b`).test(executable),
      "entry bundle process.dlopen is forbidden",
    );
    invariant(
      !new RegExp(String.raw`\bReflect\s*\.\s*get\s*\(\s*${identifier}\s*,`).test(executable),
      "entry bundle reflected process or global member access is forbidden",
    );
  }
  for (const alias of globalAliases) {
    const identifier = escapeRegExp(alias);
    invariant(
      !new RegExp(String.raw`\bReflect\s*\.\s*get\s*\(\s*${identifier}\s*,`).test(executable),
      "entry bundle reflected process or global member access is forbidden",
    );
  }
  for (const reflectAlias of reflectAliases) {
    const reflectIdentifier = escapeRegExp(reflectAlias);
    for (const targetAlias of new Set([...processAliases, ...globalAliases])) {
      const targetIdentifier = escapeRegExp(targetAlias);
      invariant(
        !new RegExp(String.raw`\b${reflectIdentifier}\s*(?:\?\.)?\s*\.\s*get\s*\(\s*${targetIdentifier}\b`).test(executable),
        "entry bundle reflected process or global member access is forbidden",
      );
    }
    const reflectedCall = new RegExp(String.raw`\b${reflectIdentifier}\s*(?:\?\.)?\s*\.\s*get\s*\(`, "g");
    for (const match of executable.matchAll(reflectedCall)) {
      const openParenthesis = (match.index ?? 0) + match[0].lastIndexOf("(");
      const argumentsList = callArgumentExpressions(source, executable, openParenthesis);
      invariant(argumentsList !== null, "entry bundle has an unterminated Reflect.get call");
      invariant(constantString(argumentsList[1] ?? "") !== "constructor", "entry bundle reflected constructor access is forbidden");
    }
  }
  for (const getAlias of reflectGetAliases) {
    const getIdentifier = escapeRegExp(getAlias);
    for (const targetAlias of new Set([...processAliases, ...globalAliases])) {
      const targetIdentifier = escapeRegExp(targetAlias);
      invariant(
        !new RegExp(String.raw`\b${getIdentifier}\s*\(\s*${targetIdentifier}\b`).test(executable),
        "entry bundle reflected process or global member access is forbidden",
      );
    }
    const reflectedAliasCall = new RegExp(String.raw`\b${getIdentifier}\s*\(`, "g");
    for (const match of executable.matchAll(reflectedAliasCall)) {
      const openParenthesis = (match.index ?? 0) + match[0].lastIndexOf("(");
      const argumentsList = callArgumentExpressions(source, executable, openParenthesis);
      invariant(argumentsList !== null, "entry bundle has an unterminated reflected getter call");
      invariant(constantString(argumentsList[1] ?? "") !== "constructor", "entry bundle reflected constructor access is forbidden");
    }
  }
}

function assertNoDangerousDescriptorRecovery(source, executable) {
  const descriptorCall = /\bObject\s*\.\s*(getOwnPropertyDescriptor|getOwnPropertyDescriptors)\s*\(/g;
  for (const match of executable.matchAll(descriptorCall)) {
    const openParenthesis = (match.index ?? 0) + match[0].lastIndexOf("(");
    const argumentsList = callArgumentExpressions(source, executable, openParenthesis);
    invariant(argumentsList !== null, "entry bundle has an unterminated property descriptor call");
    const target = argumentsList[0] ?? "";
    const property = constantString(argumentsList[1] ?? "");
    const targetsRuntimeGlobal = /\b(?:global|globalThis|process)\b/.test(target);
    invariant(
      property !== "constructor" && !(property === "process" && targetsRuntimeGlobal),
      "entry bundle forbidden reflective descriptor recovery is forbidden",
    );
  }
}

export function assertSelfContainedModule(bytes) {
  invariant(Buffer.isBuffer(bytes), "entry bundle must be descriptor-read bytes");
  const source = bytes.toString("utf8");
  invariant(Buffer.from(source, "utf8").equals(bytes), "entry bundle must be valid UTF-8");
  invariant(!source.includes("\0"), "entry bundle contains NUL");
  const executable = executableMask(source);
  const canonicalExecutable = canonicalIdentifierEscapes(executable);
  const commonJsPseudoGlobal = /\b__(?:dirname|filename)\b/.exec(canonicalExecutable);
  invariant(
    commonJsPseudoGlobal === null,
    `entry bundle CommonJS pseudo-global is forbidden at offset ${commonJsPseudoGlobal?.index ?? "unknown"}`,
  );
  const interstitial = String.raw`(?:\s|\/\*[\s\S]*?\*\/|\/\/[^\n]*\n)*`;
  invariant(!new RegExp(String.raw`\bimport${interstitial}[.(]`).test(canonicalExecutable), "entry bundle dynamic import or import.meta is forbidden");
  invariant(!/\brequire\s*\(|\bcreateRequire\b|\bgetBuiltinModule\b/.test(canonicalExecutable), "entry bundle mutable module resolution is forbidden");
  invariant(!/\bdlopen\b/.test(canonicalExecutable), "entry bundle native module loading is forbidden");
  const withoutSafeFunctionReferences = canonicalExecutable.replace(
    /\bFunction\s*\.\s*prototype(?!\s*\.\s*constructor\b)/g,
    (match) => " ".repeat(match.length),
  );
  const dynamicCodeGeneration = /\beval\b|\bFunction\b/.exec(withoutSafeFunctionReferences);
  invariant(
    dynamicCodeGeneration === null,
    `entry bundle dynamic code generation is forbidden at offset ${dynamicCodeGeneration?.index ?? "unknown"}: ${JSON.stringify(
      dynamicCodeGeneration === null
        ? ""
        : source.slice(dynamicCodeGeneration.index, Math.min(source.length, dynamicCodeGeneration.index + 160)),
    )}`,
  );
  invariant(
    !/\(\s*(?:\([^)]*\)\s*=>|(?:async\s+)?function\b)[\s\S]{0,512}?\)\s*(?:\?\.)?\s*\.\s*constructor\b/.test(canonicalExecutable),
    "entry bundle inline function constructor access is forbidden",
  );
  const withoutSafeConstructorNames = canonicalExecutable.replace(
    /\.\s*constructor\s*(?:\?\.\s*|\.\s*)name\b/g,
    (match) => " ".repeat(match.length),
  );
  const callableConstructor = /\.\s*constructor\s*(?:\?\.)?\s*\(/.exec(withoutSafeConstructorNames);
  invariant(
    callableConstructor === null,
    `entry bundle callable constructor access is forbidden at offset ${callableConstructor?.index ?? "unknown"}: ${JSON.stringify(
      callableConstructor === null
        ? ""
        : source.slice(callableConstructor.index, Math.min(source.length, callableConstructor.index + 160)),
    )}`,
  );
  assertNoComputedProcessOrGlobalAccess(source, executable);
  assertNoDangerousDescriptorRecovery(source, executable);
  assertNoDangerousComputedProperties(source, executable);
  assertNoKnownFunctionConstructorExtraction(source);
  const identifiers = codeIdentifiers(withoutSafeFunctionReferences);
  for (const { value, index } of identifiers) {
    if (value === "import") {
      const tail = source.slice(index);
      invariant(!/^import\s*(?:\/\*[\s\S]*?\*\/\s*)?[.(]/.test(tail), "entry bundle dynamic import or import.meta is forbidden");
      const declaration = tail.match(/^import\s+(?:[^;\n]+?\s+from\s+)?(["'])(node:[A-Za-z0-9_./-]+)\1\s*;/);
      invariant(declaration !== null, "entry bundle imports must be static node: built-ins");
      invariant(!FORBIDDEN_BUILTIN_IMPORTS.includes(declaration[2]), `entry bundle ${declaration[2]} import is forbidden`);
    }
    const identifierTail = source.slice(index, Math.min(source.length, index + 64));
    const safeRequirePropertyKey = value === "require" && /^require\s*:/.test(identifierTail);
    invariant(value !== "require" || safeRequirePropertyKey, "entry bundle CommonJS resolution is forbidden");
    invariant(value !== "createRequire", "entry bundle createRequire is forbidden");
    invariant(value !== "getBuiltinModule", "entry bundle process module access is forbidden");
    invariant(value !== "eval", "entry bundle eval is forbidden");
    invariant(value !== "Function", "entry bundle dynamic Function is forbidden");
  }
  invariant(!/\bexport\s+(?:\*|\{[^}]*\})\s+from\b/.test(executable), "entry bundle re-export resolution is forbidden");
  return Object.freeze({ sha256: sha256Bytes(bytes), source, policySha256: SEALED_MODULE_POLICY_SHA256 });
}

export async function importSelfContainedModule(bytes) {
  const sealed = assertSelfContainedModule(bytes);
  const url = `data:text/javascript;base64,${bytes.toString("base64")}#sha256-${sealed.sha256}`;
  return import(url);
}
