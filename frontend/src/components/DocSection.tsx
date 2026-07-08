import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import { createDocument, fetchDocuments, updateDocument } from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { DocType } from "../types";

const DOC_TYPE_LABELS: Record<DocType, string> = {
  REQUIREMENTS: "요구사항",
  DESIGN: "설계서",
  INTERFACE: "인터페이스",
  TEST_PLAN: "시험 계획서",
  VERIFICATION: "검증 문서",
  RELEASE_NOTE: "릴리즈 노트",
  OTHER: "기타",
};

export default function DocSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");

  const docs = useQuery({
    queryKey: ["documents", projectId, typeFilter],
    queryFn: () => fetchDocuments(projectId, typeFilter),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["documents", projectId] });
    setError("");
  }

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createDocument>[1]) =>
      createDocument(projectId, body),
    onSuccess: () => {
      invalidate();
      setShowForm(false);
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const versionMutation = useMutation({
    mutationFn: ({ docId, version }: { docId: number; version: string }) =>
      updateDocument(projectId, docId, { version }),
    onSuccess: invalidate,
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      doc_type: String(form.get("doc_type")) as DocType,
      title: String(form.get("title")),
      version: String(form.get("version")) || "1.0",
      file_url: String(form.get("file_url")) || undefined,
      description: String(form.get("description")) || undefined,
    });
  }

  return (
    <div className="card">
      <h3>문서 관리</h3>
      {error && <div className="error">{error}</div>}
      <div className="toolbar">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">전체 유형</option>
          {Object.entries(DOC_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {canEdit && (
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 문서 등록"}
          </button>
        )}
      </div>
      {showForm && (
        <form className="inline" style={{ marginBottom: 12 }} onSubmit={onCreate}>
          <label className="field">
            유형
            <select name="doc_type" required>
              {Object.entries(DOC_TYPE_LABELS).map(([value, label]) => (
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
            버전
            <input name="version" defaultValue="1.0" />
          </label>
          <label className="field">
            링크 URL
            <input name="file_url" placeholder="https://..." />
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
            <th style={{ width: 110 }}>버전</th>
            <th>작성자</th>
            <th>수정일</th>
          </tr>
        </thead>
        <tbody>
          {docs.data?.map((doc) => (
            <tr key={doc.id}>
              <td>
                {doc.file_url ? (
                  <a href={doc.file_url} target="_blank" rel="noreferrer">
                    {doc.title}
                  </a>
                ) : (
                  doc.title
                )}
              </td>
              <td>{DOC_TYPE_LABELS[doc.doc_type]}</td>
              <td>
                {canEdit ? (
                  <input
                    defaultValue={doc.version}
                    style={{ width: 80 }}
                    onBlur={(e) => {
                      if (e.target.value && e.target.value !== doc.version) {
                        versionMutation.mutate({ docId: doc.id, version: e.target.value });
                      }
                    }}
                  />
                ) : (
                  doc.version
                )}
              </td>
              <td>{doc.author_name}</td>
              <td>{new Date(doc.updated_at).toLocaleDateString("ko-KR")}</td>
            </tr>
          ))}
          {docs.data?.length === 0 && (
            <tr>
              <td colSpan={5}>등록된 문서가 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
