import { BookOpen, KeyRound, Shield, Users, type LucideIcon } from "lucide-react";

export type Field = {
  name: string;
  label: string;
  type?: "text" | "email" | "password" | "textarea" | "checkbox";
  required?: boolean;
};

export type Column = {
  label: string;
  render: (row: Row) => string;
};

/** Many-to-many edited through `POST/DELETE {basePath}/{id}/{path}/{targetId}`. */
export type Link = {
  label: string;
  path: string;
  /** resource key whose rows are the available options */
  options: string;
  /** field on the row holding the currently linked objects */
  field: string;
};

export type Row = Record<string, unknown> & { id: number };

export type Resource = {
  key: string;
  label: string;
  icon: LucideIcon;
  basePath: string;
  columns: Column[];
  createFields: Field[];
  updateFields: Field[];
  link?: Link;
};

const names = (v: unknown, key = "name") =>
  Array.isArray(v) ? v.map((o) => String(o[key])).join(", ") || "—" : "—";

export const resources: Resource[] = [
  {
    key: "users",
    label: "Users",
    icon: Users,
    basePath: "/iam/users",
    columns: [
      { label: "Username", render: (r) => String(r.username) },
      { label: "Name", render: (r) => `${r.first_name} ${r.last_name}`.trim() || "—" },
      { label: "Email", render: (r) => String(r.email || "—") },
      { label: "Roles", render: (r) => names(r.roles) },
      { label: "Active", render: (r) => (r.is_active ? "yes" : "no") },
    ],
    createFields: [
      { name: "username", label: "Username", required: true },
      { name: "password", label: "Password", type: "password", required: true },
      { name: "email", label: "Email", type: "email" },
      { name: "first_name", label: "First name" },
      { name: "last_name", label: "Last name" },
    ],
    updateFields: [
      { name: "email", label: "Email", type: "email" },
      { name: "first_name", label: "First name" },
      { name: "last_name", label: "Last name" },
      { name: "is_active", label: "Active", type: "checkbox" },
    ],
    link: { label: "Roles", path: "roles", options: "roles", field: "roles" },
  },
  {
    key: "roles",
    label: "Roles",
    icon: Shield,
    basePath: "/iam/roles",
    columns: [
      { label: "Name", render: (r) => String(r.name) },
      { label: "Actions", render: (r) => names(r.actions) },
    ],
    createFields: [{ name: "name", label: "Name", required: true }],
    updateFields: [{ name: "name", label: "Name", required: true }],
    link: { label: "Actions", path: "actions", options: "actions", field: "actions" },
  },
  {
    key: "actions",
    label: "Actions",
    icon: KeyRound,
    basePath: "/iam/actions",
    columns: [{ label: "Name", render: (r) => String(r.name) }],
    createFields: [{ name: "name", label: "Name", required: true }],
    updateFields: [{ name: "name", label: "Name", required: true }],
  },
  {
    key: "courses",
    label: "Courses",
    icon: BookOpen,
    basePath: "/courses",
    columns: [
      { label: "Code", render: (r) => String(r.code) },
      { label: "Name", render: (r) => String(r.name) },
      { label: "Description", render: (r) => String(r.description || "—") },
      { label: "Staff", render: (r) => names(r.professors, "username") },
    ],
    createFields: [
      { name: "code", label: "Code", required: true },
      { name: "name", label: "Name", required: true },
      { name: "description", label: "Description", type: "textarea" },
    ],
    updateFields: [
      { name: "code", label: "Code", required: true },
      { name: "name", label: "Name", required: true },
      { name: "description", label: "Description", type: "textarea" },
    ],
  },
];

export const getResource = (key: string) => resources.find((r) => r.key === key);
