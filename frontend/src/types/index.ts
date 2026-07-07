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
