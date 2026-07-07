import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import {
  addContract,
  changeProjectStatus,
  fetchChangeLogs,
  fetchProject,
  fetchUsers,
  setProjectMembers,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import StatusBadge from "../components/StatusBadge";
import { TYPE_LABELS, allowedNextStatuses, statusLabel } from "../utils/labels";
import type { ProjectStatus } from "../types";

export default function ProjectDetailPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const project = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
  });
  const logs = useQuery({
    queryKey: ["change-logs", "project", projectId],
    queryFn: () => fetchChangeLogs("project", projectId),
  });
  const users = useQuery({
    queryKey: ["users-all"],
    queryFn: () => fetchUsers(),
    enabled: canEdit,
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    queryClient.invalidateQueries({ queryKey: ["change-logs", "project", projectId] });
    setError("");
  }

  const statusMutation = useMutation({
    mutationFn: (status: ProjectStatus) => changeProjectStatus(projectId, status),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  const memberMutation = useMutation({
    mutationFn: (members: { user_id: number; role?: string | null }[]) =>
      setProjectMembers(projectId, members),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  const contractMutation = useMutation({
    mutationFn: (body: { contract_no: string; amount?: string }) =>
      addContract(projectId, body),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  function onAddMember(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!project.data) return;
    const form = new FormData(e.currentTarget);
    const userId = Number(form.get("user_id"));
    const role = String(form.get("role")) || null;
    const existing = project.data.members.map((m) => ({
      user_id: m.user_id,
      role: m.role,
    }));
    if (existing.some((m) => m.user_id === userId)) {
      setError("이미 참여 중인 사용자입니다.");
      return;
    }
    memberMutation.mutate([...existing, { user_id: userId, role }]);
    e.currentTarget.reset();
  }

  function onRemoveMember(userId: number) {
    if (!project.data) return;
    memberMutation.mutate(
      project.data.members
        .filter((m) => m.user_id !== userId)
        .map((m) => ({ user_id: m.user_id, role: m.role }))
    );
  }

  function onAddContract(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    contractMutation.mutate({
      contract_no: String(form.get("contract_no")),
      amount: String(form.get("amount")) || undefined,
    });
    e.currentTarget.reset();
  }

  if (project.isLoading) return <p>불러오는 중…</p>;
  if (!project.data) return <p>프로젝트를 찾을 수 없습니다.</p>;
  const p = project.data;

  return (
    <div>
      <h2>
        [{p.code}] {p.name} <StatusBadge status={p.status} />
      </h2>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>기본 정보</h3>
        <table className="grid">
          <tbody>
            <tr>
              <th>고객사</th>
              <td>{p.customer_name}</td>
              <th>유형</th>
              <td>{TYPE_LABELS[p.project_type]}</td>
            </tr>
            <tr>
              <th>PM</th>
              <td>{p.manager_name}</td>
              <th>기간</th>
              <td>
                {p.start_date ?? "-"} ~ {p.end_date ?? "-"}
              </td>
            </tr>
            <tr>
              <th>설명</th>
              <td colSpan={3}>{p.description ?? "-"}</td>
            </tr>
          </tbody>
        </table>
        {canEdit && allowedNextStatuses(p.status).length > 0 && (
          <div className="toolbar" style={{ marginTop: 12 }}>
            상태 변경:
            {allowedNextStatuses(p.status).map((s) => (
              <button
                key={s}
                className={s === "CANCELED" ? "danger" : ""}
                disabled={statusMutation.isPending}
                onClick={() => statusMutation.mutate(s)}
              >
                {statusLabel(s)}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="card">
        <h3>참여자</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>이름</th>
              <th>역할</th>
              {canEdit && <th></th>}
            </tr>
          </thead>
          <tbody>
            {p.members.map((m) => (
              <tr key={m.id}>
                <td>{m.user_name}</td>
                <td>{m.role ?? "-"}</td>
                {canEdit && (
                  <td>
                    <button
                      className="danger"
                      onClick={() => onRemoveMember(m.user_id)}
                    >
                      제외
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {p.members.length === 0 && (
              <tr>
                <td colSpan={3}>참여자가 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
        {canEdit && (
          <form className="inline" style={{ marginTop: 12 }} onSubmit={onAddMember}>
            <label className="field">
              사용자
              <select name="user_id" required>
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
              역할
              <input name="role" placeholder="HW개발, SW개발 등" />
            </label>
            <button type="submit" disabled={memberMutation.isPending}>
              추가
            </button>
          </form>
        )}
      </div>

      <div className="card">
        <h3>계약</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>계약번호</th>
              <th>금액</th>
              <th>계약일</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            {p.contracts.map((c) => (
              <tr key={c.id}>
                <td>{c.contract_no}</td>
                <td>{c.amount ? Number(c.amount).toLocaleString() + "원" : "-"}</td>
                <td>{c.signed_date ?? "-"}</td>
                <td>{c.status}</td>
              </tr>
            ))}
            {p.contracts.length === 0 && (
              <tr>
                <td colSpan={4}>등록된 계약이 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
        {canEdit && (
          <form className="inline" style={{ marginTop: 12 }} onSubmit={onAddContract}>
            <label className="field">
              계약번호
              <input name="contract_no" required />
            </label>
            <label className="field">
              금액(원)
              <input name="amount" type="number" min="0" />
            </label>
            <button type="submit" disabled={contractMutation.isPending}>
              계약 등록
            </button>
          </form>
        )}
      </div>

      <div className="card">
        <h3>변경 이력</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>일시</th>
              <th>작업</th>
              <th>변경자</th>
            </tr>
          </thead>
          <tbody>
            {logs.data?.items.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.changed_at).toLocaleString("ko-KR")}</td>
                <td>{log.action}</td>
                <td>{log.changed_by_name}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
