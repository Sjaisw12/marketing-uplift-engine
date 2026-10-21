import Decimal from "decimal.js";
import {
  checkOptions,
  DEFAULT,
  MODELS,
  estimate,
  type Model,
  type Options,
  type Snapshot,
} from "./data";
const D = Decimal.clone({ precision: 28, rounding: Decimal.ROUND_HALF_EVEN });
function money(input: unknown) {
  if (typeof input !== "string" && typeof input !== "number")
    throw new Error("Money inputs must be finite and nonnegative.");
  if (String(input).trim() === "")
    throw new Error("Complete all hypothetical inputs.");
  let v;
  try {
    if (
      !/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(String(input).trim())
    )
      throw new Error();
    v = new D(String(input).trim());
  } catch {
    throw new Error("Money inputs must be finite and nonnegative.");
  }
  if (!v.isFinite() || v.lt(0) || v.gt("1000000000000"))
    throw new Error(
      "Money inputs must be finite, nonnegative and at most 1 trillion.",
    );
  return v;
}
export function illustrate(
  d: Snapshot,
  model: Model | "none",
  reach: number,
  population: number,
  cost: unknown,
  value: unknown,
  budget: unknown,
  o: Options = DEFAULT,
) {
  checkOptions(o);
  if (![...MODELS, "none"].includes(model))
    throw new Error(
      "Simulator supports no targeting or saved diagnostic rankings only.",
    );
  if (!Number.isSafeInteger(population) || population < 1 || population > 1e9)
    throw new Error(
      "Eligible audience must be an integer from 1 to 1 billion.",
    );
  const [c, v, cap] = [cost, value, budget].map(money);
  if (model === "none") {
    if (reach !== 0) throw new Error("No targeting always has zero reach.");
    return {
      assignments: 0,
      actualReach: new D(0),
      gain: new D(0),
      bounds: null,
      spend: new D(0),
      net: new D(0),
      incrementalValue: new D(0),
      unspent: cap,
    };
  }
  const saved = estimate(d, model, reach, o);
  const assignments = Math.floor((population * reach + 99) / 100);
  const spend = c.mul(assignments);
  if (spend.gt(cap))
    throw new Error(
      `This scenario needs ${spend.toFixed(2)} units, above the ${cap.toFixed(2)} budget. No automatic trimming: choose a saved lower reach or no targeting.`,
    );
  const scale = new D(population).div(1000),
    gain = new D(String(saved.value)).mul(scale),
    incrementalValue = v.mul(gain);
  return {
    assignments,
    actualReach: new D(assignments).div(population),
    gain,
    bounds: [
      new D(String(saved.low)).mul(scale),
      new D(String(saved.high)).mul(scale),
    ] as const,
    spend,
    net: incrementalValue.sub(spend),
    incrementalValue,
    unspent: cap.sub(spend),
  };
}
