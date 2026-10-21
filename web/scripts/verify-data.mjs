import { readFileSync, readdirSync } from "node:fs";
import { createHash } from "node:crypto";
import { resolve, join } from "node:path";
const root = resolve(import.meta.dirname, "..");
const expected =
  "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169";
const data = readFileSync(join(root, "public/aggregate_results.json"));
if (createHash("sha256").update(data).digest("hex") !== expected)
  throw new Error("Approved snapshot hash mismatch; build blocked");
const allowed = new Set(["aggregate_results.json", "favicon.svg"]);
if (readdirSync(join(root, "public")).some((f) => !allowed.has(f)))
  throw new Error("Unexpected public asset; disclosure review required");
console.log(
  "Approved public snapshot SHA-256 and public-asset allowlist: PASS",
);
