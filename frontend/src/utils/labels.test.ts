import { allowedNextStatuses, statusLabel } from "./labels";

describe("statusLabel", () => {
  it("한글 라벨을 반환한다", () => {
    expect(statusLabel("PLANNED")).toBe("준비");
    expect(statusLabel("IN_PROGRESS")).toBe("진행");
    expect(statusLabel("COMPLETED")).toBe("완료");
  });
});

describe("allowedNextStatuses", () => {
  it("PLANNED에서는 진행/취소만 가능하다", () => {
    expect(allowedNextStatuses("PLANNED")).toEqual(["IN_PROGRESS", "CANCELED"]);
  });

  it("COMPLETED/CANCELED에서는 전이가 불가하다", () => {
    expect(allowedNextStatuses("COMPLETED")).toEqual([]);
    expect(allowedNextStatuses("CANCELED")).toEqual([]);
  });
});
