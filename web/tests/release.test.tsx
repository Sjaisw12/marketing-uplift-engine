import { readFileSync } from "node:fs";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect } from "vitest";
import { Experience, TeachingDemo } from "../src/App";
import {
  DEFAULT,
  estimate,
  paired,
  validateSnapshot,
  type Model,
  type Options,
} from "../src/data";
import { illustrate } from "../src/budget";
import { SITE, META, shareTags, validateSiteConfig } from "../src/site";
import reference from "./python-scientific-reference.json";
const data = validateSnapshot(
  JSON.parse(readFileSync("public/aggregate_results.json", "utf8")),
);
const options = (a: unknown[]): Options => ({
  method: a[0] as Options["method"],
  propensity: a[1] as number,
  uncertainty: a[2] as Options["uncertainty"],
  interval: a[3] as Options["interval"],
});
it.each(reference.estimates.map((r, i) => ({ r, i })))(
  "matches Python displayed estimate/interval $i",
  ({ r }) => {
    const [model, reach, ...rest] = r;
    const value = estimate(
      data,
      model as Model | "all",
      reach as number,
      options(rest),
    );
    expect(value).toEqual({ value: r[6], low: r[7], high: r[8] });
  },
);
it.each(reference.pairs.map((r, i) => ({ r, i })))(
  "matches Python paired T-minus-S interval $i",
  ({ r }) => {
    expect(
      paired(
        data,
        "t_learner",
        "s_learner",
        r[0] as number,
        options(r.slice(1)),
      ),
    ).toEqual({ value: r[5], low: r[6], high: r[7] });
  },
);
it.each(reference.budgets.map((r, i) => ({ r, i })))(
  "matches exact Python Decimal illustration $i",
  ({ r }) => {
    const value = illustrate(
      data,
      r[0] as Model | "none",
      r[1] as number,
      r[2] as number,
      r[3],
      r[4],
      r[5],
      options(r.slice(6)),
    );
    expect(value.assignments).toBe(r[10]);
    for (const [v, expected] of [
      [value.gain, r[11]],
      [value.spend, r[12]],
      [value.net, r[13]],
      [value.unspent, r[14]],
    ] as const)
      expect(v.eq(expected as string)).toBe(true);
    if (r[15] === null) expect(value.bounds).toBeNull();
    else {
      expect(value.bounds![0].eq(r[15] as string)).toBe(true);
      expect(value.bounds![1].eq(r[16] as string)).toBe(true);
    }
  },
);
it("explains observed rates without implying absolute count comparisons or new advertising", () => {
  render(<Experience data={data} />);
  expect(
    screen.getByText("The ad-assigned group had a higher observed visit rate."),
  ).toBeTruthy();
  expect(screen.getByText(/Historical assignments are not/)).toBeTruthy();
  expect(screen.getByText(/portfolio site deploys no ads/)).toBeTruthy();
  expect(
    screen.queryByText("More visits in the assigned-ad group."),
  ).toBeNull();
});
it("uses selected reach and saved numbers in the plain-language unit example", async () => {
  render(<Experience data={data} />);
  const user = userEvent.setup();
  const compare = document.getElementById("compare")!;
  await user.click(within(compare).getByRole("button", { name: "30%" }));
  const example = compare.querySelector(".unit-example")!;
  expect(example.textContent).toContain("300 assignments");
  expect(example.textContent).toContain(
    estimate(data, "s_learner", 30, DEFAULT).value.toLocaleString("en-US", {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    }),
  );
  expect(example.textContent).toContain("not a conversion percentage");
  expect(example.textContent).toContain("validated forecast");
});
it("offers explicit conceptual ON/OFF instructions and truthfully attributes the creator", () => {
  render(<Experience data={data} />);
  expect(screen.getByText(/switch advertising OFF, then ON/)).toBeTruthy();
  expect(
    screen.getByRole("link", { name: /Sanyam Jaiswal/ }).getAttribute("href"),
  ).toBe("https://github.com/Sjaisw12");
  expect(screen.queryByText("Professional profile")).toBeNull();
  expect(screen.queryByText(/LinkedIn/)).toBeNull();
});
it("supports the teaching toggle by keyboard without a recommendation side effect", async () => {
  render(<TeachingDemo />);
  const user = userEvent.setup();
  const button = screen.getByRole("button", { name: /Advertising on/ });
  button.focus();
  await user.keyboard(" ");
  expect(screen.getByText("A visit without advertising.")).toBeTruthy();
});
it("omits unapproved canonical, image and professional-profile URLs locally", () => {
  expect(SITE.professionalProfileUrl).toBeNull();
  expect(SITE.productionUrl).toBeNull();
  const meta = shareTags(SITE);
  expect(meta.canonical).toBeNull();
  expect(
    meta.tags.some(
      (t) => t.attrs.property === "og:image" || t.attrs.property === "og:url",
    ),
  ).toBe(false);
  expect(
    meta.tags.find((t) => t.attrs.property === "og:title")?.attrs.content,
  ).toBe(META.title);
});
it("builds absolute sharing URLs for a synthetic Pages subpath configuration", () => {
  const fixture = {
    ...SITE,
    productionUrl: "https://fixture-owner.github.io/study/",
  };
  const meta = shareTags(fixture);
  expect(meta.canonical).toBe(fixture.productionUrl);
  expect(
    meta.tags.find((t) => t.attrs.property === "og:image")?.attrs.content,
  ).toBe("https://fixture-owner.github.io/study/social-preview.png");
});
it.each([
  "http://localhost:8000/",
  "https://example.com/",
  "https://host.invalid/",
  "https://user:password@host.org/",
  "https://host.org/?token=x",
  "https://host.org/no-slash",
])("rejects unsafe or placeholder production URL %s", (url) => {
  expect(() => validateSiteConfig({ ...SITE, productionUrl: url })).toThrow();
});
it("has a valid 1200×630 PNG, favicon and an explicit social-image allowlist", () => {
  const png = readFileSync("public/social-preview.png");
  expect(png.subarray(0, 8).toString("hex")).toBe("89504e470d0a1a0a");
  expect(png.readUInt32BE(16)).toBe(1200);
  expect(png.readUInt32BE(20)).toBe(630);
  expect(readFileSync("public/favicon.svg", "utf8")).toContain("<svg");
});

it("rejects unexpected configuration fields before anything can be bundled", () => {
  expect(() =>
    validateSiteConfig({
      ...SITE,
      privateKey: "not-a-real-key",
    } as typeof SITE),
  ).toThrow("Unexpected metadata fields");
});
