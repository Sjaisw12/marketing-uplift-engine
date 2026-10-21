import { readFileSync } from "node:fs";
import { render, within } from "@testing-library/react";
import { expect, it } from "vitest";
import { Experience } from "../src/App";
import { DEFAULT, estimate, paired, validateSnapshot } from "../src/data";
const data = validateSnapshot(
  JSON.parse(readFileSync("public/aggregate_results.json", "utf8")),
);
it("explains the exact recorded abstention without changing the primary policy", () => {
  const { container } = render(<Experience data={data} />);
  const decision = container.querySelector("#decision")!;
  const text = decision.textContent!.replace(/\s+/g, " ");
  for (const phrase of [
    "all 40 development",
    "Five configurations failed",
    "remaining 30 configurations",
    "all 120 candidate ranking records",
    "first 10% tranche",
    "assumed e=0.90",
    "insufficient event support was not",
    "not a universal business prescription",
    "abstention is universally optimal",
  ])
    expect(text).toContain(phrase);
  expect(container.querySelector<HTMLSelectElement>("#lab-policy")!.value).toBe(
    "none",
  );
});
it("renders the saved reference values with the common denominator and correct rounded difference", () => {
  const { container } = render(<Experience data={data} />);
  const science = container.querySelector("#science")!;
  const text = science.textContent!.replace(/\s+/g, " ");
  const ipw = estimate(data, "all", 100, { ...DEFAULT, method: "ipw" }).value;
  const dr = estimate(data, "all", 100, DEFAULT).value;
  expect(text).toContain("2,096,939-record final holdout denominator");
  expect(text).toContain(ipw.toFixed(9));
  expect(text).toContain(dr.toFixed(9));
  expect(text).toContain((dr - ipw).toFixed(9).replace("-", "−"));
  expect(text).toContain(
    "Factual calibration cannot establish counterfactual outcome-model correctness",
  );
  const equations = within(science as HTMLElement)
    .getByText("Exact reconciliation & the unnormalized IPW sweep")
    .closest("details")!;
  expect(equations.open).toBe(false);
  expect(equations.textContent).toContain("mean[(e−T)(m₁/e + m₀/(1−e))]");
  expect(equations.textContent).toContain("−A/e² − B/(1−e)² ≤ 0");
  expect(equations.textContent).toContain(
    "No normalized replacement estimate was generated",
  );
});
it.each([30, 40, 50])(
  "grounds the higher-reach qualification in saved paired evidence at %i%%",
  (reach) => {
    const r = estimate(data, "response", reach, DEFAULT);
    expect(r.value).toBeGreaterThan(
      estimate(data, "s_learner", reach, DEFAULT).value,
    );
    expect(r.value).toBeGreaterThan(
      estimate(data, "t_learner", reach, DEFAULT).value,
    );
    for (const [a, b] of [
      ["response", "s_learner"],
      ["response", "t_learner"],
      ["s_learner", "t_learner"],
    ] as const) {
      const p = paired(data, a, b, reach, DEFAULT);
      expect(p.low).toBeLessThanOrEqual(0);
      expect(p.high).toBeGreaterThanOrEqual(0);
    }
  },
);
it("qualifies the saved nine contrasts and mechanical sweep in the newcomer narrative", () => {
  const { container } = render(<Experience data={data} />);
  expect(container.querySelector("#compare")!.textContent).toContain(
    "All nine relevant simultaneous pairwise intervals",
  );
  expect(container.querySelector("#compare")!.textContent).toContain(
    "neither statistical superiority nor equivalence",
  );
  expect(container.querySelector("#decision")!.textContent).toContain(
    "not observed treatment-effect variation",
  );
});
