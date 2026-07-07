import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import { errorMessage } from "../api/client";
import { createCustomer, fetchCustomers } from "../api/erp";
import { useAuth } from "../auth/AuthContext";

export default function CustomerListPage() {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [q, setQ] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState("");

  const customers = useQuery({
    queryKey: ["customers", q],
    queryFn: () => fetchCustomers(q),
  });

  const create = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    create.mutate({
      name: String(form.get("name")),
      business_no: String(form.get("business_no")) || undefined,
      address: String(form.get("address")) || undefined,
      note: String(form.get("note")) || undefined,
    });
  }

  return (
    <div>
      <h2>고객사</h2>
      <div className="toolbar">
        <input
          placeholder="고객사명 검색"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        {canEdit && (
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 고객사 등록"}
          </button>
        )}
      </div>

      {showForm && (
        <div className="card">
          <h3>고객사 등록</h3>
          <form className="inline" onSubmit={onCreate}>
            <label className="field">
              이름
              <input name="name" required />
            </label>
            <label className="field">
              사업자번호
              <input name="business_no" />
            </label>
            <label className="field">
              주소
              <input name="address" />
            </label>
            <label className="field">
              비고
              <input name="note" />
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
            <th>사업자번호</th>
            <th>주소</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          {customers.data?.items.map((c) => (
            <tr key={c.id}>
              <td>
                <Link to={`/customers/${c.id}`}>{c.name}</Link>
              </td>
              <td>{c.business_no ?? "-"}</td>
              <td>{c.address ?? "-"}</td>
              <td>
                <span className={`badge ${c.is_active ? "active" : "inactive"}`}>
                  {c.is_active ? "활성" : "비활성"}
                </span>
              </td>
            </tr>
          ))}
          {customers.data?.items.length === 0 && (
            <tr>
              <td colSpan={4}>등록된 고객사가 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
