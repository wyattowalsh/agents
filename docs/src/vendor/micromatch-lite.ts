type MatchPattern = string | string[];

const regexCache = new Map<string, RegExp>();

function escapeRegex(source: string): string {
  return source.replace(/[|\\{}()[\]^$+?.]/g, '\\$&');
}

function globToRegExpSource(pattern: string): string {
  let out = '^';

  for (let i = 0; i < pattern.length; i += 1) {
    const char = pattern[i];

    if (char === '*') {
      const next = pattern[i + 1];

      if (next === '*') {
        const afterGlobstar = pattern[i + 2];
        // `**/` should also match the zero-directory case (e.g. `**/*` matches `foo`)
        if (afterGlobstar === '/') {
          out += '(?:.*/)?';
          i += 2;
          continue;
        }
        out += '.*';
        i += 1;
        continue;
      }

      out += '[^/]*';
      continue;
    }

    if (char === '?') {
      out += '[^/]';
      continue;
    }

    if (char === '[') {
      const closeIndex = pattern.indexOf(']', i + 1);
      if (closeIndex > i + 1) {
        const rawClass = pattern.slice(i + 1, closeIndex);
        const normalized = rawClass.startsWith('!') ? `^${rawClass.slice(1)}` : rawClass;
        out += `[${normalized}]`;
        i = closeIndex;
        continue;
      }
    }

    out += escapeRegex(char);
  }

  out += '$';
  return out;
}

function getRegex(pattern: string): RegExp {
  const cached = regexCache.get(pattern);
  if (cached) return cached;

  const compiled = new RegExp(globToRegExpSource(pattern));
  regexCache.set(pattern, compiled);
  return compiled;
}

export function isMatch(input: string, pattern: MatchPattern): boolean {
  if (Array.isArray(pattern)) {
    return pattern.some((entry) => isMatch(input, entry));
  }

  return getRegex(pattern).test(input);
}

const micromatch = { isMatch };

export default micromatch;
