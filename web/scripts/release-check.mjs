/** A mechanical launch prerequisite, never publication authorization. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
const root = resolve(import.meta.dirname, "..");
const config = JSON.parse(
  readFileSync(resolve(root, "site.config.json"), "utf8"),
);
if (!config.productionUrl) {
  console.error(
    "BLOCKED: productionUrl is intentionally unset. Owner must choose and review the exact HTTPS deployment root before canonical/absolute social-image metadata can be finalized. No publication is authorized by this check.",
  );
  process.exit(2);
}
const html = readFileSync(resolve(root, "dist/index.html"), "utf8");
const image = new URL("social-preview.png", config.productionUrl).href;
if (
  !html.includes(config.productionUrl) ||
  !html.includes(image) ||
  !html.includes("og:image") ||
  !html.includes("canonical")
) {
  console.error(
    "BLOCKED: build does not contain the exact reviewed production URL and social image. Rebuild and review before publication.",
  );
  process.exit(2);
}
console.log(
  "Mechanical URL/share prerequisites present. Owner publication approval and live-host checks remain mandatory.",
);
