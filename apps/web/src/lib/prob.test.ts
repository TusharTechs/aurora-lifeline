import { describe, expect, it } from "vitest";
import { isoDecilesToHours, NEVER_H, probAt, probAtHours, rampRed } from "./prob";

describe("probAt", () => {
  it("is the largest decile share reached by t", () => {
    const d = { d1: 10, d2: 12, d3: 20 };
    expect(probAt(d, 5)).toBe(0);
    expect(probAt(d, 10)).toBeCloseTo(0.1);
    expect(probAt(d, 15)).toBeCloseTo(0.2);
    expect(probAt(d, 100)).toBeCloseTo(0.3); // d4..d9 missing: never reached by 40%+ of members
  });
  it("is monotone in t", () => {
    const d = { d1: 3, d2: 5, d3: 5, d4: 8, d5: 9, d6: 20, d7: 30, d8: 40, d9: 50 };
    let prev = 0;
    for (let t = 0; t < 60; t++) {
      const p = probAt(d, t);
      expect(p).toBeGreaterThanOrEqual(prev);
      prev = p;
    }
    expect(prev).toBeCloseTo(0.9);
  });
  it("treats the never-reached sentinel as never, even at the end of the horizon", () => {
    const d = {
      d1: 21,
      d2: 30,
      d3: NEVER_H,
      d4: NEVER_H,
      d5: NEVER_H,
      d6: NEVER_H,
      d7: NEVER_H,
      d8: NEVER_H,
      d9: NEVER_H,
    };
    expect(probAt(d, 0)).toBe(0);
    expect(probAt(d, 25)).toBeCloseTo(0.1);
    expect(probAt(d, 5000)).toBeCloseTo(0.2);
  });
});

describe("iso deciles", () => {
  it("converts to hours and back to probability", () => {
    const h = isoDecilesToHours("2025-10-26T04:00:00Z", ["2025-10-26T10:00:00Z", null]);
    expect(h).toEqual([6, null]);
    expect(probAtHours(h, 6)).toBeCloseTo(0.1);
  });
});

describe("rampRed", () => {
  it("is transparent at zero and dark red at one", () => {
    expect(rampRed(0)[3]).toBe(0);
    expect(rampRed(1).slice(0, 3)).toEqual([127, 29, 29]);
  });
});
