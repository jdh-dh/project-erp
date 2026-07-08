import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import {
  changeIssueStatus,
  createIssue,
  fetchIssue,
  fetchIssues,
  fetchUsers,
  updateIssue,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { IssueSeverity, IssueStatus, IssueType } from "../types";

const ISSUE_TYPE_LABELS: Record<IssueType, string> = {
  BUG: "버그",
  IMPROVEMENT: "개선",
  CUSTOMER_REQUEST: "고객요청",
  FAILURE: "장애",
};

const SEVERITY_LABELS: Record<IssueSeverity, string> = {
  LOW: "낮음",
  MEDIUM: "보통",
  HIGH: "높음",
  CRITICAL: "치명",
};

const STATUS_LABELS: Record<IssueStatus, string> = {
  OPEN: "접수",
  IN_PROGRESS: "처리중",
  RESOLVED: "해결",
  CLOSED: "종료",
};

// 백엔드 상태 전이 규칙과 동일 (api.md 6.9절)
const STATUS_TRANSITIONS: Record<IssueStatus, IssueStatus[]> = {
  OPEN: ["IN_PROGRESS", "RESOLVED", "CLOSED"],
  IN_PROGRESS: ["OPEN", "RESOLVED", "CLOSED"],
  RESOLVED: ["OPEN", "CLOSED"],
  CLOSED: [],
};

function IssueDetailView({ projectId, issueId }: { projectId: number; issueId: number }) {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const issue = useQuery({
    queryKey: ["issue", projectId, issueId],
    queryFn: () => fetchIssue(projectId, issueId),
  });

  const canEdit =
    user?.role === "admin" ||
    user?.role === "manager" ||
    (issue.data != null && issue.data.assignee_id === user?.id);

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["issue", projectId, issueId] });
    queryClient.invalidateQueries({ queryKey: ["issues", projectId] });
    setError("");
  }
  const onError = (err: unknown) => setError(errorMessage(err));

  const statusMutation = useMutation({
    mutationFn: ({ status, resolution }: { status: IssueStatus; resolution?: string }) =>
      changeIssueStatus(projectId, issueId, status, resolution),
    onSuccess: invalidate,
    onError,
  });
  const updateMutation = useMutation({
    mutationFn: (body: Parameters<typeof updateIssue>[2]) =>
      updateIssue(projectId, issueId, body),
    onSuccess: invalidate,
    onError,
  });

  function onStatusChange(status: IssueStatus) {
    if (status === "RESOLVED") {
      const resolution = window.prompt("조치 결과를 입력하세요 (필수):", issue.data?.resolution ?? "");
      if (!resolution) return;
      statusMutation.mutate({ status, resolution });
    } else {
      statusMutation.mutate({ status });
    }
  }

  function onSaveAnalysis(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    updateMutation.mutate({
      cause_analysis: String(form.get("cause_analysis")) || undefined,
    });
  }

  if (!issue.data) return <p>불러오는 중…</p>;
  const data = issue.data;

  return (
    <div style={{ padding: "8px 0 8px 24px" }}>
      {error && <div className="error">{error}</div>}
      <table className="grid">
        <tbody>
          <tr>
            <th>설명</th>
            <td colSpan={3}>{data.description ?? "-"}</td>
          </tr>
          <tr>
            <th>원인 분석</th>
            <td>{data.cause_analysis ?? "-"}</td>
            <th>조치 결과</th>
            <td>{data.resolution ?? "-"}</td>
          </tr>
          <tr>
            <th>등록자</th>
            <td>{data.reporter_name}</td>
            <th>해결일</th>
            <td>{data.resolved_date ?? "-"}</td>
          </tr>
        </tbody>
      </table>
      {canEdit && (
        <>
          {STATUS_TRANSITIONS[data.status].length > 0 && (
            <div className="toolbar" style={{ marginTop: 8 }}>
              상태 변경:
              {STATUS_TRANSITIONS[data.status].map((status) => (
                <button
                  key={status}
                  className={status === "CLOSED" ? "secondary" : ""}
                  disabled={statusMutation.isPending}
                  onClick={() => onStatusChange(status)}
                >
                  {STATUS_LABELS[status]}
                </button>
              ))}
            </div>
          )}
          <form className="inline" style={{ marginTop: 8 }} onSubmit={onSaveAnalysis}>
            <label className="field" style={{ minWidth: 320 }}>
              원인 분석
              <input name="cause_analysis" defaultValue={data.cause_analysis ?? ""} />
            </label>
            <button type="submit" disabled={updateMutation.isPending}>
              저장
            </button>
          </form>
        </>
      )}
    </div>
  );
}

export default function IssueSection({ projectId }: { projectId: number }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const issues = useQuery({
    queryKey: ["issues", projectId, statusFilter],
    queryFn: () => fetchIssues(projectId, { status: statusFilter }),
  });
  const users = useQuery({ queryKey: ["users-all"], queryFn: () => fetchUsers() });

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createIssue>[1]) =>
      createIssue(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["issues", projectId] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      issue_type: String(form.get("issue_type")) as IssueType,
      title: String(form.get("title")),
      description: String(form.get("description")) || undefined,
      severity: String(form.get("severity")) as IssueSeverity,
      assignee_id: form.get("assignee_id") ? Number(form.get("assignee_id")) : null,
    });
  }

  return (
    <div className="card">
      <h3>이슈 관리</h3>
      {error && <div className="error">{error}</div>}
      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">전체 상태</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <button onClick={() => setShowForm((v) => !v)}>
          {showForm ? "닫기" : "+ 이슈 등록"}
        </button>
      </div>
      {showForm && (
        <form className="inline" style={{ marginBottom: 12 }} onSubmit={onCreate}>
          <label className="field">
            유형
            <select name="issue_type" required>
              {Object.entries(ISSUE_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            제목
            <input name="title" required />
          </label>
          <label className="field">
            심각도
            <select name="severity" defaultValue="MEDIUM">
              {Object.entries(SEVERITY_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            담당자
            <select name="assignee_id" defaultValue="">
              <option value="">(미지정)</option>
              {users.data?.items
                .filter((u) => u.is_active)
                .map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name}
                  </option>
                ))}
            </select>
          </label>
          <label className="field">
            설명
            <input name="description" />
          </label>
          <button type="submit" disabled={createMutation.isPending}>
            등록
          </button>
        </form>
      )}
      <table className="grid">
        <thead>
          <tr>
            <th>제목</th>
            <th>유형</th>
            <th>심각도</th>
            <th>상태</th>
            <th>담당자</th>
          </tr>
        </thead>
        <tbody>
          {issues.data?.map((issue) => (
            <tr key={issue.id}>
              <td>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setExpandedId(expandedId === issue.id ? null : issue.id);
                  }}
                >
                  {expandedId === issue.id ? "▼" : "▶"} {issue.title}
                </a>
              </td>
              <td>{ISSUE_TYPE_LABELS[issue.issue_type]}</td>
              <td>
                <span
                  className={`badge ${
                    issue.severity === "CRITICAL" || issue.severity === "HIGH"
                      ? "inactive"
                      : ""
                  }`}
                >
                  {SEVERITY_LABELS[issue.severity]}
                </span>
              </td>
              <td>
                <span className={`badge ${issue.status === "RESOLVED" || issue.status === "CLOSED" ? "active" : ""}`}>
                  {STATUS_LABELS[issue.status]}
                </span>
              </td>
              <td>{issue.assignee_name ?? "-"}</td>
            </tr>
          ))}
          {issues.data?.length === 0 && (
            <tr>
              <td colSpan={5}>등록된 이슈가 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {expandedId != null && <IssueDetailView projectId={projectId} issueId={expandedId} />}
    </div>
  );
}
