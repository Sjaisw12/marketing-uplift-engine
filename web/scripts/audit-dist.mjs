import { readFileSync, readdirSync, statSync } from "node:fs";
import { resolve, relative, join } from "node:path";
import { createHash } from "node:crypto";
const root = resolve(import.meta.dirname, "../dist");
const files = [];
function walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p);
    else files.push(p);
  }
}
walk(root);
const allowed = new Set([
  "index.html",
  "aggregate_results.json",
  "favicon.svg",
  "social-preview.svg",
  "social-preview.png",
]);
const secrets = [
  /-----BEGIN (?:OPENSSH |RSA |EC |ENCRYPTED )?PRIVATE KEY-----/,
  /gh[pousr]_[A-Za-z0-9]{30,}/,
  /github_pat_[A-Za-z0-9_]{30,}/,
  /AGE-SECRET-KEY-1[A-Z0-9]+/,
];
for (const p of files) {
  const name = relative(root, p).replaceAll("\\", "/");
  if (!allowed.has(name) && !/^assets\/[\w-]+\.(js|css)$/.test(name))
    throw new Error("Unexpected distribution file: " + name);
  if (
    !name.endsWith(".png") &&
    secrets.some((pattern) => pattern.test(readFileSync(p, "utf8")))
  )
    throw new Error("Credential-like content in distribution file: " + name);
}
const hash = createHash("sha256")
  .update(readFileSync(join(root, "aggregate_results.json")))
  .digest("hex");
if (hash !== "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169")
  throw new Error("Distribution aggregate hash mismatch");
const total = files.reduce((n, p) => n + statSync(p).size, 0);
if (total > 2000000)
  throw new Error("Unexpected distribution growth; review required");
console.log(
  `Distribution allowlist, aggregate identity and credential-format audit: PASS (${files.length} files, ${total} bytes)`,
);
