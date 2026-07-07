import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import {
  achieveMilestone,
  createMilestone,
  createWbs,
  deactivateWbs,
  fetchMilestones,
  fetchScheduleSummary,
  fetchUsers,
  fetchWbs,
  updateWbs,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { WbsStatus } from "../types";

const WBS_STATUS_LABELS: Record<WbsStatus, string> = {
  TODO: "대기",
  IN_PROGRESS: "진행",
  DONE: "완료",
};

export default function ScheduleSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showWbsForm, setShowWbsForm] = useState(false);
  const [showMsForm, setShowMsForm] = useState(false);

  const wbs = useQuery({
    queryKey: ["wbs", projectId],
    queryFn: () => fetchWbs(projectId),
  });
  const milestones = useQuery({
    queryKey: ["milestones", projectId],
    queryFn: () => fetchMilestones(projectId),
  });
  const summary = useQuery({
    queryKey: ["schedule-summary", projectId],
    queryFn: () => fetchScheduleSummary(projectId),
  });
  const users = useQuery({
    queryKey: ["users-all"],
    queryFn: () => fetchUsers(),
    enabled: canEdit,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["wbs", projectId] });
    queryClient.invalidateQueries({ queryKey: ["milestones", projectId] });
    queryClient.invalidateQueries({ queryKey: ["schedule-summary", projectId] });
    setError("");
  }

  const onError = (err: unknown) => setError(errorMessage(err));

  const createWbsMutation = useMutation({
    mutationFn: (body: Parameters<typeof createWbs>[1]) => createWbs(projectId, body),
    onSuccess: () => {
      invalidate();
      setShowWbsForm(false);
    },
    onError,
  });
  const updateWbsMutation = useMutation({
    mutationFn: ({ itemId, body }: { itemId: number; body: Parameters<typeof updateWbs>[2] }) =>
      updateWbs(projectId, itemId, body),
    onSuccess: invalidate,
    onError,
  });
  const deactivateWbsMutation = useMutation({
    mutationFn: (itemId: number) => deactivateWbs(projectId, itemId),
    onSuccess: invalidate,
    onError,
  });
  const createMsMutation = useMutation({
    mutationFn: (body: { name: string; due_date: string }) =>
      createMilestone(projectId, body),
    onSuccess: () => {
      invalidate();
      setShowMsForm(false);
    },
    onError,
  });
  const achieveMsMutation = useMutation({
    mutationFn: (msId: number) => achieveMilestone(projectId, msId),
    onSuccess: invalidate,
    onError,
  });

  function onCreateWbs(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createWbsMutation.mutate({
      name: String(form.get("name")),
      parent_id: form.get("parent_id") ? Number(form.get("parent_id")) : null,
      assignee_id: form.get("assignee_id") ? Number(form.get("assignee_id")) : null,
      start_date: String(form.get("start_date")) || null,
      end_date: String(form.get("end_date")) || null,
    });
  }

  function onCreateMs(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMsMutation.mutate({
      name: String(form.get("name")),
      due_date: String(form.get("due_date")),
    });
  }

  function canEditProgress(assigneeId: number | null): boolean {
    return canEdit || (user != null && assigneeId === user.id);
  }

  return (
    <>
      <div className="card">
        <h3>
          일정 (WBS)
          {summary.data && (
            <span style={{ fontWeight: 400, fontSize: 13, marginLeft: 12 }}>
              전체 진척률 <b>{summary.data.progress}%</b> · WBS {summary.data.wbs_total}건
              {summary.data.wbs_delayed > 0 && (
                <span className="badge inactive" style={{ marginLeft: 6 }}>
                  지연 {summary.data.wbs_delayed}건
                </span>
              )}
            </span>
          )}
        </h3>
        {error && <div className="error">{error}</div>}
        <table className="grid">
          <thead>
            <tr>
              <th>작업명</th>
              <th>담당자</th>
              <th>기간</th>
              <th style={{ width: 140 }}>진척률</th>
              <th>상태</th>
              {canEdit && <th></th>}
            </tr>
          </thead>
          <tbody>
            {wbs.data?.map((item) => (
              <tr key={item.id}>
                <td>
                  <span style={{ paddingLeft: item.depth * 18 }}>
                    {item.depth > 0 && "└ "}
                    {item.name}
                  </span>
                  {item.is_delayed && (
                    <span className="badge inactive" style={{ marginLeft: 6 }}>
                      지연
                    </span>
                  )}
                </td>
                <td>{item.assignee_name ?? "-"}</td>
                <td>
                  {item.start_date ?? "-"} ~ {item.end_date ?? "-"}
                </td>
                <td>
                  {canEditProgress(item.assignee_id) ? (
                    <input
                      type="number"
                      min={0}
                      max={100}
                      defaultValue={item.progress}
                      style={{ width: 70 }}
                      onBlur={(e) => {
                        const value = Number(e.target.value);
                        if (value !== item.progress && value >= 0 && value <= 100) {
                          updateWbsMutation.mutate({
                            itemId: item.id,
                            body: { progress: value },
                          });
                        }
                      }}
                    />
                  ) : (
                    `${item.progress}%`
                  )}
                </td>
                <td>{WBS_STATUS_LABELS[item.status]}</td>
                {canEdit && (
                  <td>
                    <button
                      className="danger"
                      disabled={deactivateWbsMutation.isPending}
                      onClick={() => {
                        if (window.confirm(`'${item.name}' 항목을 삭제(비활성화)하시겠습니까? 하위 항목도 함께 삭제됩니다.`)) {
                          deactivateWbsMutation.mutate(item.id);
                        }
                      }}
                    >
                      삭제
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {wbs.data?.length === 0 && (
              <tr>
                <td colSpan={6}>등록된 WBS 항목이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
        {canEdit && (
          <div style={{ marginTop: 12 }}>
            <button onClick={() => setShowWbsForm((v) => !v)}>
              {showWbsForm ? "닫기" : "+ WBS 항목 추가"}
            </button>
            {showWbsForm && (
              <form className="inline" style={{ marginTop: 12 }} onSubmit={onCreateWbs}>
                <label className="field">
                  작업명
                  <input name="name" required />
                </label>
                <label className="field">
                  상위 항목
                  <select name="parent_id" defaultValue="">
                    <option value="">(최상위)</option>
                    {wbs.data?.map((item) => (
                      <option key={item.id} value={item.id}>
                        {" ".repeat(item.depth * 2)}
                        {item.name}
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
                  시작일
                  <input name="start_date" type="date" />
                </label>
                <label className="field">
                  종료일
                  <input name="end_date" type="date" />
                </label>
                <button type="submit" disabled={createWbsMutation.isPending}>
                  추가
                </button>
              </form>
            )}
          </div>
        )}
      </div>

      <div className="card">
        <h3>
          마일스톤
          {summary.data && summary.data.milestone_delayed > 0 && (
            <span className="badge inactive" style={{ marginLeft: 8 }}>
              지연 {summary.data.milestone_delayed}건
            </span>
          )}
        </h3>
        <table className="grid">
          <thead>
            <tr>
              <th>이름</th>
              <th>목표일</th>
              <th>상태</th>
              <th>달성일</th>
              {canEdit && <th></th>}
            </tr>
          </thead>
          <tbody>
            {milestones.data?.map((ms) => (
              <tr key={ms.id}>
                <td>
                  {ms.name}
                  {ms.is_delayed && (
                    <span className="badge inactive" style={{ marginLeft: 6 }}>
                      지연
                    </span>
                  )}
                </td>
                <td>{ms.due_date}</td>
                <td>
                  <span className={`badge ${ms.status === "ACHIEVED" ? "active" : ""}`}>
                    {ms.status === "ACHIEVED" ? "달성" : "예정"}
                  </span>
                </td>
                <td>{ms.achieved_date ?? "-"}</td>
                {canEdit && (
                  <td>
                    {ms.status === "PENDING" && (
                      <button
                        disabled={achieveMsMutation.isPending}
                        onClick={() => achieveMsMutation.mutate(ms.id)}
                      >
                        달성 처리
                      </button>
                    )}
                  </td>
                )}
              </tr>
            ))}
            {milestones.data?.length === 0 && (
              <tr>
                <td colSpan={5}>등록된 마일스톤이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
        {canEdit && (
          <div style={{ marginTop: 12 }}>
            <button onClick={() => setShowMsForm((v) => !v)}>
              {showMsForm ? "닫기" : "+ 마일스톤 추가"}
            </button>
            {showMsForm && (
              <form className="inline" style={{ marginTop: 12 }} onSubmit={onCreateMs}>
                <label className="field">
                  이름
                  <input name="name" required />
                </label>
                <label className="field">
                  목표일
                  <input name="due_date" type="date" required />
                </label>
                <button type="submit" disabled={createMsMutation.isPending}>
                  추가
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </>
  );
}
