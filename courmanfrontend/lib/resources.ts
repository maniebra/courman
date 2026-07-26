import {
  BookOpen,
  KeyRound,
  Shield,
  Users,
  type LucideIcon,
} from "lucide-react";

import type { User } from "@/lib/api";
import type { Key } from "@/lib/i18n";

export type Field = {
  name: string;
  labelKey: Key;
  type?: "text" | "email" | "password" | "textarea" | "checkbox";
  required?: boolean;
};

export type Column = {
  labelKey: Key;
  render: (row: Row, t: (key: Key) => string) => string;
  /** render as badges instead of a comma-joined string */
  chips?: (row: Row) => string[];
  /** render as a status dot */
  bool?: (row: Row) => boolean;
};

/** Many-to-many edited through `POST/DELETE {basePath}/{id}/{path}/{targetId}`. */
export type Link = {
  labelKey: Key;
  path: string;
  /** resource key whose rows are the available options */
  options: string;
  /** field on the row holding the currently linked objects */
  field: string;
};

export type Row = Record<string, unknown> & { id: number };

export type Resource = {
  key: string;
  labelKey: Key;
  /** singular, for "New course" / "Delete this course?" */
  singularKey: Key;
  icon: LucideIcon;
  basePath: string;
  columns: Column[];
  createFields: Field[];
  updateFields: Field[];
  link?: Link;
  /** rows link to a dedicated page when set */
  detailPath?: (id: number) => string;
  /** mirrors what the API actually enforces, so we never show a dead end */
  visible: (user: User) => boolean;
  canWrite: (user: User) => boolean;
};

const isStaff = (user: User) => user.is_staff;

const list = (v: unknown, key = "name") =>
  Array.isArray(v) ? v.map((o) => String(o[key])) : [];

const names = (v: unknown, key = "name") =>
  Array.isArray(v) ? v.map((o) => String(o[key])).join(", ") || "—" : "—";

export const resources: Resource[] = [
  {
    key: "users",
    labelKey: "res.users",
    singularKey: "res.user",
    icon: Users,
    basePath: "/iam/users",
    visible: isStaff,
    canWrite: isStaff,
    columns: [
      { labelKey: "field.username", render: (r) => String(r.username) },
      {
        labelKey: "field.name",
        render: (r) => `${r.first_name} ${r.last_name}`.trim() || "—",
      },
      { labelKey: "field.email", render: (r) => String(r.email || "—") },
      { labelKey: "field.roles", render: (r) => names(r.roles) },
      {
        labelKey: "field.active",
        render: (r, t) => t(r.is_active ? "common.yes" : "common.no"),
      },
    ],
    createFields: [
      { name: "username", labelKey: "field.username", required: true },
      {
        name: "password",
        labelKey: "field.password",
        type: "password",
        required: true,
      },
      { name: "email", labelKey: "field.email", type: "email" },
      { name: "first_name", labelKey: "field.firstName" },
      { name: "last_name", labelKey: "field.lastName" },
    ],
    updateFields: [
      { name: "email", labelKey: "field.email", type: "email" },
      { name: "first_name", labelKey: "field.firstName" },
      { name: "last_name", labelKey: "field.lastName" },
      { name: "is_active", labelKey: "field.active", type: "checkbox" },
    ],
    link: {
      labelKey: "field.roles",
      path: "roles",
      options: "roles",
      field: "roles",
    },
  },
  {
    key: "roles",
    labelKey: "res.roles",
    singularKey: "res.role",
    icon: Shield,
    basePath: "/iam/roles",
    visible: isStaff,
    canWrite: isStaff,
    columns: [
      { labelKey: "field.name", render: (r) => String(r.name) },
      {
        labelKey: "field.actions",
        render: (r) => names(r.actions),
        chips: (r) => list(r.actions),
      },
    ],
    createFields: [{ name: "name", labelKey: "field.name", required: true }],
    updateFields: [{ name: "name", labelKey: "field.name", required: true }],
    link: {
      labelKey: "field.actions",
      path: "actions",
      options: "actions",
      field: "actions",
    },
  },
  {
    key: "actions",
    labelKey: "res.actions",
    singularKey: "res.action",
    icon: KeyRound,
    basePath: "/iam/actions",
    visible: isStaff,
    canWrite: isStaff,
    columns: [{ labelKey: "field.name", render: (r) => String(r.name) }],
    createFields: [{ name: "name", labelKey: "field.name", required: true }],
    updateFields: [{ name: "name", labelKey: "field.name", required: true }],
  },
  {
    key: "courses",
    labelKey: "res.courses",
    singularKey: "res.course",
    icon: BookOpen,
    basePath: "/courses",
    visible: () => true,
    canWrite: isStaff,
    columns: [
      { labelKey: "field.code", render: (r) => String(r.code) },
      { labelKey: "field.name", render: (r) => String(r.name) },
      { labelKey: "field.semester", render: (r) => String(r.semester || "—") },
      {
        labelKey: "field.description",
        render: (r) => String(r.description || "—"),
      },
      {
        labelKey: "field.staff",
        render: (r) => names(r.professors, "username"),
      },
    ],
    createFields: [
      { name: "code", labelKey: "field.code", required: true },
      { name: "name", labelKey: "field.name", required: true },
      { name: "semester", labelKey: "field.semester" },
      { name: "description", labelKey: "field.description", type: "textarea" },
    ],
    updateFields: [
      { name: "code", labelKey: "field.code", required: true },
      { name: "name", labelKey: "field.name", required: true },
      { name: "semester", labelKey: "field.semester" },
      { name: "description", labelKey: "field.description", type: "textarea" },
    ],
    detailPath: (id) => `/panel/courses/${id}`,
  },
];

export const getResource = (key: string) =>
  resources.find((r) => r.key === key);
