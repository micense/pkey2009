/**
 * PKEY2009 encoding and checksum, ported from keygen/python/pkey2009/keygen.py.
 *
 * The 10-bit checksum is CRC-32 (poly 0x04C11DB7, init 0xFFFFFFFF) over the
 * 16-byte key block, truncated to its low 10 bits.
 */

export const DIGITS = 'BCDFGHJKMPQRTVWXY2346789';

const BASE = 24n;
const SECURITY_MAX = (1n << 53n) - 1n;

function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte << 24;
    for (let bit = 0; bit < 8; bit++) {
      crc = crc & 0x80000000 ? (crc << 1) ^ 0x04c11db7 : crc << 1;
    }
  }
  return crc >>> 0;
}

function payload(group, serial, security, upgrade) {
  return (
    (BigInt(group) & 0xfffffn) |
    ((BigInt(serial) & 0x3fffffffn) << 20n) |
    ((BigInt(security) & SECURITY_MAX) << 50n) |
    ((BigInt(upgrade) & 1n) << 113n)
  );
}

function blockBytes(value) {
  const bytes = new Uint8Array(16);
  for (let i = 0; i < bytes.length; i++) {
    bytes[i] = Number(value & 0xffn);
    value >>= 8n;
  }
  return bytes;
}

export function predictChecksum(group, serial, security, upgrade) {
  const crc = crc32(blockBytes(payload(group, serial, security, upgrade)));
  return ~crc & 0x3ff;
}

export function encode(group, serial, security, checksum, upgrade) {
  let value = payload(group, serial, security, upgrade) | ((BigInt(checksum) & 0x3ffn) << 103n);
  const digits = new Array(25);
  for (let i = digits.length - 1; i >= 0; i--) {
    digits[i] = Number(value % BASE);
    value /= BASE;
  }

  const text = digits.map((digit) => DIGITS[digit]).join('');
  const position = DIGITS.indexOf(text[0]);
  const rest = text.slice(1);
  const key = rest.slice(0, position) + 'N' + rest.slice(position);
  return key.replace(/(.{5})(?=.)/g, '$1-');
}

export function decode(input) {
  const compact = String(input).toUpperCase().replace(/[-\s]/g, '');
  if (compact.length !== 25) throw new Error('a PKEY2009 key has 25 characters');

  const position = compact.indexOf('N');
  if (position < 0 || position >= DIGITS.length) throw new Error('the N is missing or misplaced');
  const text = DIGITS[position] + compact.replace('N', '');

  let value = 0n;
  for (const character of text) {
    const digit = DIGITS.indexOf(character);
    if (digit < 0) throw new Error(`invalid character "${character}"`);
    value = value * BASE + BigInt(digit);
  }

  return {
    group: Number(value & 0xfffffn),
    serial: Number((value >> 20n) & 0x3fffffffn),
    security: (value >> 50n) & SECURITY_MAX,
    checksum: Number((value >> 103n) & 0x3ffn),
    upgrade: Number((value >> 113n) & 1n),
  };
}

export function forge(group, serial, security, upgrade) {
  const checksum = predictChecksum(group, serial, security, upgrade);
  return { key: encode(group, serial, security, checksum, upgrade), checksum };
}

export function randomSecurity() {
  const words = new Uint32Array(2);
  crypto.getRandomValues(words);
  return (BigInt(words[0]) << 21n) | (BigInt(words[1]) & 0x1fffffn);
}
