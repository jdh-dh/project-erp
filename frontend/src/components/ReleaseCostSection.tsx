import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import {
  createCost,
  createRelease,
  fetchCosts,
  fetchCostSummary,
  fetchReleases,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { CostCategory } from "../types";

const COST_CATEGORY_LABELS: Record<CostCategory, string> = {
  LABOR: "인건비",
  MATERIAL: "자재비",
  OUTSOURCING: "외주비",
  EQUIPMENT: "장비비",
  ETC: "기타",
};

function won(value: string): string {
  return `${Number(value).toLocaleString()}원`;
}

export function ReleaseSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const releases = useQuery({
    queryKey: ["releases", projectId],
    queryFn: () => fetchReleases(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createRelease>[1]) =>
      createRelease(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["releases", projectId] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      version: String(form.get("version")),
      title: String(form.get("title")),
      release_date: String(form.get("release_date")),
      content: String(form.get("content")) || undefined,
    });
  }

  return (
    <div className="card">
      <h3>릴리즈 이력</h3>
      {error && <div className="error">{error}</div>}
      <table className="grid">
        <thead>
          <tr>
            <th>버전</th>
            <th>제목</th>
            <th>릴리즈일</th>
            <th>내용</th>
            <th>등록자</th>
          </tr>
        </thead>
        <tbody>
          {releases.data?.map((release) => (
            <tr key={release.id}>
              <td>{release.version}</td>
              <td>{release.title}</td>
              <td>{release.release_date}</td>
              <td>{release.content ?? "-"}</td>
              <td>{release.creator_name}</td>
            </tr>
          ))}
          {releases.data?.length === 0 && (
            <tr>
              <td colSpan={5}>릴리즈 이력이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {canEdit && (
        <div style={{ marginTop: 12 }}>
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 릴리즈 등록"}
          </button>
          {showForm && (
            <form className="inline" style={{ marginTop: 12 }} onSubmit={onCreate}>
              <label className="field">
                버전
                <input name="version" placeholder="1.0.0" required />
              </label>
              <label className="field">
                제목
                <input name="title" required />
              </label>
              <label className="field">
                릴리즈일
                <input name="release_date" type="date" required />
              </label>
              <label className="field">
                내용
                <input name="content" />
              </label>
              <button type="submit" disabled={createMutation.isPending}>
                등록
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}

export function CostSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const costs = useQuery({
    queryKey: ["costs", projectId],
    queryFn: () => fetchCosts(projectId),
  });
  const summary = useQuery({
    queryKey: ["cost-summary", projectId],
    queryFn: () => fetchCostSummary(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createCost>[1]) => createCost(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["costs", projectId] });
      queryClient.invalidateQueries({ queryKey: ["cost-summary", projectId] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      cost_date: String(form.get("cost_date")),
      category: String(form.get("category")) as CostCategory,
      item: String(form.get("item")),
      amount: String(form.get("amount")),
      note: String(form.get("note")) || undefined,
    });
  }

  return (
    <div className="card">
      <h3>
        비용
        {summary.data && (
          <span style={{ fontWeight: 400, fontSize: 13, marginLeft: 12 }}>
            총 <b>{won(summary.data.total)}</b>
            {Object.entries(summary.data.by_category).map(([category, amount]) => (
              <span key={category} style={{ marginLeft: 8 }}>
                {COST_CATEGORY_LABELS[category as CostCategory]} {won(amount)}
              </span>
            ))}
          </span>
        )}
      </h3>
      {error && <div className="error">{error}</div>}
      <table className="grid">
        <thead>
          <tr>
            <th>일자</th>
            <th>분류</th>
            <th>항목</th>
            <th>금액</th>
            <th>등록자</th>
          </tr>
        </thead>
        <tbody>
          {costs.data?.map((cost) => (
            <tr key={cost.id}>
              <td>{cost.cost_date}</td>
              <td>{COST_CATEGORY_LABELS[cost.category]}</td>
              <td>{cost.item}</td>
              <td>{won(cost.amount)}</td>
              <td>{cost.creator_name}</td>
            </tr>
          ))}
          {costs.data?.length === 0 && (
            <tr>
              <td colSpan={5}>등록된 비용이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {canEdit && (
        <div style={{ marginTop: 12 }}>
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 비용 등록"}
          </button>
          {showForm && (
            <form className="inline" style={{ marginTop: 12 }} onSubmit={onCreate}>
              <label className="field">
                일자
                <input name="cost_date" type="date" required />
              </label>
              <label className="field">
                분류
                <select name="category" required>
                  {Object.entries(COST_CATEGORY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                항목
                <input name="item" required />
              </label>
              <label className="field">
                금액(원)
                <input name="amount" type="number" min={1} required />
              </label>
              <label className="field">
                비고
                <input name="note" />
              </label>
              <button type="submit" disabled={createMutation.isPending}>
                등록
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
