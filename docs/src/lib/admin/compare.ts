import { timingSafeEqual } from 'node:crypto';

const encoder = new TextEncoder();

function toComparableBytes(value: string): Uint8Array {
  return encoder.encode(value);
}

export function safeEqualStrings(left: string, right: string): boolean {
  const leftBytes = toComparableBytes(left);
  const rightBytes = toComparableBytes(right);

  if (leftBytes.byteLength !== rightBytes.byteLength) return false;
  return timingSafeEqual(leftBytes, rightBytes);
}
