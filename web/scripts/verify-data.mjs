import { readFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { resolve, join } from "node:path";
const root = resolve(import.meta.dirname, "..");
const expected =
  "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169";
const data = readFileSync(join(root, "public/aggregate_results.json"));
if (createHash("sha256").update(data).digest("hex") !== expected)
  throw new Error("Approved snapshot hash mismatch; build blocked");
const allowed = new Set([
  "aggregate_results.json",
  "favicon.svg",
  "social-preview.svg",
  "social-preview.png",
]);
if (readdirSync(join(root, "public")).some((f) => !allowed.has(f)))
  throw new Error("Unexpected public asset; disclosure review required");
console.log(
  "Approved public snapshot SHA-256 and public-asset allowlist: PASS",
);

const png = readFileSync(join(root, "public/social-preview.png"));
if (
  png.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a" ||
  png.readUInt32BE(16) !== 1200 ||
  png.readUInt32BE(20) !== 630
)
  throw new Error("Social preview must be the reviewed 1200x630 PNG");
const svg = readFileSync(join(root, "public/social-preview.svg"), "utf8");
if (
  /<script|<foreignObject|(?:href|src)\s*=\s*["\']https?:|\bon\w+\s*=/i.test(
    svg,
  )
)
  throw new Error("Unexpected external/active social-art content");
