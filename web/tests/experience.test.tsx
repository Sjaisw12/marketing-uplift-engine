import { readFileSync } from "node:fs";
import {
  render,
  screen,
  within,
  waitFor,
  fireEvent,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { it, expect, vi } from "vitest";
import App, { Experience, TeachingDemo, teaching } from "../src/App";
import { validateSnapshot, estimate, DEFAULT } from "../src/data";
import { PolicyChart, SensitivityChart } from "../src/Charts";
const data = validateSnapshot(
  JSON.parse(readFileSync("public/aggregate_results.json", "utf8")),
);
it("teaches all six conceptual customer states without real classifications", async () => {
  for (const kind of [0, 1, 2])
    for (const ad of [false, true]) {
      expect(teaching(kind, ad).extra).toBe(kind === 1 && ad);
    }
  render(<TeachingDemo />);
  expect(screen.getByText("Same visit. Extra advertising spend.")).toBeTruthy();
  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "Could be persuaded" }));
  expect(screen.getByText("An additional visit—in this example.")).toBeTruthy();
  await user.click(screen.getByRole("button", { name: /Advertising on/ }));
  expect(screen.getByText("No advertising. No visit.")).toBeTruthy();
  expect(
    screen.getByText(/individual causal effects were not observed/),
  ).toBeTruthy();
});
it("answers the introductory questions without technical prerequisites", () => {
  render(<Experience data={data} />);
  expect(
    screen.getByRole("heading", {
      name: /Who should actually see your next ad/,
    }),
  ).toBeTruthy();
  expect(screen.getByText(/would have happened anyway/)).toBeTruthy();
  expect(screen.getByText("13,979,592")).toBeTruthy();
  expect(screen.getByText("Frozen recommendation: no targeting")).toBeTruthy();
  expect(screen.getByText("11,882,653")).toBeTruthy();
  expect(screen.getByText("2,096,939")).toBeTruthy();
  expect(
    screen
      .getByRole("link", { name: /Explore the study/ })
      .getAttribute("href"),
  ).toBe("#study");
  expect(screen.getByText(/all 40 development/)).toBeTruthy();
  expect(screen.getByText(/CC BY-NC-SA 4.0/)).toBeTruthy();
});
it("supports hash routing and direct technical entry", async () => {
  window.history.replaceState({}, "", "/#science");
  render(<Experience data={data} />);
  const nav = screen.getByRole("navigation");
  expect(
    within(nav)
      .getByRole("link", { name: "The science" })
      .getAttribute("aria-current"),
  ).toBe("location");
  window.location.hash = "compare";
  fireEvent(window, new HashChangeEvent("hashchange"));
  await waitFor(() =>
    expect(
      within(nav)
        .getByRole("link", { name: "The evidence" })
        .getAttribute("aria-current"),
    ).toBe("location"),
  );
});
it("shows exact chart points, bounds and no interpolated sensitivity curve", () => {
  const { container } = render(
    <PolicyChart
      data={data}
      reach={20}
      options={DEFAULT}
      selected="s_learner"
    />,
  );
  const saved = estimate(data, "s_learner", 20);
  expect(screen.getByRole("img").getAttribute("aria-label")).toContain(
    "simultaneous",
  );
  expect(container.querySelectorAll("circle")).toHaveLength(4);
  expect(container.textContent).toContain(
    saved.value.toLocaleString("en-US", {
      minimumFractionDigits: 3,
      maximumFractionDigits: 3,
    }),
  );
  const other = render(<SensitivityChart data={data} options={DEFAULT} />);
  expect(other.container.querySelectorAll("circle")).toHaveLength(10);
  expect(other.container.querySelector("path")).toBeNull();
});
it("separates exploratory budget outputs from the unchanged frozen policy", async () => {
  render(<Experience data={data} />);
  const user = userEvent.setup();
  const select = screen.getByLabelText("Policy to illustrate");
  expect((select as HTMLSelectElement).value).toBe("none");
  const frozen = screen.getByText(
    "FROZEN PRIMARY RECOMMENDATION",
  ).parentElement!;
  await user.selectOptions(select, "s_learner");
  const receipt = screen
    .getByText("02 / READ THE ILLUSTRATION")
    .closest(".lab-receipt")!;
  expect(receipt.textContent).toContain("20,000");
  expect(receipt.textContent).toContain("not a newly selected policy");
  expect(frozen.textContent).toContain("no spend");
  await user.clear(screen.getByLabelText("Hypothetical budget · units"));
  await user.type(screen.getByLabelText("Hypothetical budget · units"), "0");
  expect(
    within(receipt as HTMLElement).getByRole("alert").textContent,
  ).toContain("No automatic trimming");
  expect((select as HTMLSelectElement).value).toBe("s_learner");
});
it("exposes only five scenarios and preserves 765-family qualifications", async () => {
  render(<Experience data={data} />);
  const user = userEvent.setup();
  const select = screen.getAllByLabelText("Assumed treatment propensity")[0];
  expect(
    within(select)
      .getAllByRole("option")
      .map((o) => (o as HTMLOptionElement).value),
  ).toEqual(["0.8", "0.825", "0.85", "0.875", "0.9"]);
  await user.selectOptions(select, "0.9");
  expect(screen.getByText(/Saved shared DR · assumed e=0.9/)).toBeTruthy();
  expect(
    screen.getByText(/Simultaneous coverage retains the original 765/),
  ).toBeTruthy();
});
it("fails closed without publishing unverified metrics or offering private-file access", async () => {
  vi.spyOn(globalThis, "fetch").mockRejectedValue(new Error("Network error"));
  render(<App />);
  await waitFor(() =>
    expect(screen.getByRole("alert").textContent).toContain(
      "could not be verified",
    ),
  );
  expect(screen.queryByText("13,979,592")).toBeNull();
  expect(screen.queryByLabelText("Upload")).toBeNull();
});
