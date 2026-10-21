import { useEffect, useState, type ReactNode } from "react";
import { illustrate } from "./budget";
import {
  COLORS,
  DEFAULT,
  LABELS,
  MODELS,
  REACHES,
  SCENARIOS,
  SNAPSHOT_SHA256,
  estimate,
  loadSnapshot,
  observed,
  paired,
  type Model,
  type Options,
  type Snapshot,
} from "./data";
import { PolicyChart, SensitivityChart, fmt, fmtDecimal } from "./Charts";
const REPO = "https://github.com/Sjaisw12/marketing-uplift-engine";
const NAV = [
  ["story", "The question"],
  ["study", "The study"],
  ["compare", "The evidence"],
  ["lab", "Decision Lab"],
  ["decision", "The decision"],
  ["science", "The science"],
] as const;
const EXPLAIN: Record<Model, { title: string; text: string }> = {
  random: {
    title: "Pick at random",
    text: "Choose users by a frozen random priority. The benchmark for asking whether a learned ranking adds anything.",
  },
  response: {
    title: "Predict a visit",
    text: "Rank people by how likely they are to visit when assigned advertising. They might have visited anyway.",
  },
  s_learner: {
    title: "One model, two worlds",
    text: "Use one model to predict a visit with and without assignment to advertising. Rank the difference.",
  },
  t_learner: {
    title: "Two models, two worlds",
    text: "Use separate treatment and control models to predict visit probabilities. Rank their difference.",
  },
};
export function teaching(kind: number, ad: boolean) {
  return kind === 0
    ? { visit: true, extra: false }
    : kind === 1
      ? { visit: ad, extra: ad }
      : { visit: false, extra: false };
}
function Arrow({ down = false }: { down?: boolean }) {
  return (
    <svg
      className="icon-arrow"
      viewBox="0 0 20 20"
      aria-hidden="true"
      focusable="false"
    >
      <path d={down ? "M3 3l14 14M3 17h14V3" : "M3 17L17 3M3 3h14v14"} />
    </svg>
  );
}
function Chapter({ n, label }: { n: string; label: string }) {
  return (
    <div className="chapter">
      <span>{n}</span>
      {label}
    </div>
  );
}
function Note({
  children,
  tone = "plain",
}: {
  children: ReactNode;
  tone?: string;
}) {
  return <aside className={`note ${tone}`}>{children}</aside>;
}
function Assumptions({
  id,
  value,
  onChange,
}: {
  id: string;
  value: Options;
  onChange: (value: Options) => void;
}) {
  return (
    <details className="assumptions">
      <summary>
        Inspect saved evaluation assumptions <span>Technical controls</span>
      </summary>
      <p>
        These are predeclared scenarios, not known individual assignment
        probabilities. The reference assumes e=0.85.
      </p>
      <div className="control-grid">
        <label htmlFor={`${id}-method`}>
          Evaluation approach
          <select
            id={`${id}-method`}
            value={value.method}
            onChange={(e) =>
              onChange({
                ...value,
                method: e.target.value as Options["method"],
              })
            }
          >
            <option value="dr">Shared DR · models + reweighting</option>
            <option value="ipw">IPW · reweighting</option>
          </select>
        </label>
        <label htmlFor={`${id}-propensity`}>
          Assumed treatment propensity
          <select
            id={`${id}-propensity`}
            value={value.propensity}
            onChange={(e) =>
              onChange({ ...value, propensity: Number(e.target.value) })
            }
          >
            {SCENARIOS.map((e) => (
              <option key={e} value={e}>
                {e}
                {e === 0.85 ? " · reference" : ""}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor={`${id}-interval`}>
          Saved interval
          <select
            id={`${id}-interval`}
            value={value.interval}
            onChange={(e) =>
              onChange({
                ...value,
                interval: e.target.value as Options["interval"],
              })
            }
          >
            <option value="simultaneous">
              95% simultaneous · 765 comparisons
            </option>
            <option value="pointwise">95% pointwise · one comparison</option>
          </select>
        </label>
        <label htmlFor={`${id}-uncertainty`}>
          Conditioning assumption
          <select
            id={`${id}-uncertainty`}
            value={value.uncertainty}
            onChange={(e) =>
              onChange({
                ...value,
                uncertainty: e.target.value as Options["uncertainty"],
              })
            }
          >
            <option value="iid">IID working model · primary</option>
            <option value="stratified">
              Fixed-stratum sensitivity · secondary
            </option>
          </select>
        </label>
      </div>
      {value.interval === "pointwise" && (
        <Note tone="caution">
          Pointwise intervals do not provide simultaneous coverage across
          comparisons.
        </Note>
      )}
      {value.uncertainty === "stratified" && (
        <Note tone="caution">
          Secondary sensitivity fixes observed treatment × visit composition.
          Zero conditional variance is not causal certainty; this does not
          replace primary IID uncertainty.
        </Note>
      )}
    </details>
  );
}
function ScenarioLabel({ options }: { options: Options }) {
  return (
    <p className="micro scenario-label">
      Saved {options.method === "dr" ? "shared DR" : "IPW"} · assumed e=
      {options.propensity} · {options.interval} 95% ·{" "}
      {options.uncertainty === "iid"
        ? "IID working model"
        : "fixed-stratum sensitivity"}
    </p>
  );
}
function Reach({
  value,
  onChange,
  disabled = false,
}: {
  value: number;
  onChange: (n: number) => void;
  disabled?: boolean;
}) {
  return (
    <fieldset className="reach">
      <legend>
        Advertising reach <span>share of the eligible audience</span>
      </legend>
      <div>
        {REACHES.map((r) => (
          <button
            type="button"
            key={r}
            disabled={disabled}
            aria-pressed={!disabled && r === value}
            onClick={() => onChange(r)}
          >
            {r}%
          </button>
        ))}
      </div>
    </fieldset>
  );
}
export function TeachingDemo() {
  const [kind, setKind] = useState(0),
    [ad, setAd] = useState(true);
  const result = teaching(kind, ad);
  return (
    <div className="teaching-demo">
      <div className="demo-top">
        <span className="mono">A THOUGHT EXPERIMENT</span>
        <span className="live-dot">Not a real person</span>
      </div>
      <div
        className="customer-tabs"
        role="group"
        aria-label="Hypothetical customer type"
      >
        {["Visits anyway", "Could be persuaded", "Would not respond"].map(
          (name, i) => (
            <button
              type="button"
              key={name}
              aria-pressed={kind === i}
              onClick={() => setKind(i)}
            >
              {name}
            </button>
          ),
        )}
      </div>
      <svg
        className="teaching-art"
        viewBox="0 0 520 260"
        role="img"
        aria-label={`Conceptual customer: ${result.visit ? "visits" : "does not visit"} ${ad ? "with" : "without"} an ad. Not a real classification.`}
      >
        <defs>
          <pattern
            id="dots"
            x="0"
            y="0"
            width="20"
            height="20"
            patternUnits="userSpaceOnUse"
          >
            <circle cx="1" cy="1" r="1" fill="#c8c2b5" />
          </pattern>
          <marker
            id="arrow"
            markerWidth="8"
            markerHeight="8"
            refX="5"
            refY="3"
            orient="auto"
          >
            <path d="M0,0 L6,3 L0,6" fill="none" stroke="#71837a" />
          </marker>
        </defs>
        <rect width="520" height="260" fill="url(#dots)" />
        <circle cx="116" cy="130" r="68" fill="#f4eee2" stroke="#c9c2b5" />
        <circle cx="116" cy="107" r="23" fill="#183831" />
        <path d="M72 170c0-55 88-55 88 0" fill="#183831" />
        <path
          d="M190 130 H326"
          stroke="#71837a"
          strokeWidth="2"
          strokeDasharray={ad ? "0" : "5 7"}
          markerEnd="url(#arrow)"
        />
        <g className={ad ? "ad-stamp" : "ad-stamp off"}>
          <rect
            x="220"
            y="96"
            width="62"
            height="67"
            rx="5"
            fill="#ae492d"
            transform="rotate(-8 251 130)"
          />
          <text
            x="251"
            y="127"
            textAnchor="middle"
            fill="#fff8ee"
            fontSize="22"
            fontWeight="700"
          >
            AD
          </text>
          <text
            x="251"
            y="147"
            textAnchor="middle"
            fill="#fff8ee"
            fontSize="11"
          >
            assignment
          </text>
        </g>
        <rect
          x="350"
          y="78"
          width="120"
          height="105"
          rx="9"
          fill={result.visit ? "#e0ebe0" : "#eee8dd"}
          stroke="#a4b1a3"
        />
        <path d="M367 94h86M367 103h42" stroke="#a4b1a3" strokeWidth="3" />
        <text
          x="410"
          y="145"
          textAnchor="middle"
          fill="#183831"
          fontSize="25"
          fontFamily="Georgia"
        >
          {result.visit ? "A visit." : "No visit."}
        </text>
        <text x="116" y="223" textAnchor="middle" fill="#53645c" fontSize="13">
          A hypothetical person
        </text>
        <text x="410" y="223" textAnchor="middle" fill="#53645c" fontSize="13">
          The website
        </text>
      </svg>
      <button
        type="button"
        className="toggle-ad"
        aria-pressed={ad}
        onClick={() => setAd(!ad)}
      >
        <span className={`switch ${ad ? "on" : ""}`} aria-hidden="true" />
        {ad ? "Advertising on" : "Advertising off"}
        <small>Click to compare</small>
      </button>
      <div className="demo-result" aria-live="polite">
        <strong>
          {result.extra
            ? "An additional visit—in this example."
            : ad && result.visit
              ? "Same visit. Extra advertising spend."
              : !ad && result.visit
                ? "A visit without advertising."
                : ad
                  ? "Advertising spend. No additional visit."
                  : "No advertising. No visit."}
        </strong>
        <p>
          {kind === 0
            ? "They were already going to visit. A visit-prediction model could find them attractive, even though the ad adds nothing here."
            : kind === 1
              ? "This example changes when the ad is switched on. That is the kind of incrementality an advertiser would want to understand."
              : "This example does not respond either way. Advertising does not guarantee an additional visit."}
        </p>
      </div>
      <p className="micro">
        Conceptual examples only. Not real classified individuals; individual
        causal effects were not observed. No monetary costs or response rates
        are inferred from this illustration.
      </p>
    </div>
  );
}
function Study({ data }: { data: Snapshot }) {
  const rates = observed(data);
  return (
    <section id="study" className="section study">
      <div className="section-intro">
        <Chapter n="01" label="A real study, carefully separated" />
        <h2>
          A big dataset.
          <br />
          <em>A more careful question.</em>
        </h2>
        <p>
          Could learned targeting rules identify more additional visits than
          simply picking people at random? This project built and compared those
          rules—then kept the decision separate from the diagnostics.
        </p>
      </div>
      <div className="study-spread">
        <div className="big-records">
          <span className="mono">CORRECTED CRITEO UPLIFT V2.1</span>
          <strong>{data.population.source_rows.toLocaleString("en-US")}</strong>
          <p>benchmark records—not a claim about unique customers.</p>
        </div>
        <div
          className="partition"
          role="img"
          aria-label="11,882,653 development records and 2,096,939 held-out records"
        >
          <span style={{ width: "85%" }}>Development · 85%</span>
          <span style={{ width: "15%" }}>15%</span>
        </div>
        <div className="partition-notes">
          <div>
            <b>{data.population.development_rows.toLocaleString("en-US")}</b>
            <h3>The practice ground</h3>
            <p>
              Development records: build the models, compare methods and freeze
              the decision framework. Five existing splits were reused.
            </p>
          </div>
          <div>
            <b>{data.population.holdout_rows.toLocaleString("en-US")}</b>
            <h3>The final exam</h3>
            <p>
              Held-out records: evaluated once, after models and policies were
              locked. No choosing a new winner after seeing the answers.
            </p>
          </div>
        </div>
        <div className="rate-story">
          <div>
            <span className="kicker">WHAT WAS OBSERVED</span>
            <h3>More visits in the assigned-ad group.</h3>
            <p>
              That is a description of the released sample. It is not, by
              itself, proof that advertising caused the difference.
            </p>
            <div className="rate-gap">
              <strong>
                {fmt(rates.pp, 4)} <small>percentage points</small>
              </strong>
              <span>
                Descriptive difference—not a relative percentage change.
              </span>
            </div>
          </div>
          <div
            className="rates"
            aria-label="Observed assignment-arm visit rates"
          >
            {[
              ["Control · not assigned ads", rates.control, "#657577"],
              ["Treatment · assigned ads", rates.treatment, "#ae492d"],
            ].map(([name, rate, color]) => (
              <div className="rate-row" key={String(name)}>
                <div>
                  <span>{name}</span>
                  <strong>{fmt(Number(rate) * 100, 4)}%</strong>
                </div>
                <div className="rate-track">
                  <span
                    style={{
                      width: `${((Number(rate) * 100) / 5) * 100}%`,
                      background: String(color),
                    }}
                  />
                </div>
              </div>
            ))}
            <div className="rate-scale">
              <span>0%</span>
              <span>5% observed visit rate</span>
            </div>
            <p className="micro">
              Visit counts: control{" "}
              {data.support.control_visits.toLocaleString("en-US")} /{" "}
              {(
                data.support.control_visits + data.support.control_nonvisits
              ).toLocaleString("en-US")}
              ; treatment{" "}
              {data.support.treatment_visits.toLocaleString("en-US")} /{" "}
              {(
                data.support.treatment_visits + data.support.treatment_nonvisits
              ).toLocaleString("en-US")}
              .
            </p>
          </div>
        </div>
        <Note>
          Assignment is not actual ad exposure. Criteo pools experiments and
          uses non-uniform privacy subsampling. Original experiment-specific
          assignment probabilities and experiment identifiers are unavailable.
        </Note>
      </div>
    </section>
  );
}
function Compare({ data }: { data: Snapshot }) {
  const [selected, setSelected] = useState<Model>("s_learner"),
    [reach, setReach] = useState(20),
    [options, setOptions] = useState<Options>(DEFAULT);
  const e = estimate(data, selected, reach, options),
    ts = paired(data, "t_learner", "s_learner", reach, options);
  return (
    <section id="compare" className="section compare">
      <Chapter n="02" label="Four ways to choose. One fair comparison." />
      <div className="section-heading">
        <h2>
          Likely to visit?
          <br />
          <em>Or likely to visit because?</em>
        </h2>
        <p>
          A good prediction is not automatically a good advertising decision.
          Compare four frozen rankings at the same advertising reach.
        </p>
      </div>
      <div
        className="model-tabs"
        role="group"
        aria-label="Explore a frozen ranking"
      >
        {MODELS.map((m) => (
          <button
            type="button"
            aria-pressed={selected === m}
            key={m}
            onClick={() => setSelected(m)}
          >
            <i style={{ background: COLORS[m] }} />
            <span>
              {EXPLAIN[m].title}
              <small>{LABELS[m]}</small>
            </span>
          </button>
        ))}
      </div>
      <div className="model-explanation">
        <span className="pill">{LABELS[selected]}</span>
        <p>
          {EXPLAIN[selected].text} These are model-based rankings, not observed
          individual causal effects.
        </p>
      </div>
      <div className="evidence-board">
        <div className="board-top">
          <Reach value={reach} onChange={setReach} />
          <div className="selected-estimate">
            <span>Saved estimate · {LABELS[selected]}</span>
            <strong>
              {fmt(e.value)}
              <small> / 1,000</small>
            </strong>
            <span>additional visits per 1,000 eligible records</span>
          </div>
        </div>
        <PolicyChart
          data={data}
          reach={reach}
          options={options}
          selected={selected}
        />
        <div className="chart-caption">
          <span className="pill neutral">Secondary diagnostics</span>
          <p>
            The dot is the saved estimate; the whisker is its saved{" "}
            {options.interval} interval. Zero means no gain relative to no
            targeting. Higher dots do not establish a best causal policy.
          </p>
        </div>
        <ScenarioLabel options={options} />
        <details>
          <summary>What does “per 1,000 eligible” mean?</summary>
          <p>
            The denominator includes everyone eligible, including people the
            policy would not target. At {reach}% reach, a hypothetical
            1,000-person audience would have {reach * 10} assignments. The saved
            gain is still reported per 1,000 eligible—not per 1,000 ads.
          </p>
        </details>
        <Assumptions id="compare" value={options} onChange={setOptions} />
        <details>
          <summary>Exact saved values & reference policies</summary>
          <div className="table-scroll">
            <table>
              <caption>
                {reach}% reach · {options.interval} intervals · visits per 1,000
                eligible
              </caption>
              <thead>
                <tr>
                  <th>Ranking</th>
                  <th>Estimate</th>
                  <th>Lower</th>
                  <th>Upper</th>
                </tr>
              </thead>
              <tbody>
                {MODELS.map((m) => {
                  const v = estimate(data, m, reach, options);
                  return (
                    <tr key={m}>
                      <th>{LABELS[m]}</th>
                      <td>{fmt(v.value, 6)}</td>
                      <td>{fmt(v.low, 6)}</td>
                      <td>{fmt(v.high, 6)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <p>
            No targeting: zero gain relative to itself by identity, with no
            statistical interval. All-targeting anchor:{" "}
            {fmt(estimate(data, "all", 100, options).value)} [
            {fmt(estimate(data, "all", 100, options).low)},{" "}
            {fmt(estimate(data, "all", 100, options).high)}]. The 100% anchor
            uses a different budget.
          </p>
        </details>
      </div>
      <div className="paired-note">
        <span className="mono">A DIRECT S–T COMPARISON</span>
        <p>
          T minus S at {reach}%: <strong>{fmt(ts.value)}</strong>, saved{" "}
          {options.interval} interval{" "}
          <strong>
            [{fmt(ts.low)}, {fmt(ts.high)}]
          </strong>{" "}
          visits per 1,000 eligible. Compare this paired difference, not overlap
          of separate intervals. An interval containing zero is not proof of
          equivalence.
        </p>
      </div>
      <Note tone="caution">
        All intervals are nominal working-model intervals conditional on fitted
        models and fixed policies. Simultaneous coverage retains the original
        765-comparison family, even when only a few results are displayed.
        Causal interpretation additionally requires unverified assumptions.
      </Note>
    </section>
  );
}
function DecisionLab({ data }: { data: Snapshot }) {
  const [model, setModel] = useState<Model | "none">("none"),
    [reach, setReach] = useState(20),
    [options, setOptions] = useState<Options>(DEFAULT),
    [inputs, setInputs] = useState({
      population: "100000",
      budget: "500",
      cost: "0.01",
      value: "1",
    });
  let result;
  let error = "";
  try {
    if (!inputs.population.trim())
      throw new Error("Complete the eligible audience size.");
    result = illustrate(
      data,
      model,
      model === "none" ? 0 : reach,
      Number(inputs.population),
      inputs.cost,
      inputs.value,
      inputs.budget,
      options,
    );
  } catch (e) {
    error = e instanceof Error ? e.message : "Invalid hypothetical inputs.";
  }
  return (
    <section id="lab" className="section lab">
      <Chapter n="03" label="Your assumptions. Illustrative arithmetic." />
      <div className="section-heading">
        <h2>
          Try the numbers.
          <br />
          <em>Keep the question marks.</em>
        </h2>
        <p>
          What might the saved estimates mean for a hypothetical advertising
          budget? Explore the arithmetic, without asking it to make a new
          decision.
        </p>
      </div>
      <Note tone="caution">
        <strong>This is not validated ROI.</strong> Costs, values and transport
        to a new audience are unverified assumptions. No real people are
        selected. Nothing here replaces the frozen no-targeting recommendation.
      </Note>
      <div className="lab-spread">
        <div className="lab-inputs">
          <div className="lab-panel-title">
            <span className="mono">01 / SET THE SCENARIO</span>
            <span className="pill neutral">Hypothetical</span>
          </div>
          <label htmlFor="lab-policy">
            Policy to illustrate
            <select
              id="lab-policy"
              value={model}
              onChange={(e) => setModel(e.target.value as Model | "none")}
            >
              <option value="none">No targeting · frozen primary</option>
              {MODELS.map((m) => (
                <option key={m} value={m}>
                  {LABELS[m]} · exploratory
                </option>
              ))}
            </select>
          </label>
          <p className="micro">
            Start at zero spend. To explore an alternative, choose a diagnostic
            ranking above, then a saved reach below.
          </p>
          <Reach
            value={reach}
            onChange={setReach}
            disabled={model === "none"}
          />
          <div className="control-grid">
            {(
              [
                [
                  "population",
                  "Eligible audience size",
                  "1",
                  "1000000000",
                  "1",
                ],
                [
                  "budget",
                  "Hypothetical budget · units",
                  "0",
                  "1000000000000",
                  ".01",
                ],
                [
                  "cost",
                  "Cost per assignment · units",
                  "0",
                  "1000000000000",
                  ".01",
                ],
                [
                  "value",
                  "Value per additional visit · units",
                  "0",
                  "1000000000000",
                  ".1",
                ],
              ] as const
            ).map(([key, label, min, max, step]) => (
              <label key={key} htmlFor={`lab-${key}`}>
                {label}
                <input
                  id={`lab-${key}`}
                  type="number"
                  min={min}
                  max={max}
                  step={step}
                  value={inputs[key]}
                  onChange={(e) =>
                    setInputs({ ...inputs, [key]: e.target.value })
                  }
                />
              </label>
            ))}
          </div>
          <Assumptions id="lab" value={options} onChange={setOptions} />
        </div>
        <div className="lab-receipt" aria-live="polite">
          <div className="lab-panel-title">
            <span className="mono">02 / READ THE ILLUSTRATION</span>
            <span className="receipt-mark" aria-hidden="true">
              <Arrow />
            </span>
          </div>
          <h3>
            {model === "none"
              ? "No targeting. No spend."
              : `${LABELS[model]} · ${reach}% reach`}
          </h3>
          <p>
            {model === "none"
              ? "The frozen primary policy, shown as a mathematical baseline."
              : "Exploratory arithmetic only. This is not a newly selected policy."}
          </p>
          {error ? (
            <div role="alert" className="lab-error">
              {error}
            </div>
          ) : (
            result && (
              <>
                <dl className="receipt-numbers">
                  <div>
                    <dt>Advertising assignments</dt>
                    <dd>{result.assignments.toLocaleString("en-US")}</dd>
                  </div>
                  <div>
                    <dt>Estimated additional visits</dt>
                    <dd>{fmtDecimal(result.gain, 3)}</dd>
                  </div>
                  <div>
                    <dt>Illustrative spend</dt>
                    <dd>
                      {fmtDecimal(result.spend, 2)} <small>units</small>
                    </dd>
                  </div>
                  <div>
                    <dt>Illustrative incremental value</dt>
                    <dd>
                      {fmtDecimal(result.incrementalValue, 2)}{" "}
                      <small>units</small>
                    </dd>
                  </div>
                  <div className="net-line">
                    <dt>Hypothetical net benefit</dt>
                    <dd>
                      {fmtDecimal(result.net, 2)} <small>units</small>
                    </dd>
                  </div>
                  <div>
                    <dt>Remaining budget</dt>
                    <dd>
                      {fmtDecimal(result.unspent, 2)} <small>units</small>
                    </dd>
                  </div>
                </dl>
                <div
                  className="allocation"
                  aria-label={`Illustrative spend ${result.spend.toFixed(2)} units; remaining ${result.unspent.toFixed(2)} units`}
                >
                  <span
                    style={{
                      width: result.spend.add(result.unspent).isZero()
                        ? "0%"
                        : `${result.spend.div(result.spend.add(result.unspent)).mul(100).toNumber()}%`,
                    }}
                  />
                </div>
                <div className="allocation-labels">
                  <span>Spend</span>
                  <span>Unspent budget</span>
                </div>
                {result.bounds ? (
                  <p className="micro">
                    Scaled saved benchmark bounds: [
                    {fmtDecimal(result.bounds[0], 3)},{" "}
                    {fmtDecimal(result.bounds[1], 3)}] additional visits. These
                    multiply the saved interval by audience / 1,000; they are
                    not a new-population confidence or prediction interval.
                    Transport uncertainty is omitted. Actual illustrative reach:{" "}
                    {fmtDecimal(result.actualReach.mul(100), 4)}% after rounding
                    assignments up.
                  </p>
                ) : (
                  <p className="micro">
                    Zero relative gain is an identity, not evidence that
                    advertising is ineffective or no targeting is optimal. No
                    statistical CI is implied.
                  </p>
                )}
                <ScenarioLabel options={options} />
              </>
            )
          )}
        </div>
      </div>
      <details>
        <summary>Check the arithmetic & its limits</summary>
        <p>
          Assignments = ceiling(audience × saved reach). Spend = assignments ×
          cost. Additional visits = audience × saved gain / 1,000. Incremental
          value = additional visits × hypothetical value. Net benefit =
          incremental value − spend. The gain is not multiplied by targeted
          count. Unaffordable scenarios stop; there is no automatic trimming or
          interpolation. Negative values are retained. Currency units are
          hypothetical, not observed Criteo prices or revenues.
        </p>
      </details>
    </section>
  );
}
function Decision({ data }: { data: Snapshot }) {
  const options = DEFAULT;
  const reference = (method: "dr" | "ipw") =>
    SCENARIOS.map(
      (e) =>
        estimate(data, "all", 100, { ...options, method, propensity: e }).value,
    );
  const ipw = reference("ipw"),
    dr = reference("dr");
  return (
    <section id="decision" className="decision-section">
      <div className="section-inner">
        <Chapter n="04" label="The decision was frozen before the reveal" />
        <div className="decision-statement">
          <div>
            <span className="pill">FROZEN PRIMARY RECOMMENDATION</span>
            <h2>
              Sometimes the most
              <br />
              defensible spend
              <br />
              is <em>no spend.</em>
            </h2>
          </div>
          <div className="decision-zero">
            <strong>0</strong>
            <span>
              advertising assignments
              <br />
              under the retained primary policy
            </span>
          </div>
        </div>
        <div className="decision-columns">
          <h3>
            Positive diagnostics.
            <br />A conservative decision.
            <br />
            Both can be true.
          </h3>
          <div>
            <p>
              The prespecified decision framework abstained in{" "}
              <strong>all 40 development scenario/split combinations</strong>.
              That conservative rule was frozen before the one-time final
              evaluation.
            </p>
            <p>
              Some secondary holdout estimates were positive. They were
              diagnostic comparisons—not permission to choose a new model, reach
              or spending rule after seeing the final results.
            </p>
            <p className="decision-quote">
              “An estimate that looks profitable is not enough by itself to
              justify spending.”
            </p>
            <p>
              This does not establish that advertising is ineffective or that no
              targeting is globally optimal. It demonstrates evidence quality
              and decision discipline, not a production-ready targeting service.
            </p>
          </div>
        </div>
        <div className="sensitivity-paper">
          <div className="section-heading">
            <h3>What if the assignment assumption changes?</h3>
            <p>
              The saved all-targeting reference illustrates why the assumptions
              matter. Five discrete scenarios; no interpolation.
            </p>
          </div>
          <SensitivityChart data={data} options={options} />
          <div className="sensitivity-insights">
            <div>
              <span className="mono">IPW · REWEIGHTING</span>
              <strong>
                {fmt(Math.min(...ipw))} → {fmt(Math.max(...ipw))}
              </strong>
              <p>
                Range of five saved point estimates per 1,000 eligible. IPW
                changes substantially across the assumed propensities.
              </p>
            </div>
            <div>
              <span className="mono">SHARED DR · MODELS + REWEIGHTING</span>
              <strong>
                {fmt(Math.min(...dr))} → {fmt(Math.max(...dr))}
              </strong>
              <p>
                Comparatively stable in this saved reference. Stability does not
                verify identification or correct nuisance models.
              </p>
            </div>
          </div>
          <p className="micro">
            Assumed e: 0.80, 0.825, 0.85, 0.875, 0.90. Shared DR and IPW; IID,
            saved simultaneous 95% intervals, original 765-comparison family.
            Ranges above are not intervals. These scenarios are not a calibrated
            uncertainty distribution.
          </p>
        </div>
        <div className="decision-bottom">
          <b>What a marketing team can take away</b>
          <p>
            A disciplined way to distinguish likely response from incremental
            impact, compare policies fairly, expose assumption sensitivity and
            avoid making a spending decision from a point estimate alone.
          </p>
        </div>
      </div>
    </section>
  );
}
function Science({ data }: { data: Snapshot }) {
  return (
    <section id="science" className="section science">
      <Chapter n="05" label="For the curious. And the technical." />
      <div className="section-heading">
        <h2>
          Open the notebook.
          <br />
          <em>Inspect the reasoning.</em>
        </h2>
        <p>
          The introductory story is simple. The identification problem is not.
          Here is the methodology behind the saved results, and what it cannot
          establish.
        </p>
      </div>
      <div className="science-grid">
        <div className="science-index">
          <span className="mono">EVIDENCE, NOT A BLACK BOX</span>
          <p>
            Corrected dataset.
            <br />
            Frozen partitions.
            <br />
            Locked recipes.
            <br />
            One final evaluation.
          </p>
          <a
            href={`${REPO}/blob/main/docs/CASE_STUDY.md`}
            target="_blank"
            rel="noreferrer"
          >
            Read the case study <Arrow />
          </a>
          <a
            href={`${REPO}/blob/main/docs/MODEL_CARD.md`}
            target="_blank"
            rel="noreferrer"
          >
            Inspect the model card <Arrow />
          </a>
          <a href={REPO} target="_blank" rel="noreferrer">
            Source & research documentation <Arrow />
          </a>
        </div>
        <div className="science-details">
          <details open>
            <summary>Data, provenance & the one-time holdout</summary>
            <p>
              Corrected Criteo Uplift v2.1:{" "}
              {data.population.source_rows.toLocaleString("en-US")} records.
              Joint treatment × visit stratification created a 15% final holdout
              and five frozen 80/20 development re-splits. Overlapping
              development splits are not independent experiments. Row
              identifiers and memberships were preserved; no deduplication was
              used to remove repeated vectors.
            </p>
            <p>
              Final models were refit only on development records under
              predetermined recipes. Owner-signed approvals, a fixed receipt,
              durable journal, sealed predictions and independently restored
              encrypted backup preceded one-time outcome evaluation. That
              evaluation is complete and closed. This static site can only read
              the approved public aggregate snapshot.
            </p>
            <p className="micro">
              Snapshot SHA-256 <code>{SNAPSHOT_SHA256}</code>
            </p>
            <p className="micro">
              Final result manifest{" "}
              <code>{data.provenance.result_manifest_sha256}</code>
            </p>
          </details>
          <details>
            <summary>Response, S-learner & T-learner</summary>
            <p>
              Treated-response LightGBM predicts visits among treatment-assigned
              records. The S-learner uses one outcome model with a separate
              treatment intervention indicator and contrasts predictions at 1
              and 0. The T-learner contrasts separate arm-model predictions.
              Only f0–f11 were user predictors; exposure, outcomes and row
              identifiers were excluded. Rankings are not observed individual
              treatment effects. No model is shipped with this website.
            </p>
          </details>
          <details>
            <summary>IPW, shared DR & identification</summary>
            <p>
              For a fixed policy π(X), saved gains are differences in policy
              value relative to no targeting. Under assumed constant e, IPW gain
              averages π(X)[TY/e − (1−T)Y/(1−e)]. Shared DR adds the frozen
              nuisance difference m₁(X)−m₀(X) and uses residual reweighting:
              π(X)[m₁−m₀ + T(Y−m₁)/e − (1−T)(Y−m₀)/(1−e)]. This site does not
              run those estimators; it selects saved aggregate rows.
            </p>
            <p>
              DR's double-robustness property requires causal identification and
              appropriate nuisance correctness. It does not automatically remove
              privacy selection, hidden experiment-specific assignment
              probabilities, dependence or interference. Assignment effects are
              not treatment-on-the-treated exposure effects. Five constant
              propensity scenarios are assumptions, not verified individual
              probabilities or a statistical distribution.
            </p>
          </details>
          <details>
            <summary>765 comparisons, paired uncertainty & saved grids</summary>
            <p>
              Saved intervals use 2,000 paired Gaussian-multiplier draws, with a
              predeclared family of 765 diagnostic contrasts. They are nominal
              working-model intervals conditional on fitted models and fixed
              policies—not exact randomization intervals or an ordinary row
              bootstrap. The family includes nuisance-sensitivity contrasts not
              individually selectable here. Pointwise coverage applies to one
              comparison; simultaneous coverage retains the entire family after
              display filtering.
            </p>
            <p>
              Training uncertainty, outcome-stratification limitations and
              possible dependence remain. Secondary fixed-stratum sensitivity
              conditions on observed treatment × visit composition; it does not
              replace the primary IID analysis. T-minus-S comparisons are
              paired, not inferred from overlaps of separate intervals.
              Reference e=0.85 simultaneous S/T contrasts include zero; that is
              not equivalence. Any grid-based areas at fixed reach points are
              not conventional full-prefix AUUC/Qini. The website does not
              calculate curve areas.
            </p>
          </details>
          <details>
            <summary>What this project did not establish</summary>
            <p>
              No validated advertiser ROI, revenue or cost savings. No globally
              optimal policy. No proven causal superiority from assumed
              propensities. No evidence that advertising never works. No
              production targeting, individual causal labels, temporal
              deployment validation, or live experiment. Criteo's pooled
              experiments, non-uniform privacy subsampling, unknown assignment
              and lack of verified customer identifiers limit interpretation and
              generalization.
            </p>
          </details>
        </div>
      </div>
    </section>
  );
}
export function Experience({ data }: { data: Snapshot }) {
  const [active, setActive] = useState(() => location.hash.slice(1) || "story");
  useEffect(() => {
    const update = () => setActive(location.hash.slice(1) || "story");
    window.addEventListener("hashchange", update);
    const initial = location.hash.slice(1);
    if (NAV.some(([id]) => id === initial))
      document.getElementById(initial)?.scrollIntoView?.({ block: "start" });
    const observer =
      typeof IntersectionObserver === "undefined"
        ? null
        : new IntersectionObserver(
            (entries) => {
              for (const entry of entries)
                if (entry.isIntersecting) setActive(entry.target.id);
            },
            { rootMargin: "-20% 0px -55% 0px", threshold: 0 },
          );
    for (const [id] of NAV) {
      const element = document.getElementById(id);
      if (element) observer?.observe(element);
    }
    return () => {
      window.removeEventListener("hashchange", update);
      observer?.disconnect();
    };
  }, []);
  return (
    <>
      <a className="skip-link" href="#main">
        Skip to the study experience
      </a>
      <header className="site-header">
        <a
          className="wordmark"
          href="#story"
          aria-label="Marketing Uplift, The Decision Lab home"
        >
          <span className="brand-glyph" aria-hidden="true">
            <i />
            <i />
          </span>
          <span>
            Marketing Uplift<small>THE DECISION LAB</small>
          </span>
        </a>
        <nav aria-label="Study chapters">
          {NAV.map(([id, label]) => (
            <a
              key={id}
              href={`#${id}`}
              aria-current={active === id ? "location" : undefined}
            >
              {label}
            </a>
          ))}
        </nav>
        <span className="demo-badge">OFFLINE RESEARCH / INTERACTIVE STORY</span>
      </header>
      <main id="main">
        <section id="story" className="hero">
          <div className="hero-copy">
            <div className="eyebrow">
              <span /> A STUDY IN ADVERTISING & EVIDENCE
            </div>
            <h1>
              Who should <br />
              <em>actually</em> see <br />
              your next ad?
            </h1>
            <p className="hero-deck">
              Reaching someone likely to visit isn't the same as convincing
              someone to visit.
            </p>
            <p>
              Advertising can spend money on a visit that would have happened
              anyway. This study asks whether machine learning and careful
              evaluation can help us decide whether—and whom—to target.
            </p>
            <a className="button primary" href="#study">
              Explore the study <Arrow down />
            </a>
            <div className="hero-footnote">
              <span>13.98M benchmark records</span>
              <span>Frozen recommendation: no targeting</span>
            </div>
          </div>
          <div className="hero-visual">
            <TeachingDemo />
          </div>
        </section>
        <div className="story-bridge">
          <span className="mono">THE IMPORTANT DIFFERENCE</span>
          <p>
            “Who will visit?”<span aria-hidden="true"> ≠ </span>
            <strong>“Who will visit because of the ad?”</strong>
          </p>
        </div>
        <Study data={data} />
        <Compare data={data} />
        <DecisionLab data={data} />
        <Decision data={data} />
        <Science data={data} />
      </main>
      <footer>
        <div>
          <a className="footer-name" href="#story">
            The Decision Lab <Arrow />
          </a>
          <p>
            A portfolio demonstration of offline advertising decision support.
            <br />
            No live targeting. No new experiments. No production deployment
            guidance.
          </p>
        </div>
        <div>
          <strong>Attribution & licensing</strong>
          <p>
            Criteo AI Lab · Diemert et al. (2018),{" "}
            <em>A Large Scale Benchmark for Uplift Modeling.</em> Criteo-derived
            aggregates and visualizations:{" "}
            <a href="https://creativecommons.org/licenses/by-nc-sa/4.0/">
              CC BY-NC-SA 4.0
            </a>
            . Software: MIT. No endorsement implied.
          </p>
          <a href="https://huggingface.co/datasets/criteo/criteo-uplift">
            Official dataset <Arrow />
          </a>
        </div>
      </footer>
    </>
  );
}
export default function App() {
  const [data, setData] = useState<Snapshot | null>(null),
    [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    loadSnapshot()
      .then((d) => {
        if (active) setData(d);
      })
      .catch(() => {
        if (active) setError(true);
      });
    return () => {
      active = false;
    };
  }, []);
  if (error)
    return (
      <main className="loading" role="alert">
        <span className="mono">THE DECISION LAB</span>
        <h1>Evidence unavailable.</h1>
        <p>
          The approved public snapshot could not be verified. No alternate
          source, private file or execution fallback is permitted.
        </p>
      </main>
    );
  if (!data)
    return (
      <main className="loading" role="status">
        <span className="mono">THE DECISION LAB</span>
        <h1>Evidence before answers.</h1>
        <p>Verifying the frozen public snapshot…</p>
      </main>
    );
  return <Experience data={data} />;
}
