import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { errorMessage } from "../api/client";
import {
  addBomItem,
  addFabrication,
  createBoard,
  fetchBoard,
  fetchBoards,
  updateBoard,
} from "../api/erp";
import { useAuth } from "../auth/AuthContext";
import type { BoardStatus } from "../types";

const BOARD_STATUS_LABELS: Record<BoardStatus, string> = {
  DESIGN: "설계",
  PROTOTYPE: "시제",
  PRODUCTION: "양산",
  OBSOLETE: "단종",
};

function BoardDetail({ projectId, boardId }: { projectId: number; boardId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");

  const board = useQuery({
    queryKey: ["hw-board", projectId, boardId],
    queryFn: () => fetchBoard(projectId, boardId),
  });

  function invalidate() {
    queryClient.invalidateQueries({ queryKey: ["hw-board", projectId, boardId] });
    setError("");
  }
  const onError = (err: unknown) => setError(errorMessage(err));

  const bomMutation = useMutation({
    mutationFn: (body: Parameters<typeof addBomItem>[2]) =>
      addBomItem(projectId, boardId, body),
    onSuccess: invalidate,
    onError,
  });
  const fabMutation = useMutation({
    mutationFn: (body: Parameters<typeof addFabrication>[2]) =>
      addFabrication(projectId, boardId, body),
    onSuccess: invalidate,
    onError,
  });

  function onAddBom(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    bomMutation.mutate({
      part_name: String(form.get("part_name")),
      part_number: String(form.get("part_number")) || undefined,
      manufacturer: String(form.get("manufacturer")) || undefined,
      quantity: Number(form.get("quantity")) || 1,
      reference: String(form.get("reference")) || undefined,
    });
    e.currentTarget.reset();
  }

  function onAddFab(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    fabMutation.mutate({
      fab_date: String(form.get("fab_date")),
      quantity: Number(form.get("quantity")) || 1,
      vendor: String(form.get("vendor")) || undefined,
    });
    e.currentTarget.reset();
  }

  if (!board.data) return <p>불러오는 중…</p>;

  return (
    <div style={{ padding: "8px 0 8px 24px" }}>
      {error && <div className="error">{error}</div>}
      <h4 style={{ margin: "8px 0" }}>BOM (부품 목록)</h4>
      <table className="grid">
        <thead>
          <tr>
            <th>부품명</th>
            <th>부품번호</th>
            <th>제조사</th>
            <th>수량</th>
            <th>위치기호</th>
          </tr>
        </thead>
        <tbody>
          {board.data.bom_items.map((item) => (
            <tr key={item.id}>
              <td>{item.part_name}</td>
              <td>{item.part_number ?? "-"}</td>
              <td>{item.manufacturer ?? "-"}</td>
              <td>{item.quantity}</td>
              <td>{item.reference ?? "-"}</td>
            </tr>
          ))}
          {board.data.bom_items.length === 0 && (
            <tr>
              <td colSpan={5}>등록된 부품이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {canEdit && (
        <form className="inline" style={{ marginTop: 8 }} onSubmit={onAddBom}>
          <label className="field">
            부품명
            <input name="part_name" required />
          </label>
          <label className="field">
            부품번호
            <input name="part_number" />
          </label>
          <label className="field">
            제조사
            <input name="manufacturer" />
          </label>
          <label className="field">
            수량
            <input name="quantity" type="number" min={1} defaultValue={1} required />
          </label>
          <label className="field">
            위치기호
            <input name="reference" placeholder="U1, R1-R8" />
          </label>
          <button type="submit" disabled={bomMutation.isPending}>
            부품 추가
          </button>
        </form>
      )}

      <h4 style={{ margin: "16px 0 8px" }}>제작 이력</h4>
      <table className="grid">
        <thead>
          <tr>
            <th>제작일</th>
            <th>수량</th>
            <th>제작처</th>
            <th>결과</th>
          </tr>
        </thead>
        <tbody>
          {board.data.fabrications.map((fab) => (
            <tr key={fab.id}>
              <td>{fab.fab_date}</td>
              <td>{fab.quantity}</td>
              <td>{fab.vendor ?? "-"}</td>
              <td>{fab.result}</td>
            </tr>
          ))}
          {board.data.fabrications.length === 0 && (
            <tr>
              <td colSpan={4}>제작 이력이 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {canEdit && (
        <form className="inline" style={{ marginTop: 8 }} onSubmit={onAddFab}>
          <label className="field">
            제작일
            <input name="fab_date" type="date" required />
          </label>
          <label className="field">
            수량
            <input name="quantity" type="number" min={1} defaultValue={1} required />
          </label>
          <label className="field">
            제작처
            <input name="vendor" />
          </label>
          <button type="submit" disabled={fabMutation.isPending}>
            제작 이력 추가
          </button>
        </form>
      )}
    </div>
  );
}

export default function HwSection({ projectId }: { projectId: number }) {
  const { user } = useAuth();
  const canEdit = user?.role === "admin" || user?.role === "manager";
  const queryClient = useQueryClient();
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const boards = useQuery({
    queryKey: ["hw-boards", projectId],
    queryFn: () => fetchBoards(projectId),
  });

  const createMutation = useMutation({
    mutationFn: (body: { name: string; revision: string; description?: string }) =>
      createBoard(projectId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hw-boards", projectId] });
      setShowForm(false);
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  const statusMutation = useMutation({
    mutationFn: ({ boardId, status }: { boardId: number; status: BoardStatus }) =>
      updateBoard(projectId, boardId, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hw-boards", projectId] });
      setError("");
    },
    onError: (err) => setError(errorMessage(err)),
  });

  function onCreate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = new FormData(e.currentTarget);
    createMutation.mutate({
      name: String(form.get("name")),
      revision: String(form.get("revision")),
      description: String(form.get("description")) || undefined,
    });
  }

  return (
    <div className="card">
      <h3>하드웨어 (보드)</h3>
      {error && <div className="error">{error}</div>}
      <table className="grid">
        <thead>
          <tr>
            <th>보드명</th>
            <th>리비전</th>
            <th>상태</th>
          </tr>
        </thead>
        <tbody>
          {boards.data?.map((board) => (
            <tr key={board.id}>
              <td>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    setExpandedId(expandedId === board.id ? null : board.id);
                  }}
                >
                  {expandedId === board.id ? "▼" : "▶"} {board.name}
                </a>
              </td>
              <td>{board.revision}</td>
              <td>
                {canEdit ? (
                  <select
                    value={board.status}
                    onChange={(e) =>
                      statusMutation.mutate({
                        boardId: board.id,
                        status: e.target.value as BoardStatus,
                      })
                    }
                  >
                    {Object.entries(BOARD_STATUS_LABELS).map(([value, label]) => (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    ))}
                  </select>
                ) : (
                  BOARD_STATUS_LABELS[board.status]
                )}
              </td>
            </tr>
          ))}
          {boards.data?.length === 0 && (
            <tr>
              <td colSpan={3}>등록된 보드가 없습니다.</td>
            </tr>
          )}
        </tbody>
      </table>
      {expandedId != null && <BoardDetail projectId={projectId} boardId={expandedId} />}
      {canEdit && (
        <div style={{ marginTop: 12 }}>
          <button onClick={() => setShowForm((v) => !v)}>
            {showForm ? "닫기" : "+ 보드 등록"}
          </button>
          {showForm && (
            <form className="inline" style={{ marginTop: 12 }} onSubmit={onCreate}>
              <label className="field">
                보드명
                <input name="name" required />
              </label>
              <label className="field">
                리비전
                <input name="revision" placeholder="A0" required />
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
