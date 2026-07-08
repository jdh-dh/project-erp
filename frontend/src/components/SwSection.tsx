import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import {
  addBuild,
  addDeployment,
  createModule,
  createVersion,
  fetchModule,
  fetchModules,
  fetchVersion,
  releaseVersion,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { ModuleType, VersionStatus } from "../types";

const MODULE_TYPE_LABELS: Record<ModuleType, string> = {
  FIRMWARE: "펌웨어",
  APP: "앱",
  SERVER: "서버",
  LIBRARY: "라이브러리",
};

const VERSION_STATUS_LABELS: Record<VersionStatus, string> = {
  DEVELOP: "개발중",
  RELEASED: "릴리즈",
  DEPRECATED: "중단",
};

function VersionDetail({
  projectId,
  moduleId,
  versionId,
}: {
  projectId: number;
  moduleId: number;
  versionId: number;
}) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const version = useQuery({
    queryKey: ["sw-version", projectId, moduleId, versionId],
    queryFn: () => fetchVersion(projectId, moduleId, versionId),
  });

  function invalidate() {
    queryClient.invalidateQueries({
      queryKey: ["sw-version", projectId, moduleId, versionId],
    });
    setError("");
  }
  const onError = (err: unknown) => setError(errorMessage(err));

  const buildMutation = useMutation({
    mutationFn: (body: Parameters<typeof addBuild>[3]) =>
      addBuild(projectId, moduleId, versionId, body),
    onSuccess: invalidate,
    onError,
  });
  const deployMutation = useMutation({
    mutationFn: (body: Parameters<typeof addDeployment>[3]) =>
      addDeployment(projectId, moduleId, versionId, body),
    onSuccess: invalidate,
    onError,
  });

  function onAddBuild(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    buildMutation.mutate({
      build_no: String(form.get("build_no")),
      commit_hash: String(form.get("commit_hash")) || undefined,
      result: String(form.get("result")),
    });
    e.currentTarget.reset();
  }

  function onAddDeploy(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    deployMutation.mutate({
      environment: String(form.get("environment")),
      note: String(form.get("note")) || undefined,
    });
    e.currentTarget.reset();
  }

  if (!version.data) return <p>불러오는 중…</p>;

  return (
    <div style={{ padding: "8px 0 8px 24px" }}>
      {error && <div className="error">{error}</div>}
      <h4 style={{ margin: "8px 0" }}>빌드 이력</h4>
      <table className="grid">
        <thead>
          <tr>
            <th>빌드 번호</th>
            <th>커밋 해시</th>
            <th>일시</th>
            <th>결과</th>
          </tr>
        </thead>
        <tbody>
          {version.data.builds.map((build) => (
            <tr key={build.id}>
              <td>{build.build_no}</td>
              <td>{build.commit_hash ?? "-"}</td>
              <td>{new Date(build.built_at).toLocaleString("ko-KR")}</td>
              <td>
                <span className={`badge ${build.result === "SUCCESS" ? "active" : "inactive"}`}>
                  {build.result === "SUCCESS" ? "성공" : "실패"}
                </span>
              </td>
            </tr>
          ))}
          {version.data.builds.length === 0 && (
            <tr>
              <td colSpan={4}>빌드 이력이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {canEdit && (
        <form className="inline" style={{ marginTop: 8 }} onSubmit={onAddBuild}>
          <label className="field">
            빌드 번호
            <input name="build_no" required />
          </label>
          <label className="field">
            커밋 해시
            <input name="commit_hash" placeholder="abc1234" />
          </label>
          <label className="field">
            결과
            <select name="result" defaultValue="SUCCESS">
              <option value="SUCCESS">성공</option>
              <option value="FAIL">실패</option>
            </select>
          </label>
          <button type="submit" disabled={buildMutation.isPending}>
            빌드 추가
          </button>
        </form>
      )}

      <h4 style={{ margin: "16px 0 8px" }}>배포 이력</h4>
      <table className="grid">
        <thead>
          <tr>
            <th>환경</th>
            <th>배포일시</th>
            <th>비고</th>
          </tr>
        </thead>
        <tbody>
          {version.data.deployments.map((dep) => (
            <tr key={dep.id}>
              <td>{dep.environment}</td>
              <td>{new Date(dep.deployed_at).toLocaleString("ko-KR")}</td>
              <td>{dep.note ?? "-"}</td>
            </tr>
          ))}
          {version.data.deployments.length === 0 && (
            <tr>
              <td colSpan={3}>배포 이력이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {canEdit && (
        <form className="inline" style={{ marginTop: 8 }} onSubmit={onAddDeploy}>
          <label className="field">
            환경
            <select name="environment" defaultValue="DEV">
              <option value="DEV">DEV</option>
              <option value="STAGE">STAGE</option>
              <option value="PROD">PROD</option>
              <option value="FIELD">FIELD(현장)</option>
            </select>
          </label>
          <label className="field">
            비고
            <input name="note" />
          </label>
          <button type="submit" disabled={deployMutation.isPending}>
            배포 추가
          </button>
        </form>
      )}
    </div>
  );
}

function ModuleDetail({ projectId, moduleId }: { projectId: number; moduleId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [expandedVersionId, setExpandedVersionId] = useState<number | null>(null);

  const module = useQuery({
    queryKey: ["sw-module", projectId, moduleId],
    queryFn: () => fetchModule(projectId, moduleId),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["sw-module", projectId, moduleId] });
    setError("");
  }
  const onError = (err: unknown) => setError(errorMessage(err));

  const versionMutation = useMutation({
    mutationFn: (body: { version: string; note?: string }) =>
      createVersion(projectId, moduleId, body),
    onSuccess: invalidate,
    onError,
  });
  const releaseMutation = useMutation({
    mutationFn: (versionId: number) => releaseVersion(projectId, moduleId, versionId),
    onSuccess: (_, versionId) => {
      invalidate();
      queryClient.invalidateQueries({
        queryKey: ["sw-version", projectId, moduleId, versionId],
      });
    },
    onError,
  });

  function onAddVersion(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    versionMutation.mutate({
      version: String(form.get("version")),
      note: String(form.get("note")) || undefined,
    });
    e.currentTarget.reset();
  }

  if (!module.data) return <p>불러오는 중…</p>;

  return (
    <div style={{ padding: "8px 0 8px 24px" }}>
      {error && <div className="error">{error}</div>}
      <h4 style={{ margin: "8px 0" }}>버전</h4>
      <table className="grid">
        <thead>
          <tr>
            <th>버전</th>
            <th>상태</th>
            <th>릴리즈일</th>
            <th>변경 내용</th>
            {canEdit && <th></th>}
          </tr>
        </thead>
        <tbody>
          {module.data.versions.map((version) => (
            <tr key={version.id}>
              <td>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setExpandedVersionId(
                      expandedVersionId === version.id ? null : version.id
                    );
                  }}
                >
                  {expandedVersionId === version.id ? "▼" : "▶"} {version.version}
                </a>
              </td>
              <td>
                <span className={`badge ${version.status === "RELEASED" ? "active" : ""}`}>
                  {VERSION_STATUS_LABELS[version.status]}
                </span>
              </td>
              <td>{version.released_date ?? "-"}</td>
              <td>{version.note ?? "-"}</td>
              {canEdit && (
                <td>
                  {version.status === "DEVELOP" && (
                    <button
                      disabled={releaseMutation.isPending}
                      onClick={() => releaseMutation.mutate(version.id)}
                    >
                      릴리즈
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
          {module.data.versions.length === 0 && (
            <tr>
              <td colSpan={5}>등록된 버전이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {expandedVersionId != null && (
        <VersionDetail
          projectId={projectId}
          moduleId={moduleId}
          versionId={expandedVersionId}
        />
      )}
      {canEdit && (
        <form className="inline" style={{ marginTop: 8 }} onSubmit={onAddVersion}>
          <label className="field">
            버전
            <input name="version" placeholder="1.0.0" required />
          </label>
          <label className="field">
            변경 내용
            <input name="note" />
          </label>
          <button type="submit" disabled={versionMutation.isPending}>
            버전 추가
          </button>
        </form>
      )}
    </div>
  );
}

export default function SwSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const modules = useQuery({
    queryKey: ["sw-modules", projectId],
    queryFn: () => fetchModules(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (body: Parameters<typeof createModule>[1]) =>
      createModule(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sw-modules", projectId] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      name: String(form.get("name")),
      module_type: String(form.get("module_type")) as ModuleType,
      repo_url: String(form.get("repo_url")) || undefined,
      description: String(form.get("description")) || undefined,
    });
  }

  return (
    <div className="card">
      <h3>소프트웨어 (모듈)</h3>
      {error && <div className="error">{error}</div>}
      <table className="grid">
        <thead>
          <tr>
            <th>모듈명</th>
            <th>유형</th>
            <th>GitHub 저장소</th>
          </tr>
        </thead>
        <tbody>
          {modules.data?.map((module) => (
            <tr key={module.id}>
              <td>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setExpandedId(expandedId === module.id ? null : module.id);
                  }}
                >
                  {expandedId === module.id ? "▼" : "▶"} {module.name}
                </a>
              </td>
              <td>{MODULE_TYPE_LABELS[module.module_type]}</td>
              <td>
                {module.repo_url ? (
                  <a href={module.repo_url} target="_blank" rel="noreferrer">
                    {module.repo_url}
                  </a>
                ) : (
                  "-"
                )}
              </td>
            </tr>
          ))}
          {modules.data?.length === 0 && (
            <tr>
              <td colSpan={3}>등록된 모듈이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {expandedId != null && <ModuleDetail projectId={projectId} moduleId={expandedId} />}
      {canEdit && (
        <div style={{ marginTop: 12 }}>
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 모듈 등록"}
          </button>
          {showForm && (
            <form className="inline" style={{ marginTop: 12 }} onSubmit={onCreate}>
              <label className="field">
                모듈명
                <input name="name" required />
              </label>
              <label className="field">
                유형
                <select name="module_type" required>
                  {Object.entries(MODULE_TYPE_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="field">
                GitHub 저장소 URL
                <input name="repo_url" placeholder="https://github.com/..." />
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
        </div>
      )}
    </div>
  );
}
