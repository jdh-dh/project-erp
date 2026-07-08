import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import { addTestRun, createTestCase, fetchTestCase, fetchTestCases } from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { TestResult, TestType } from "../types";

const TEST_TYPE_LABELS: Record<TestType, string> = {
  UNIT: "단위",
  INTEGRATION: "통합",
  FIELD: "현장",
};

const RESULT_LABELS: Record<TestResult, string> = {
  PASS: "합격",
  FAIL: "불합격",
  BLOCKED: "보류",
};

function ResultBadge({ result }: { result: TestResult | null }) {
  if (!result) return <span>-</span>;
  const cls = result === "PASS" ? "active" : result === "FAIL" ? "inactive" : "";
  return <span className={`badge ${cls}`}>{RESULT_LABELS[result]}</span>;
}

function CaseDetail({ projectId, caseId }: { projectId: number; caseId: number }) {
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const testCase = useQuery({
    queryKey: ["test-case", projectId, caseId],
    queryFn: () => fetchTestCase(projectId, caseId),
  });

  const runMutation = useMutation({
    mutationFn: (body: Parameters<typeof addTestRun>[2]) =>
      addTestRun(projectId, caseId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["test-case", projectId, caseId] });
      queryClient.invalidateQueries({ queryKey: ["test-cases", projectId] });
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onAddRun(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    runMutation.mutate({
      run_date: String(form.get("run_date")),
      result: String(form.get("result")) as TestResult,
      note: String(form.get("note")) || undefined,
    });
    e.currentTarget.reset();
  }

  if (!testCase.data) return <p>불러오는 중…</p>;

  return (
    <div style={{ padding: "8px 0 8px 24px" }}>
      {error && <div className="error">{error}</div>}
      {testCase.data.expected_result && (
        <p style={{ fontSize: 13, margin: "4px 0" }}>
          기대 결과: {testCase.data.expected_result}
        </p>
      )}
      <h4 style={{ margin: "8px 0" }}>실행 이력</h4>
      <table className="grid">
        <thead>
          <tr>
            <th>실행일</th>
            <th>결과</th>
            <th>시험자</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          {testCase.data.runs.map((run) => (
            <tr key={run.id}>
              <td>{run.run_date}</td>
              <td>
                <ResultBadge result={run.result} />
              </td>
              <td>{run.tester_name}</td>
              <td>{run.note ?? "-"}</td>
            </tr>
          ))}
          {testCase.data.runs.length === 0 && (
            <tr>
              <td colSpan={4}>실행 이력이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      <form className="inline" style={{ marginTop: 8 }} onSubmit={onAddRun}>
        <label className="field">
          실행일
          <input name="run_date" type="date" required />
        </label>
        <label className="field">
          결과
          <select name="result" defaultValue="PASS">
            {Object.entries(RESULT_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          비고
          <input name="note" />
        </label>
        <button type="submit" disabled={runMutation.isPending}>
          결과 기록
        </button>
      </form>
    </div>
  );
}

export default function TestSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [typeFilter, setTypeFilter] = useState("");
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const cases = useQuery({
    queryKey: ["test-cases", projectId, typeFilter],
    queryFn: () => fetchTestCases(projectId, typeFilter),
  });

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createTestCase>[1]) =>
      createTestCase(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["test-cases", projectId] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      test_type: String(form.get("test_type")) as TestType,
      name: String(form.get("name")),
      expected_result: String(form.get("expected_result")) || undefined,
    });
  }

  return (
    <div className="card">
      <h3>시험 관리</h3>
      {error && <div className="error">{error}</div>}
      <div className="toolbar">
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">전체 유형</option>
          {Object.entries(TEST_TYPE_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}시험
            </option>
          ))}
        </select>
        {canEdit && (
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 시험 케이스 등록"}
          </button>
        )}
      </div>
      {showForm && (
        <form className="inline" style={{ marginBottom: 12 }} onSubmit={onCreate}>
          <label className="field">
            유형
            <select name="test_type" required>
              {Object.entries(TEST_TYPE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}시험
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            케이스명
            <input name="name" required />
          </label>
          <label className="field">
            기대 결과
            <input name="expected_result" />
          </label>
          <button type="submit" disabled={createMutation.isPending}>
            등록
          </button>
        </form>
      )}
      <table className="grid">
        <thead>
          <tr>
            <th>케이스명</th>
            <th>유형</th>
            <th>최근 결과</th>
          </tr>
        </thead>
        <tbody>
          {cases.data?.map((testCase) => (
            <tr key={testCase.id}>
              <td>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setExpandedId(expandedId === testCase.id ? null : testCase.id);
                  }}
                >
                  {expandedId === testCase.id ? "▼" : "▶"} {testCase.name}
                </a>
              </td>
              <td>{TEST_TYPE_LABELS[testCase.test_type]}시험</td>
              <td>
                <ResultBadge result={testCase.last_result} />
              </td>
            </tr>
          ))}
          {cases.data?.length === 0 && (
            <tr>
              <td colSpan={3}>등록된 시험 케이스가 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {expandedId != null && <CaseDetail projectId={projectId} caseId={expandedId} />}
    </div>
  );
}
