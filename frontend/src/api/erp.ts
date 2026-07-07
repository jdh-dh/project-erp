import client, { setTokens } from "./client";
import type {
  ChangeLog,
  Contact,
  Contract,
  Customer,
  CustomerDetail,
  Page,
  Project,
  ProjectDetail,
  ProjectStatus,
  User,
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
