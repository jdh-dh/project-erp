import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { errorMessage } from "../api/client";
import {
  createProject,
  fetchCustomers,
  fetchProjects,
  fetchUsers,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import StatusBadge from "../components/StatusBadge";
import { STATUS_LABELS, TYPE_LABELS } from "../utils/labels";
import type { ProjectStatus, ProjectType } from "../types";

export default function ProjectListPage() {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();

  const [statusFilter, setStatusFilter] = useState("");
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const projects = useQuery({
    queryKey: ["projects", statusFilter, q],
    queryFn: () =>
      fetchProjects({ status: statusFilter || undefined, q: q || undefined }),
  });
  const customers = useQuery({
    queryKey: ["customers-all"],
    queryFn: () => fetchCustomers(),
    enabled: canEdit,
  });
  const users = useQuery({
    queryKey: ["users-all"],
    queryFn: () => fetchUsers(),
    enabled: canEdit,
  });

  const create = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    create.mutate({
      code: String(form.get("code")),
      name: String(form.get("name")),
      customer_id: Number(form.get("customer_id")),
      project_type: String(form.get("project_type")) as ProjectType,
      manager_id: Number(form.get("manager_id")),
      start_date: String(form.get("start_date")) || null,
      end_date: String(form.get("end_date")) || null,
      description: String(form.get("description")) || null,
    });
  }

  return (
    <div>
      <h2>프로젝트</h2>
      <div className="toolbar">
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">전체 상태</option>
          {Object.entries(STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <input
          placeholder="코드/이름 검색"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {canEdit && (
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 프로젝트 등록"}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card">
          <h3>프로젝트 등록</h3>
          <form className="inline" onSubmit={onCreate}>
            <label className="field">
              코드
              <input name="code" required />
            </label>
            <label className="field">
              이름
              <input name="name" required />
            </label>
            <label className="field">
              고객사
              <select name="customer_id" required>
                {customers.data?.items.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              유형
              <select name="project_type" required>
                {Object.entries(TYPE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="field">
              PM
              <select name="manager_id" required>
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
            <label className="field">
              설명
              <input name="description" />
            </label>
            <button type="submit" disabled={create.isPending}>
              등록
            </button>
          </form>
          {error && <div className="error">{error}</div>}
        </div>
      )}

      <table className="grid">
        <thead>
          <tr>
            <th>코드</th>
            <th>이름</th>
            <th>고객사</th>
            <th>유형</th>
            <th>상태</th>
            <th>PM</th>
            <th>기간</th>
          </tr>
        </thead>
        <tbody>
          {projects.data?.items.map((p) => (
            <tr key={p.id}>
              <td>
                <Link to={`/projects/${p.id}`}>{p.code}</Link>
              </td>
              <td>{p.name}</td>
              <td>{p.customer_name}</td>
              <td>{TYPE_LABELS[p.project_type]}</td>
              <td>
                <StatusBadge status={p.status as ProjectStatus} />
              </td>
              <td>{p.manager_name}</td>
              <td>
                {p.start_date ?? "-"} ~ {p.end_date ?? "-"}
              </td>
            </tr>
          ))}
          {projects.data?.items.length === 0 && (
            <tr>
              <td colSpan={7}>등록된 프로젝트가 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
