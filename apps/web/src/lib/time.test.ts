import { describe, expect, it } from "vitest";
import { formatIst } from "./time";

describe("formatIst", () => {
  it("converts UTC to IST (+05:30)", () => {
    expect(formatIst("2025-10-28T08:30:00Z")).toBe("28 Oct, 14:00 IST");
  });
  it("rejects invalid input", () => {
    expect(() => formatIst("not a date")).toThrow();
  });
});
