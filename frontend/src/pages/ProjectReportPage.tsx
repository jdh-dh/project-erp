import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { fetchProjectReport } from "../api/erp";
import StatusBadge from "../components/StatusBadge";
import { TYPE_LABELS } from "../utils/labels";

function won(value: string): string {
  return `${Number(value).toLocaleString()}원`;
}

const COST_LABELS: Record<string, string> = {
  LABOR: "인건비",
  MATERIAL: "자재비",
  OUTSOURCING: "외주비",
  EQUIPMENT: "장비비",
  ETC: "기타",
};

export default function ProjectReportPage() {
  const { id } = useParams();
  const projectId = Number(id);

  const report = useQuery({
    queryKey: ["report", projectId],
    queryFn: () => fetchProjectReport(projectId),
  });

  if (report.isLoading) return <p>보고서 생성 중…</p>;
  if (!report.data) return <p>보고서를 불러올 수 없습니다.</p>;
  const data = report.data;

  return (
    <div>
      <div className="toolbar" style={{ justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>
          프로젝트 보고서 — [{data.project.code}] {data.project.name}{" "}
          <StatusBadge status={data.project.status} />
        </h2>
        <div>
          <button className="secondary" onClick={() => window.print()}>
            인쇄
          </button>{" "}
          <Link to={`/projects/${projectId}`}>
            <button>상세로 돌아가기</button>
          </Link>
        </div>
      </div>

      <div className="card">
        <h3>기본 정보</h3>
        <table className="grid">
          <tbody>
            <tr>
              <th>고객사</th>
              <td>{data.project.customer_name}</td>
              <th>유형</th>
              <td>{TYPE_LABELS[data.project.project_type]}</td>
            </tr>
            <tr>
              <th>PM</th>
              <td>{data.project.manager_name}</td>
              <th>기간</th>
              <td>
                {data.project.start_date ?? "-"} ~ {data.project.end_date ?? "-"}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>일정 현황</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>전체 진척률</th>
              <th>WBS 항목</th>
              <th>WBS 지연</th>
              <th>마일스톤</th>
              <th>마일스톤 지연</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <b>{data.schedule.progress}%</b>
              </td>
              <td>{data.schedule.wbs_total}건</td>
              <td>{data.schedule.wbs_delayed}건</td>
              <td>{data.schedule.milestone_total}건</td>
              <td>{data.schedule.milestone_delayed}건</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>이슈 현황</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>전체</th>
              <th>접수</th>
              <th>처리중</th>
              <th>해결</th>
              <th>종료</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{data.issues.total}건</td>
              <td>{data.issues.open}건</td>
              <td>{data.issues.in_progress}건</td>
              <td>{data.issues.resolved}건</td>
              <td>{data.issues.closed}건</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>시험 현황 (최근 결과 기준)</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>전체</th>
              <th>합격</th>
              <th>불합격</th>
              <th>보류</th>
              <th>미실행</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{data.tests.total}건</td>
              <td>{data.tests.passed}건</td>
              <td>{data.tests.failed}건</td>
              <td>{data.tests.blocked}건</td>
              <td>{data.tests.not_run}건</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>하드웨어 / 소프트웨어 / 릴리즈</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>보드</th>
              <th>SW 모듈</th>
              <th>SW 버전</th>
              <th>릴리즈된 버전</th>
              <th>릴리즈 이력</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{data.hardware.boards}건</td>
              <td>{data.software.modules}건</td>
              <td>{data.software.versions}건</td>
              <td>{data.software.released_versions}건</td>
              <td>{data.releases}건</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>비용 현황</h3>
        <table className="grid">
          <thead>
            <tr>
              <th>총액</th>
              {Object.keys(data.costs.by_category).map((category) => (
                <th key={category}>{COST_LABELS[category] ?? category}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>
                <b>{won(data.costs.total)}</b>
              </td>
              {Object.values(data.costs.by_category).map((amount, i) => (
                <td key={i}>{won(amount)}</td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
