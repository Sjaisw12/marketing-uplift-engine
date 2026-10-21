/** Approved public aggregates only. No backend, model, row-level or execution interfaces. */
export const SNAPSHOT_SHA256 =
  "358c331d72df76d0ca1e4fddd36c7c35be32b1a0b2dd0ae12949c5967ac46169";
export const MODELS = ["random", "response", "s_learner", "t_learner"] as const;
export type Model = (typeof MODELS)[number];
export const REACHES = [10, 20, 30, 40, 50] as const;
export const SCENARIOS = [0.8, 0.825, 0.85, 0.875, 0.9] as const;
export type Options = {
  method: "dr" | "ipw";
  propensity: number;
  uncertainty: "iid" | "stratified";
  interval: "simultaneous" | "pointwise";
};
export const DEFAULT: Options = {
  method: "dr",
  propensity: 0.85,
  uncertainty: "iid",
  interval: "simultaneous",
};
export const LABELS: Record<Model | string, string> = {
  random: "Random",
  response: "Treated response",
  s_learner: "S-learner",
  t_learner: "T-learner",
  none: "No targeting",
  all: "All-targeting anchor",
};
export const COLORS: Record<Model, string> = {
  random: "#657577",
  response: "#ae492d",
  s_learner: "#26776b",
  t_learner: "#6e5aa6",
};
export const FIELDS = [
  "estimate_per_1000",
  "standard_error_per_1000",
  "pointwise_low_per_1000",
  "pointwise_high_per_1000",
  "simultaneous_low_per_1000",
  "simultaneous_high_per_1000",
] as const;
export type Row = {
  contrast: string;
  evaluator: "ipw" | "dr" | "s_dr";
  propensity_assumption: number;
  uncertainty: "iid" | "stratified";
} & Record<(typeof FIELDS)[number], number>;
export interface Snapshot {
  schema: number;
  publication_status: string;
  provenance: Record<string, string>;
  population: {
    source_rows: number;
    development_rows: number;
    holdout_rows: number;
  };
  support: {
    control_visits: number;
    control_nonvisits: number;
    treatment_visits: number;
    treatment_nonvisits: number;
  };
  primary: {
    policy: string;
    assignments: number;
    hypothetical_spending: number;
    incremental_gain_relative_to_none: number;
    identity_not_optimality_proof: boolean;
  };
  methodology: {
    reference_propensity: number;
    propensity_scenarios: number[];
    reaches: number[];
    replicates: number;
    confidence: number;
    simultaneous_family_size: number;
    iid_critical: number;
    stratified_critical: number;
    stratified_status: string;
    units: string;
  };
  comparisons: Row[];
}
function fail(): never {
  throw new Error(
    "Approved public snapshot validation failed. No substitute data is permitted.",
  );
}
function keys(x: unknown, expected: string[]) {
  if (
    !x ||
    typeof x !== "object" ||
    Array.isArray(x) ||
    Object.keys(x).sort().join("|") !== [...expected].sort().join("|")
  )
    fail();
}
const equal = (a: unknown, b: unknown) =>
  JSON.stringify(a) === JSON.stringify(b);
export function validateSnapshot(input: unknown): Snapshot {
  keys(input, [
    "schema",
    "publication_status",
    "provenance",
    "population",
    "support",
    "primary",
    "methodology",
    "comparisons",
  ]);
  const d = input as Snapshot;
  if (d.schema !== 1 || d.publication_status !== "local-review-only") fail();
  keys(d.provenance, [
    "evaluation_commit",
    "execution_lock_sha256",
    "result_manifest_sha256",
    "source_aggregate_sha256",
    "model_manifest_sha256",
    "dataset_sha256",
  ]);
  for (const [k, v] of Object.entries(d.provenance))
    if (
      typeof v !== "string" ||
      !new RegExp(`^[a-f0-9]{${k === "evaluation_commit" ? 40 : 64}}$`).test(v)
    )
      fail();
  keys(d.population, ["source_rows", "development_rows", "holdout_rows"]);
  keys(d.support, [
    "control_nonvisits",
    "control_visits",
    "treatment_nonvisits",
    "treatment_visits",
  ]);
  if (
    [...Object.values(d.population), ...Object.values(d.support)].some(
      (v) => !Number.isSafeInteger(v) || v <= 0,
    )
  )
    fail();
  if (
    d.population.source_rows !== 13979592 ||
    d.population.development_rows !== 11882653 ||
    d.population.holdout_rows !== 2096939 ||
    Object.values(d.support).reduce((a, b) => a + b, 0) !==
      d.population.holdout_rows ||
    d.population.development_rows + d.population.holdout_rows !==
      d.population.source_rows
  )
    fail();
  keys(d.primary, [
    "policy",
    "assignments",
    "hypothetical_spending",
    "incremental_gain_relative_to_none",
    "identity_not_optimality_proof",
  ]);
  if (
    d.primary.policy !== "no-targeting" ||
    d.primary.assignments !== 0 ||
    d.primary.hypothetical_spending !== 0 ||
    d.primary.incremental_gain_relative_to_none !== 0 ||
    d.primary.identity_not_optimality_proof !== true
  )
    fail();
  const m = d.methodology;
  keys(m, [
    "reference_propensity",
    "propensity_scenarios",
    "reaches",
    "replicates",
    "confidence",
    "simultaneous_family_size",
    "iid_critical",
    "stratified_critical",
    "stratified_status",
    "units",
  ]);
  if (
    m.reference_propensity !== 0.85 ||
    !equal(m.propensity_scenarios, SCENARIOS) ||
    !equal(m.reaches, [0.1, 0.2, 0.3, 0.4, 0.5]) ||
    m.replicates !== 2000 ||
    m.confidence !== 0.95 ||
    m.simultaneous_family_size !== 765 ||
    m.stratified_status !== "defined" ||
    m.units !== "estimated incremental visits per 1000 eligible records" ||
    ![m.iid_critical, m.stratified_critical].every(
      (v) => Number.isFinite(v) && v > 0,
    )
  )
    fail();
  const names = new Set(["all_minus_none"]);
  for (const a of MODELS)
    for (let k = 1; k <= 5; k++) names.add(`${a}:${k}_minus_none`);
  for (let i = 0; i < MODELS.length; i++)
    for (let j = i + 1; j < MODELS.length; j++)
      for (let k = 1; k <= 5; k++)
        names.add(`${MODELS[i]}_minus_${MODELS[j]}:${k}`);
  if (!Array.isArray(d.comparisons) || d.comparisons.length !== 1530) fail();
  const seen = new Set<string>();
  for (const r of d.comparisons) {
    keys(r, [
      "contrast",
      "evaluator",
      "propensity_assumption",
      "uncertainty",
      ...FIELDS,
    ]);
    const key = [
      r.uncertainty,
      r.evaluator,
      r.propensity_assumption,
      r.contrast,
    ].join("|");
    if (
      !["iid", "stratified"].includes(r.uncertainty) ||
      !["ipw", "dr", "s_dr"].includes(r.evaluator) ||
      !SCENARIOS.includes(r.propensity_assumption as 0.8) ||
      !names.has(r.contrast) ||
      seen.has(key)
    )
      fail();
    seen.add(key);
    if (
      FIELDS.some((f) => typeof r[f] !== "number" || !Number.isFinite(r[f])) ||
      r.standard_error_per_1000 < 0
    )
      fail();
    for (const kind of ["pointwise", "simultaneous"] as const)
      if (r[`${kind}_low_per_1000`] > r[`${kind}_high_per_1000`]) fail();
    for (const [side, sign] of [
      ["low", -1],
      ["high", 1],
    ] as const) {
      const expected =
        r.estimate_per_1000 +
        sign * m[`${r.uncertainty}_critical`] * r.standard_error_per_1000;
      if (
        Math.abs(r[`simultaneous_${side}_per_1000`] - expected) >
        1e-10 * Math.max(1, Math.abs(expected))
      )
        fail();
    }
  }
  return d;
}
export async function decodeSnapshot(bytes: ArrayBuffer): Promise<Snapshot> {
  if (bytes.byteLength > 2_000_000) fail();
  const hash = Array.from(
    new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)),
    (x) => x.toString(16).padStart(2, "0"),
  ).join("");
  if (hash !== SNAPSHOT_SHA256) fail();
  return validateSnapshot(JSON.parse(new TextDecoder().decode(bytes)));
}
export async function loadSnapshot() {
  const response = await fetch(
    `${import.meta.env.BASE_URL}aggregate_results.json`,
    { credentials: "omit" },
  );
  if (!response.ok) fail();
  return decodeSnapshot(await response.arrayBuffer());
}
export function checkOptions(o: Options) {
  if (
    !["dr", "ipw"].includes(o.method) ||
    !SCENARIOS.includes(o.propensity as 0.8) ||
    !["iid", "stratified"].includes(o.uncertainty) ||
    !["simultaneous", "pointwise"].includes(o.interval)
  )
    throw new Error(
      "Choose an exact saved evaluation scenario. No interpolation.",
    );
}
export function lookup(d: Snapshot, contrast: string, o: Options = DEFAULT) {
  checkOptions(o);
  const r = d.comparisons.find(
    (r) =>
      r.contrast === contrast &&
      r.evaluator === o.method &&
      r.propensity_assumption === o.propensity &&
      r.uncertainty === o.uncertainty,
  );
  if (!r) throw new Error("Saved comparison missing.");
  return {
    value: r.estimate_per_1000,
    low: r[`${o.interval}_low_per_1000`],
    high: r[`${o.interval}_high_per_1000`],
  };
}
export function estimate(
  d: Snapshot,
  model: Model | "all",
  reach: number,
  o: Options = DEFAULT,
) {
  if (model === "all") {
    if (reach !== 100) throw new Error("All targeting requires 100% reach.");
    return lookup(d, "all_minus_none", o);
  }
  if (!MODELS.includes(model) || !REACHES.includes(reach as 10))
    throw new Error("Choose a saved ranking and reach.");
  return lookup(d, `${model}:${reach / 10}_minus_none`, o);
}
export function paired(
  d: Snapshot,
  first: Model,
  second: Model,
  reach: number,
  o: Options = DEFAULT,
) {
  if (
    !MODELS.includes(first) ||
    !MODELS.includes(second) ||
    first === second ||
    !REACHES.includes(reach as 10)
  )
    throw new Error("Choose two different saved rankings.");
  const [a, b] = [first, second].sort(
    (a, b) => MODELS.indexOf(a) - MODELS.indexOf(b),
  );
  const e = lookup(d, `${a}_minus_${b}:${reach / 10}`, o);
  return first === a ? e : { value: -e.value, low: -e.high, high: -e.low };
}
export function observed(d: Snapshot) {
  const s = d.support;
  const control = s.control_visits / (s.control_visits + s.control_nonvisits);
  const treatment =
    s.treatment_visits / (s.treatment_visits + s.treatment_nonvisits);
  return { control, treatment, pp: 100 * (treatment - control) };
}
