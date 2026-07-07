import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import { createUser, deactivateUser, fetchUsers } from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import { ROLE_LABELS } from "../utils/labels";
import type { Role } from "../types";

export default function UserListPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const users = useQuery({ queryKey: ["users-all"], queryFn: () => fetchUsers() });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["users-all"] });
    setError("");
  }

  const create = useMutation({
    mutationFn: createUser,
    onSuccess: () => {
      invalidate();
      setShowForm(false);
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const deactivate = useMutation({
    mutationFn: deactivateUser,
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    create.mutate({
      email: String(form.get("email")),
      password: String(form.get("password")),
      name: String(form.get("name")),
      role: String(form.get("role")),
    });
  }

  return (
    <div>
      <h2>사용자</h2>
      {isAdmin && (
        <div className="toolbar">
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 사용자 등록"}
          </button>
        </div>
      )}

      {showForm && (
        <div className="card">
          <h3>사용자 등록</h3>
          <form className="inline" onSubmit={onCreate}>
            <label className="field">
              이메일
              <input name="email" type="email" required />
            </label>
            <label className="field">
              비밀번호
              <input name="password" type="password" minLength={8} required />
            </label>
            <label className="field">
              이름
              <input name="name" required />
            </label>
            <label className="field">
              역할
              <select name="role" required>
                {Object.entries(ROLE_LABELS).map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </select>
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
            <th>이름</th>
            <th>이메일</th>
            <th>역할</th>
            <th>상태</th>
            {isAdmin && <th></th>}
          </tr>
        </thead>
        <tbody>
          {users.data?.items.map((u) => (
            <tr key={u.id}>
              <td>{u.name}</td>
              <td>{u.email}</td>
              <td>{ROLE_LABELS[u.role as Role]}</td>
              <td>
                <span className={`badge ${u.is_active ? "active" : "inactive"}`}>
                  {u.is_active ? "활성" : "비활성"}
                </span>
              </td>
              {isAdmin && (
                <td>
                  {u.is_active && u.id !== user?.id && (
                    <button
                      className="danger"
                      disabled={deactivate.isPending}
                      onClick={() => {
                        if (window.confirm(`${u.name} 계정을 비활성화하시겠습니까?`)) {
                          deactivate.mutate(u.id);
                        }
                      }}
                    >
                      비활성화
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
