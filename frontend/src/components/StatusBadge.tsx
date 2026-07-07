import type { ProjectStatus } from "../types";
import { statusLabel } from "../utils/labels";

export default function StatusBadge({ status }: { status: ProjectStatus }) {
  return <span className={`badge ${status}`}>{statusLabel(status)}</span>;
}
