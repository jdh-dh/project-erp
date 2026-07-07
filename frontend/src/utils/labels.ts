import type { ProjectStatus, ProjectType, Role } from "../types";

export const STATUS_LABELS: Record<ProjectStatus, string> = {
  PLANNED: "준비",
  IN_PROGRESS: "진행",
  ON_HOLD: "보류",
  COMPLETED: "완료",
  CANCELED: "취소",
};

export const TYPE_LABELS: Record<ProjectType, string> = {
  HW: "하드웨어",
  SW: "소프트웨어",
  HYBRID: "HW+SW",
};

export const ROLE_LABELS: Record<Role, string> = {
  admin: "관리자",
  manager: "매니저",
  member: "구성원",
};

// 백엔드 상태 전이 규칙과 동일 (api.md 6절)
export const STATUS_TRANSITIONS: Record<ProjectStatus, ProjectStatus[]> = {
  PLANNED: ["IN_PROGRESS", "CANCELED"],
  IN_PROGRESS: ["ON_HOLD", "COMPLETED", "CANCELED"],
  ON_HOLD: ["IN_PROGRESS", "CANCELED"],
  COMPLETED: [],
  CANCELED: [],
};

export function statusLabel(status: ProjectStatus): string {
  return STATUS_LABELS[status] ?? status;
}

export function allowedNextStatuses(status: ProjectStatus): ProjectStatus[] {
  return STATUS_TRANSITIONS[status] ?? [];
}
