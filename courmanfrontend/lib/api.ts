import axios, { isAxiosError } from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "/api",
  withCredentials: true,
  xsrfCookieName: "csrftoken",
  xsrfHeaderName: "X-CSRFToken",
});

/** All list endpoints are ninja-paginated: `{ items, count }`. */
export async function listAll<T>(path: string, limit = 100) {
  const res = await api.get<{ items: T[]; count: number }>(path + "/", {
    params: { limit },
  });
  return res.data;
}

export function errorMessage(err: unknown, fallback = "Something went wrong") {
  if (isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return fallback;
}

export type Role = {
  id: number;
  name: string;
};

export type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  is_staff: boolean;
  is_superuser: boolean;
  roles: Role[];
  /** every action the user holds, flattened from their roles by the API */
  actions: string[];
};

/** Action names, mirroring iam/actions.py. */
export const ACTIONS = {
  usersView: "users.view",
  usersManage: "users.manage",
  rolesView: "roles.view",
  rolesManage: "roles.manage",
  coursesView: "courses.view",
  coursesManage: "courses.manage",
  courseStaffManage: "courses.staff.manage",
  studentsManage: "students.manage",
} as const;

export type Course = {
  id: number;
  code: string;
  name: string;
  description: string;
};
