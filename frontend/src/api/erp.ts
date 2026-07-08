import client, { setTokens } from "./client";
import type {
  BoardStatus,
  BomItem,
  ChangeLog,
  Contact,
  Contract,
  Customer,
  CustomerDetail,
  Fabrication,
  HwBoard,
  HwBoardDetail,
  Milestone,
  ModuleType,
  Page,
  Project,
  ProjectDetail,
  ProjectStatus,
  ScheduleSummary,
  SwBuild,
  SwDeployment,
  SwModule,
  SwModuleDetail,
  CostCategory,
  CostSummary,
  DocType,
  Issue,
  IssueDetail,
  IssueSeverity,
  IssueStatus,
  IssueType,
  ProjectCost,
  ProjectDocument,
  ProjectReport,
  Release,
  SwVersion,
  SwVersionDetail,
  TestCase,
  TestCaseDetail,
  TestResult,
  TestRun,
  TestType,
  User,
  WbsItem,
  WbsStatus,
} from "../types";

// ---- auth ----
export async function login(email: string, password: string): Promise<void> {
  const res = await client.post("/auth/login", { email, password });
  setTokens(res.data.access_token, res.data.refresh_token);
}

export async function fetchMe(): Promise<User> {
  return (await client.get("/auth/me")).data;
}

// ---- users ----
export async function fetchUsers(page = 1, size = 100): Promise<Page<User>> {
  return (await client.get("/users", { params: { page, size } })).data;
}

export async function createUser(body: {
  email: string;
  password: string;
  name: string;
  role: string;
}): Promise<User> {
  return (await client.post("/users", body)).data;
}

export async function deactivateUser(id: number): Promise<User> {
  return (await client.patch(`/users/${id}/deactivate`)).data;
}

// ---- customers ----
export async function fetchCustomers(q = "", page = 1, size = 100): Promise<Page<Customer>> {
  return (await client.get("/customers", { params: { q: q || undefined, page, size } })).data;
}

export async function fetchCustomer(id: number): Promise<CustomerDetail> {
  return (await client.get(`/customers/${id}`)).data;
}

export async function createCustomer(body: {
  name: string;
  business_no?: string;
  address?: string;
  note?: string;
}): Promise<CustomerDetail> {
  return (await client.post("/customers", body)).data;
}

export async function updateCustomer(
  id: number,
  body: Partial<Pick<Customer, "name" | "business_no" | "address" | "note">>
): Promise<CustomerDetail> {
  return (await client.patch(`/customers/${id}`, body)).data;
}

export async function deactivateCustomer(id: number): Promise<CustomerDetail> {
  return (await client.patch(`/customers/${id}/deactivate`)).data;
}

export async function addContact(
  customerId: number,
  body: { name: string; position?: string; phone?: string; email?: string }
): Promise<Contact> {
  return (await client.post(`/customers/${customerId}/contacts`, body)).data;
}

// ---- projects ----
export async function fetchProjects(params: {
  status?: string;
  customer_id?: number;
  q?: string;
  page?: number;
  size?: number;
}): Promise<Page<Project>> {
  return (await client.get("/projects", { params })).data;
}

export async function fetchProject(id: number): Promise<ProjectDetail> {
  return (await client.get(`/projects/${id}`)).data;
}

export async function createProject(body: {
  code: string;
  name: string;
  customer_id: number;
  project_type: string;
  manager_id: number;
  start_date?: string | null;
  end_date?: string | null;
  description?: string | null;
}): Promise<ProjectDetail> {
  return (await client.post("/projects", body)).data;
}

export async function changeProjectStatus(
  id: number,
  status: ProjectStatus
): Promise<ProjectDetail> {
  return (await client.patch(`/projects/${id}/status`, { status })).data;
}

export async function setProjectMembers(
  id: number,
  members: { user_id: number; role?: string | null }[]
): Promise<ProjectDetail> {
  return (await client.put(`/projects/${id}/members`, { members })).data;
}

export async function addContract(
  projectId: number,
  body: {
    contract_no: string;
    amount?: string;
    signed_date?: string;
    start_date?: string;
    end_date?: string;
    note?: string;
  }
): Promise<Contract> {
  return (await client.post(`/projects/${projectId}/contracts`, body)).data;
}

// ---- schedule (WBS / milestones) ----
export async function fetchWbs(projectId: number): Promise<WbsItem[]> {
  return (await client.get(`/projects/${projectId}/wbs`)).data;
}

export async function createWbs(
  projectId: number,
  body: {
    name: string;
    parent_id?: number | null;
    assignee_id?: number | null;
    start_date?: string | null;
    end_date?: string | null;
  }
): Promise<WbsItem> {
  return (await client.post(`/projects/${projectId}/wbs`, body)).data;
}

export async function updateWbs(
  projectId: number,
  itemId: number,
  body: Partial<{
    name: string;
    parent_id: number | null;
    assignee_id: number | null;
    start_date: string | null;
    end_date: string | null;
    progress: number;
    status: WbsStatus;
  }>
): Promise<WbsItem> {
  return (await client.patch(`/projects/${projectId}/wbs/${itemId}`, body)).data;
}

export async function deactivateWbs(projectId: number, itemId: number): Promise<void> {
  await client.patch(`/projects/${projectId}/wbs/${itemId}/deactivate`);
}

export async function fetchMilestones(projectId: number): Promise<Milestone[]> {
  return (await client.get(`/projects/${projectId}/milestones`)).data;
}

export async function createMilestone(
  projectId: number,
  body: { name: string; due_date: string; note?: string }
): Promise<Milestone> {
  return (await client.post(`/projects/${projectId}/milestones`, body)).data;
}

export async function achieveMilestone(
  projectId: number,
  msId: number
): Promise<Milestone> {
  return (await client.patch(`/projects/${projectId}/milestones/${msId}/achieve`)).data;
}

export async function fetchScheduleSummary(
  projectId: number
): Promise<ScheduleSummary> {
  return (await client.get(`/projects/${projectId}/schedule/summary`)).data;
}

// ---- hardware ----
export async function fetchBoards(projectId: number): Promise<HwBoard[]> {
  return (await client.get(`/projects/${projectId}/hw/boards`)).data;
}

export async function fetchBoard(
  projectId: number,
  boardId: number
): Promise<HwBoardDetail> {
  return (await client.get(`/projects/${projectId}/hw/boards/${boardId}`)).data;
}

export async function createBoard(
  projectId: number,
  body: { name: string; revision: string; description?: string }
): Promise<HwBoardDetail> {
  return (await client.post(`/projects/${projectId}/hw/boards`, body)).data;
}

export async function updateBoard(
  projectId: number,
  boardId: number,
  body: Partial<{ name: string; revision: string; status: BoardStatus; description: string }>
): Promise<HwBoardDetail> {
  return (await client.patch(`/projects/${projectId}/hw/boards/${boardId}`, body)).data;
}

export async function addBomItem(
  projectId: number,
  boardId: number,
  body: {
    part_name: string;
    part_number?: string;
    manufacturer?: string;
    quantity: number;
    reference?: string;
  }
): Promise<BomItem> {
  return (await client.post(`/projects/${projectId}/hw/boards/${boardId}/bom`, body)).data;
}

export async function addFabrication(
  projectId: number,
  boardId: number,
  body: { fab_date: string; quantity: number; vendor?: string; result?: string }
): Promise<Fabrication> {
  return (
    await client.post(`/projects/${projectId}/hw/boards/${boardId}/fabrications`, body)
  ).data;
}

// ---- software ----
export async function fetchModules(projectId: number): Promise<SwModule[]> {
  return (await client.get(`/projects/${projectId}/sw/modules`)).data;
}

export async function fetchModule(
  projectId: number,
  moduleId: number
): Promise<SwModuleDetail> {
  return (await client.get(`/projects/${projectId}/sw/modules/${moduleId}`)).data;
}

export async function createModule(
  projectId: number,
  body: { name: string; module_type: ModuleType; repo_url?: string; description?: string }
): Promise<SwModuleDetail> {
  return (await client.post(`/projects/${projectId}/sw/modules`, body)).data;
}

export async function createVersion(
  projectId: number,
  moduleId: number,
  body: { version: string; note?: string }
): Promise<SwVersion> {
  return (
    await client.post(`/projects/${projectId}/sw/modules/${moduleId}/versions`, body)
  ).data;
}

export async function fetchVersion(
  projectId: number,
  moduleId: number,
  versionId: number
): Promise<SwVersionDetail> {
  return (
    await client.get(`/projects/${projectId}/sw/modules/${moduleId}/versions/${versionId}`)
  ).data;
}

export async function releaseVersion(
  projectId: number,
  moduleId: number,
  versionId: number
): Promise<SwVersion> {
  return (
    await client.patch(
      `/projects/${projectId}/sw/modules/${moduleId}/versions/${versionId}/release`
    )
  ).data;
}

export async function addBuild(
  projectId: number,
  moduleId: number,
  versionId: number,
  body: { build_no: string; commit_hash?: string; result?: string; note?: string }
): Promise<SwBuild> {
  return (
    await client.post(
      `/projects/${projectId}/sw/modules/${moduleId}/versions/${versionId}/builds`,
      body
    )
  ).data;
}

export async function addDeployment(
  projectId: number,
  moduleId: number,
  versionId: number,
  body: { environment: string; note?: string }
): Promise<SwDeployment> {
  return (
    await client.post(
      `/projects/${projectId}/sw/modules/${moduleId}/versions/${versionId}/deployments`,
      body
    )
  ).data;
}

// ---- test cases ----
export async function fetchTestCases(
  projectId: number,
  testType?: string
): Promise<TestCase[]> {
  return (
    await client.get(`/projects/${projectId}/test-cases`, {
      params: { test_type: testType || undefined },
    })
  ).data;
}

export async function fetchTestCase(
  projectId: number,
  caseId: number
): Promise<TestCaseDetail> {
  return (await client.get(`/projects/${projectId}/test-cases/${caseId}`)).data;
}

export async function createTestCase(
  projectId: number,
  body: { test_type: TestType; name: string; description?: string; expected_result?: string }
): Promise<TestCaseDetail> {
  return (await client.post(`/projects/${projectId}/test-cases`, body)).data;
}

export async function addTestRun(
  projectId: number,
  caseId: number,
  body: { run_date: string; result: TestResult; note?: string }
): Promise<TestRun> {
  return (
    await client.post(`/projects/${projectId}/test-cases/${caseId}/runs`, body)
  ).data;
}

// ---- issues ----
export async function fetchIssues(
  projectId: number,
  filters: { status?: string; issue_type?: string } = {}
): Promise<Issue[]> {
  return (
    await client.get(`/projects/${projectId}/issues`, {
      params: {
        status: filters.status || undefined,
        issue_type: filters.issue_type || undefined,
      },
    })
  ).data;
}

export async function fetchIssue(
  projectId: number,
  issueId: number
): Promise<IssueDetail> {
  return (await client.get(`/projects/${projectId}/issues/${issueId}`)).data;
}

export async function createIssue(
  projectId: number,
  body: {
    issue_type: IssueType;
    title: string;
    description?: string;
    severity?: IssueSeverity;
    assignee_id?: number | null;
  }
): Promise<IssueDetail> {
  return (await client.post(`/projects/${projectId}/issues`, body)).data;
}

export async function updateIssue(
  projectId: number,
  issueId: number,
  body: Partial<{
    title: string;
    description: string;
    severity: IssueSeverity;
    assignee_id: number | null;
    cause_analysis: string;
    resolution: string;
  }>
): Promise<IssueDetail> {
  return (await client.patch(`/projects/${projectId}/issues/${issueId}`, body)).data;
}

export async function changeIssueStatus(
  projectId: number,
  issueId: number,
  status: IssueStatus,
  resolution?: string
): Promise<IssueDetail> {
  return (
    await client.patch(`/projects/${projectId}/issues/${issueId}/status`, {
      status,
      resolution,
    })
  ).data;
}

// ---- documents ----
export async function fetchDocuments(
  projectId: number,
  docType?: string
): Promise<ProjectDocument[]> {
  return (
    await client.get(`/projects/${projectId}/documents`, {
      params: { doc_type: docType || undefined },
    })
  ).data;
}

export async function createDocument(
  projectId: number,
  body: {
    doc_type: DocType;
    title: string;
    version?: string;
    file_url?: string;
    description?: string;
  }
): Promise<ProjectDocument> {
  return (await client.post(`/projects/${projectId}/documents`, body)).data;
}

export async function updateDocument(
  projectId: number,
  docId: number,
  body: Partial<{ title: string; version: string; file_url: string; description: string }>
): Promise<ProjectDocument> {
  return (await client.patch(`/projects/${projectId}/documents/${docId}`, body)).data;
}

// ---- releases ----
export async function fetchReleases(projectId: number): Promise<Release[]> {
  return (await client.get(`/projects/${projectId}/releases`)).data;
}

export async function createRelease(
  projectId: number,
  body: { version: string; title: string; release_date: string; content?: string }
): Promise<Release> {
  return (await client.post(`/projects/${projectId}/releases`, body)).data;
}

// ---- costs ----
export async function fetchCosts(projectId: number): Promise<ProjectCost[]> {
  return (await client.get(`/projects/${projectId}/costs`)).data;
}

export async function fetchCostSummary(projectId: number): Promise<CostSummary> {
  return (await client.get(`/projects/${projectId}/costs/summary`)).data;
}

export async function createCost(
  projectId: number,
  body: { cost_date: string; category: CostCategory; item: string; amount: string; note?: string }
): Promise<ProjectCost> {
  return (await client.post(`/projects/${projectId}/costs`, body)).data;
}

// ---- report ----
export async function fetchProjectReport(projectId: number): Promise<ProjectReport> {
  return (await client.get(`/projects/${projectId}/report`)).data;
}

// ---- change logs ----
export async function fetchChangeLogs(
  entityType: string,
  entityId: number
): Promise<Page<ChangeLog>> {
  return (
    await client.get("/change-logs", {
      params: { entity_type: entityType, entity_id: entityId },
    })
  ).data;
}
