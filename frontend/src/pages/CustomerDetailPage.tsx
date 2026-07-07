import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";
import { errorMessage } from "../api/client";
import { addContact, deactivateCustomer, fetchCustomer } from "../api/erp";
import { useAuth } from "../auth/AuthContext";

export default function CustomerDetailPage() {
  const { id } = useParams();
  const customerId = Number(id);
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const customer = useQuery({
    queryKey: ["customer", customerId],
    queryFn: () => fetchCustomer(customerId),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["customer", customerId] });
    queryClient.invalidateQueries({ queryKey: ["customers"] });
    setError("");
  }

  const contactMutation = useMutation({
    mutationFn: (body: { name: string; position?: string; phone?: string; email?: string }) =>
      addContact(customerId, body),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateCustomer(customerId),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  function onAddContact(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    contactMutation.mutate({
      name: String(form.get("name")),
      position: String(form.get("position")) || undefined,
      phone: String(form.get("phone")) || undefined,
      email: String(form.get("email")) || undefined,
    });
    e.currentTarget.reset();
  }

  if (customer.isLoading) return <p>불러오는 중…</p>;
  if (!customer.data) return <p>고객사를 찾을 수 없습니다.</p>;
  const c = customer.data;

  return (
    <div>
      <h2>
        {c.name}{" "}
        <span className={`badge ${c.is_active ? "active" : "inactive"}`}>
          {c.is_active ? "활성" : "비활성"}
        </span>
      </h2>
      {error && <div className="error">{error}</div>}

      <div className="card">
        <h3>기본 정보</h3>
        <table className="grid">
          <tbody>
            <tr>
              <th>사업자번호</th>
              <td>{c.business_no ?? "-"}</td>
              <th>주소</th>
              <td>{c.address ?? "-"}</td>
            </tr>
            <tr>
              <th>비고</th>
              <td colSpan={3}>{c.note ?? "-"}</td>
            </tr>
          </tbody>
        </table>
        {canEdit && c.is_active && (
          <div className="toolbar" style={{ marginTop: 12 }}>
            <button
              className="danger"
              disabled={deactivateMutation.isPending}
              onClick={() => {
                if (window.confirm("이 고객사를 비활성화하시겠습니까?")) {
                  deactivateMutation.mutate();
                }
              }}
            >
              비활성화
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h3>담당자</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>이름</th>
              <th>직책</th>
              <th>연락처</th>
              <th>이메일</th>
            </tr>
          </thead>
          <tbody>
            {c.contacts.map((contact) => (
              <tr key={contact.id}>
                <td>{contact.name}</td>
                <td>{contact.position ?? "-"}</td>
                <td>{contact.phone ?? "-"}</td>
                <td>{contact.email ?? "-"}</td>
              </tr>
            ))}
            {c.contacts.length === 0 && (
              <tr>
                <td colSpan={4}>등록된 담당자가 없습니다.</td>
              </tr>
            )}
          </tbody>
        </table>
        {canEdit && (
          <form className="inline" style={{ marginTop: 12 }} onSubmit={onAddContact}>
            <label className="field">
              이름
              <input name="name" required />
            </label>
            <label className="field">
              직책
              <input name="position" />
            </label>
            <label className="field">
              연락처
              <input name="phone" />
            </label>
            <label className="field">
              이메일
              <input name="email" type="email" />
            </label>
            <button type="submit" disabled={contactMutation.isPending}>
              담당자 추가
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
