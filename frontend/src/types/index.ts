export type Role = "admin" | "manager" | "member";

export type ProjectStatus =
  | "PLANNED"
  | "IN_PROGRESS"
  | "ON_HOLD"
  | "COMPLETED"
  | "CANCELED";

export type ProjectType = "HW" | "SW" | "HYBRID";

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface User {
  id: number;
  email: string;
  name: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}

export interface Contact {
  id: number;
  name: string;
  position: string | null;
  phone: string | null;
  email: string | null;
  is_active: boolean;
}

export interface Customer {
  id: number;
  name: string;
  business_no: string | null;
  address: string | null;
  note: string | null;
  is_active: boolean;
  created_at: string;
}

export interface CustomerDetail extends Customer {
  contacts: Contact[];
}

export interface Member {
  id: number;
  user_id: number;
  role: string | null;
  user_name: string;
}

export interface Contract {
  id: number;
  contract_no: string;
  amount: string | null;
  signed_date: string | null;
  start_date: string | null;
  end_date: string | null;
  status: "ACTIVE" | "CLOSED" | "CANCELED";
  note: string | null;
}

export interface Project {
  id: number;
  code: string;
  name: string;
  customer_id: number;
  customer_name: string;
  project_type: ProjectType;
  status: ProjectStatus;
  manager_id: number;
  manager_name: string;
  start_date: string | null;
  end_date: string | null;
  created_at: string;
}

export interface ProjectDetail extends Project {
  description: string | null;
  members: Member[];
  contracts: Contract[];
}

export type WbsStatus = "TODO" | "IN_PROGRESS" | "DONE";

export interface WbsItem {
  id: number;
  parent_id: number | null;
  name: string;
  assignee_id: number | null;
  assignee_name: string | null;
  start_date: string | null;
  end_date: string | null;
  progress: number;
  status: WbsStatus;
  sort_order: number;
  depth: number;
  is_delayed: boolean;
}

export interface Milestone {
  id: number;
  name: string;
  due_date: string;
  status: "PENDING" | "ACHIEVED";
  achieved_date: string | null;
  note: string | null;
  is_delayed: boolean;
}

export interface ScheduleSummary {
  progress: number;
  wbs_total: number;
  wbs_delayed: number;
  milestone_total: number;
  milestone_delayed: number;
}

export type BoardStatus = "DESIGN" | "PROTOTYPE" | "PRODUCTION" | "OBSOLETE";

export interface HwBoard {
  id: number;
  name: string;
  revision: string;
  status: BoardStatus;
  description: string | null;
}

export interface BomItem {
  id: number;
  part_name: string;
  part_number: string | null;
  manufacturer: string | null;
  quantity: number;
  reference: string | null;
  note: string | null;
}

export interface Fabrication {
  id: number;
  fab_date: string;
  quantity: number;
  vendor: string | null;
  result: "OK" | "NG" | "PARTIAL";
  note: string | null;
}

export interface HwBoardDetail extends HwBoard {
  bom_items: BomItem[];
  fabrications: Fabrication[];
}

export type ModuleType = "FIRMWARE" | "APP" | "SERVER" | "LIBRARY";
export type VersionStatus = "DEVELOP" | "RELEASED" | "DEPRECATED";

export interface SwModule {
  id: number;
  name: string;
  module_type: ModuleType;
  repo_url: string | null;
  description: string | null;
}

export interface SwVersion {
  id: number;
  version: string;
  status: VersionStatus;
  released_date: string | null;
  note: string | null;
}

export interface SwModuleDetail extends SwModule {
  versions: SwVersion[];
}

export interface SwBuild {
  id: number;
  build_no: string;
  commit_hash: string | null;
  built_at: string;
  result: "SUCCESS" | "FAIL";
  note: string | null;
}

export interface SwDeployment {
  id: number;
  environment: "DEV" | "STAGE" | "PROD" | "FIELD";
  deployed_at: string;
  note: string | null;
}

export interface SwVersionDetail extends SwVersion {
  builds: SwBuild[];
  deployments: SwDeployment[];
}

export type TestType = "UNIT" | "INTEGRATION" | "FIELD";
export type TestResult = "PASS" | "FAIL" | "BLOCKED";

export interface TestRun {
  id: number;
  run_date: string;
  result: TestResult;
  tester_id: number;
  tester_name: string;
  note: string | null;
}

export interface TestCase {
  id: number;
  test_type: TestType;
  name: string;
  description: string | null;
  expected_result: string | null;
  last_result: TestResult | null;
}

export interface TestCaseDetail extends TestCase {
  runs: TestRun[];
}

export type IssueType = "BUG" | "IMPROVEMENT" | "CUSTOMER_REQUEST" | "FAILURE";
export type IssueSeverity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type IssueStatus = "OPEN" | "IN_PROGRESS" | "RESOLVED" | "CLOSED";

export interface Issue {
  id: number;
  issue_type: IssueType;
  title: string;
  severity: IssueSeverity;
  status: IssueStatus;
  reporter_id: number;
  reporter_name: string;
  assignee_id: number | null;
  assignee_name: string | null;
  resolved_date: string | null;
  created_at: string;
}

export interface IssueDetail extends Issue {
  description: string | null;
  cause_analysis: string | null;
  resolution: string | null;
}

export type DocType =
  | "REQUIREMENTS"
  | "DESIGN"
  | "INTERFACE"
  | "TEST_PLAN"
  | "VERIFICATION"
  | "RELEASE_NOTE"
  | "OTHER";

export interface ProjectDocument {
  id: number;
  doc_type: DocType;
  title: string;
  version: string;
  file_url: string | null;
  description: string | null;
  author_id: number;
  author_name: string;
  updated_at: string;
}

export interface ChangeLog {
  id: number;
  entity_type: string;
  entity_id: number;
  action: string;
  changed_by: number;
  changed_by_name: string;
  changed_at: string;
  before_data: Record<string, unknown> | null;
  after_data: Record<string, unknown> | null;
}
