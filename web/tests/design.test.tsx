import { readFileSync, readdirSync } from "node:fs";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect } from "vitest";
import { TeachingDemo } from "../src/App";
it("supports the teaching interaction using only a keyboard", async () => {
  render(<TeachingDemo />);
  const user = userEvent.setup();
  await user.tab();
  await user.tab();
  await user.keyboard("{Enter}");
  expect(screen.getByText("An additional visit—in this example.")).toBeTruthy();
});
it.each([
  ["183831", "f7f4ee"],
  ["59665d", "f7f4ee"],
  ["ae492d", "f7f4ee"],
  ["d2dccb", "183831"],
])("core text contrast %s on %s meets 4.5:1", (foreground, background) => {
  const lum = (hex: string) =>
    [0, 2, 4]
      .map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
      .map((c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
      .reduce((sum, c, i) => sum + c * [0.2126, 0.7152, 0.0722][i], 0);
  const [a, b] = [lum(foreground), lum(background)].sort((a, b) => a - b);
  expect((b + 0.05) / (a + 0.05)).toBeGreaterThanOrEqual(4.5);
});
it("uses local design assets, reduced motion, focus styles and no external fonts", () => {
  const css = readFileSync("src/styles.css", "utf8");
  expect(css).toContain("prefers-reduced-motion");
  expect(css).toContain("focus-visible");
  expect(css).not.toMatch(/@import|url\(/);
  expect(readdirSync("public").sort()).toEqual([
    "aggregate_results.json",
    "favicon.svg",
    "social-preview.png",
    "social-preview.svg",
  ]);
});
