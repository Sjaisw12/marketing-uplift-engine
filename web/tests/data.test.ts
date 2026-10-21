import { readFileSync } from "node:fs";
import { describe, it, expect, vi } from "vitest";
import Decimal from "decimal.js";
import {
  DEFAULT,
  decodeSnapshot,
  estimate,
  lookup,
  observed,
  paired,
  validateSnapshot,
  loadSnapshot,
  type Snapshot,
  type Options,
  type Model,
} from "../src/data";
import { illustrate } from "../src/budget";
import { fmtDecimal } from "../src/Charts";
import references from "./python-budget-reference.json";
const raw = readFileSync("public/aggregate_results.json");
const data = validateSnapshot(JSON.parse(raw.toString()));
const bytes = () => Uint8Array.from(raw).buffer;
const clone = () => JSON.parse(raw.toString()) as Snapshot;
describe("pinned aggregate contract", () => {
  it("independently verifies exact bytes and all 1530 saved rows", async () => {
    expect((await decodeSnapshot(bytes())).comparisons).toHaveLength(1530);
  });
  it("blocks tampered bytes before parsing", async () => {
    const b = Uint8Array.from(raw);
    b[0] = 33;
    await expect(decodeSnapshot(b.buffer)).rejects.toThrow("validation");
  });
  it("blocks oversized data", async () => {
    await expect(decodeSnapshot(new ArrayBuffer(2000001))).rejects.toThrow(
      "validation",
    );
  });
  it.each([
    "unknown field",
    "missing comparison",
    "duplicate comparison",
    "primary changed",
    "wrong population",
    "invalid support",
    "reversed interval",
    "nonfinite",
    "wrong family",
    "unknown scenario",
    "unknown provenance",
  ])("rejects %s", (kind) => {
    const d = clone();
    switch (kind) {
      case "unknown field":
        Object.assign(d, { predictions: [1, 2] });
        break;
      case "missing comparison":
        d.comparisons.pop();
        break;
      case "duplicate comparison":
        d.comparisons[1] = d.comparisons[0];
        break;
      case "primary changed":
        d.primary.assignments = 1;
        break;
      case "wrong population":
        d.population.holdout_rows--;
        break;
      case "invalid support":
        d.support.control_visits = -1;
        break;
      case "reversed interval":
        d.comparisons[0].pointwise_low_per_1000 = 999;
        break;
      case "nonfinite":
        d.comparisons[0].estimate_per_1000 = NaN;
        break;
      case "wrong family":
        d.methodology.simultaneous_family_size = 10;
        break;
      case "unknown scenario":
        d.comparisons[0].propensity_assumption = 0.84;
        break;
      case "unknown provenance":
        d.provenance.dataset_sha256 = "not-a-hash";
    }
    expect(() => validateSnapshot(d)).toThrow();
  });
  it("has a single public fetch path and omits credentials", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      arrayBuffer: async () => bytes(),
    } as Response);
    await loadSnapshot();
    expect(fetchMock).toHaveBeenCalledWith(
      `${import.meta.env.BASE_URL}aggregate_results.json`,
      {
        credentials: "omit",
      },
    );
  });
  it("fails closed on an HTTP error", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({ ok: false } as Response);
    await expect(loadSnapshot()).rejects.toThrow();
  });
});
describe("saved selections, units and pairing", () => {
  it("shows descriptive rates with percentage-point units", () => {
    expect(observed(data).treatment).toBeCloseTo(86523 / 1782398, 14);
    expect(observed(data).control).toBeCloseTo(12016 / 314541, 14);
    expect(observed(data).pp).toBeCloseTo(1.0341333156248161, 12);
  });
  it.each([0.8, 0.825, 0.85, 0.875, 0.9])(
    "selects exact saved scenario %s",
    (e) => {
      for (const method of ["dr", "ipw"] as const)
        for (const uncertainty of ["iid", "stratified"] as const)
          for (const interval of ["pointwise", "simultaneous"] as const) {
            const o = { method, uncertainty, interval, propensity: e };
            const expected = data.comparisons.find(
              (r) =>
                r.contrast === "s_learner:2_minus_none" &&
                r.evaluator === method &&
                r.uncertainty === uncertainty &&
                r.propensity_assumption === e,
            )!;
            expect(estimate(data, "s_learner", 20, o)).toEqual({
              value: expected.estimate_per_1000,
              low: expected[`${interval}_low_per_1000`],
              high: expected[`${interval}_high_per_1000`],
            });
          }
    },
  );
  it("rejects interpolation, unsupported reach, method and anchor", () => {
    expect(() => estimate(data, "s_learner", 15)).toThrow();
    expect(() =>
      estimate(data, "s_learner", 20, { ...DEFAULT, propensity: 0.84 }),
    ).toThrow();
    expect(() => estimate(data, "all", 20)).toThrow();
    expect(() => lookup(data, "missing")).toThrow();
    expect(() =>
      estimate(data, "s_learner", 20, {
        ...DEFAULT,
        method: "unknown",
      } as unknown as Options),
    ).toThrow();
  });
  it("reverses paired endpoints rather than recomputing intervals", () => {
    const a = paired(data, "t_learner", "s_learner", 20),
      b = paired(data, "s_learner", "t_learner", 20);
    expect(a).toEqual({ value: -b.value, low: -b.high, high: -b.low });
    expect(() => paired(data, "random", "random", 20)).toThrow();
  });
});
describe("Python budget reference parity", () => {
  it.each(references.map((r, i) => ({ ...r, i })))(
    "matches frozen Python arithmetic fixture $i",
    ({ input: a, expected: e }) => {
      const r = illustrate(
        data,
        a.model as Model,
        a.reach,
        a.population,
        a.cost,
        a.value,
        a.budget,
        a.options as Options,
      );
      expect(r.assignments).toBe(e.assignments);
      for (const [value, expected] of [
        [r.gain, e.gain],
        [r.spend, e.spend],
        [r.net, e.net],
        [r.unspent, e.unspent],
      ] as const)
        expect(value.sub(expected).abs().lt("0.000000001")).toBe(true);
      expect(r.bounds![0].sub(e.bounds[0]).abs().lt("0.000000001")).toBe(true);
      expect(r.bounds![1].sub(e.bounds[1]).abs().lt("0.000000001")).toBe(true);
    },
  );
  it("retains no targeting, zero costs, negatives and exact ceiling", () => {
    const r = illustrate(data, "none", 0, 10000, ".01", "1", "500");
    expect(r.assignments).toBe(0);
    expect(r.bounds).toBeNull();
    expect(r.unspent.toString()).toBe("500");
    expect(illustrate(data, "random", 10, 11, "0", "1", "0").assignments).toBe(
      2,
    );
    expect(
      illustrate(data, "random", 50, 10000, "0", "1", "0", {
        ...DEFAULT,
        method: "ipw",
        propensity: 0.9,
      }).gain.lt(0),
    ).toBe(true);
    expect(
      illustrate(data, "s_learner", 20, 10000, ".01", "0", "20").net.toString(),
    ).toBe("-20");
  });
  it("rejects unaffordable scenarios without silently trimming", () => {
    expect(() =>
      illustrate(data, "random", 10, 11, ".01", "1", ".019"),
    ).toThrow("No automatic trimming");
  });
  it.each([NaN, Infinity, -1, true, "", "0xFF", "-0.001"])(
    "rejects invalid money %s",
    (value) => {
      expect(() =>
        illustrate(data, "random", 10, 100, value, "1", "20"),
      ).toThrow();
    },
  );
  it.each([0, 1.5, 1e9 + 1, NaN, Infinity])(
    "rejects invalid audience %s",
    (n) => {
      expect(() => illustrate(data, "random", 10, n, "0", "1", "0")).toThrow();
    },
  );
  it("keeps signed zero valid and large financial labels exact", () => {
    expect(
      illustrate(data, "none", 0, 10, "-0", "1", "0").spend.toString(),
    ).toBe("0");
    expect(fmtDecimal(new Decimal("12345678901234567890.12"), 2)).toBe(
      "12,345,678,901,234,567,890.12",
    );
  });
});

it("does not expose the 100% anchor as a simulator policy", () => {
  expect(() =>
    illustrate(data, "all" as Model, 100, 1000, "0", "1", "0"),
  ).toThrow("saved diagnostic");
});
