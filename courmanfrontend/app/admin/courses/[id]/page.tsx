"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage, listAll, type User } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useI18n, type Key } from "@/lib/i18n";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Brief = { id: number; username: string; first_name: string; last_name: string };
type CourseDetail = {
  id: number;
  code: string;
  name: string;
  description: string;
  professors: Brief[];
  head_tas: Brief[];
  tas: Brief[];
};
type Component = { id: number; name: string; weight: string };
type Task = { id: number; assigned_to: Brief; assigned_by: Brief };

/** Course staff m2m: `POST/DELETE /courses/{id}/{path}/{userId}`. */
const STAFF = [
  { field: "professors", path: "professors", labelKey: "course.professors" },
  { field: "head_tas", path: "head-tas", labelKey: "course.headTas" },
  { field: "tas", path: "tas", labelKey: "course.tas" },
] as const satisfies readonly { field: string; path: string; labelKey: Key }[];

export default function CoursePage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useI18n();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<CourseDetail>(`/courses/${id}`);
      setCourse(res.data);
    } catch (err) {
      setError(errorMessage(err, t("course.notFound")));
    }
  }, [id, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
    listAll<User>("/iam/users")
      .then((d) => setUsers(d.items))
      .catch(() => setUsers([]));
  }, [load]);

  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!course) return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;

  return (
    <>
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="icon" render={<Link href="/admin/courses" />}>
          <ArrowLeft className="rtl:rotate-180" />
        </Button>
        <div>
          <h1 className="text-xl font-semibold">
            {course.code} <span className="text-muted-foreground">· {course.name}</span>
          </h1>
          {course.description && (
            <p className="text-sm text-muted-foreground">{course.description}</p>
          )}
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {STAFF.map((s) => (
          <StaffCard
            key={s.field}
            courseId={course.id}
            path={s.path}
            label={t(s.labelKey)}
            members={course[s.field]}
            users={users}
            onChanged={load}
          />
        ))}
      </div>

      <Grading courseId={course.id} users={users} />
    </>
  );
}

function label(u: Brief | User) {
  const full = `${u.first_name} ${u.last_name}`.trim();
  return full ? `${u.username} (${full})` : u.username;
}

function StaffCard({
  courseId,
  path,
  label: title,
  members,
  users,
  onChanged,
}: {
  courseId: number;
  path: string;
  label: string;
  members: Brief[];
  users: User[];
  onChanged: () => void;
}) {
  const { t } = useI18n();
  const [picked, setPicked] = useState("");
  const available = users.filter((u) => !members.some((m) => m.id === u.id));

  async function mutate(method: "post" | "delete", userId: number) {
    try {
      await api[method](`/courses/${courseId}/${path}/${userId}`);
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("course.staffError")));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription>{t("course.assigned", { count: members.length })}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-1">
          {members.length === 0 && (
            <span className="text-sm text-muted-foreground">{t("common.none")}</span>
          )}
          {members.map((m) => (
            <Badge key={m.id} variant="secondary" className="gap-1">
              {m.username}
              <button
                type="button"
                aria-label={`Remove ${m.username}`}
                onClick={() => mutate("delete", m.id)}
              >
                <Trash2 className="size-3" />
              </button>
            </Badge>
          ))}
        </div>
        <form
          className="flex gap-2"
          onSubmit={(e) => {
            e.preventDefault();
            if (!picked) return;
            mutate("post", Number(picked));
            setPicked("");
          }}
        >
          <select
            aria-label={`Add to ${title}`}
            className="h-9 flex-1 rounded-md border bg-transparent px-2 text-sm"
            value={picked}
            onChange={(e) => setPicked(e.target.value)}
          >
            <option value="">{t("course.addUser")}</option>
            {available.map((u) => (
              <option key={u.id} value={u.id}>
                {label(u)}
              </option>
            ))}
          </select>
          <Button type="submit" size="icon" disabled={!picked}>
            <Plus />
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function Grading({ courseId, users }: { courseId: number; users: User[] }) {
  const { t } = useI18n();
  const [components, setComponents] = useState<Component[] | null>(null);
  const [name, setName] = useState("");
  const [weight, setWeight] = useState("");
  const [open, setOpen] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Component[]>(`/grading/courses/${courseId}/components`);
      setComponents(res.data);
    } catch (err) {
      toast.error(errorMessage(err, t("grading.loadError")));
      setComponents([]);
    }
  }, [courseId, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  async function add(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post(`/grading/courses/${courseId}/components`, {
        name,
        weight: Number(weight),
      });
      setName("");
      setWeight("");
      load();
    } catch (err) {
      toast.error(errorMessage(err, t("grading.addError")));
    }
  }

  async function remove(componentId: number) {
    if (!confirm(t("grading.deleteConfirm"))) return;
    try {
      await api.delete(`/grading/components/${componentId}`);
      load();
    } catch (err) {
      toast.error(errorMessage(err, t("grading.deleteError")));
    }
  }

  const total = (components ?? []).reduce((sum, c) => sum + Number(c.weight), 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("grading.title")}</CardTitle>
        <CardDescription>
          {t("grading.total", { total })}
          {total !== 100 && components?.length ? t("grading.notHundred") : ""}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("field.name")}</TableHead>
              <TableHead>{t("field.weight")}</TableHead>
              <TableHead className="w-0" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {components === null && (
              <TableRow>
                <TableCell colSpan={3}>{t("common.loading")}</TableCell>
              </TableRow>
            )}
            {components?.length === 0 && (
              <TableRow>
                <TableCell colSpan={3}>{t("grading.noComponents")}</TableCell>
              </TableRow>
            )}
            {components?.map((c) => (
              <TableRow key={c.id}>
                <TableCell>
                  <button
                    type="button"
                    className="font-medium underline-offset-4 hover:underline"
                    onClick={() => setOpen(open === c.id ? null : c.id)}
                  >
                    {c.name}
                  </button>
                  {open === c.id && (
                    <Tasks componentId={c.id} courseId={courseId} users={users} />
                  )}
                </TableCell>
                <TableCell>
                  {/* keep "12.50%" from being reordered in RTL */}
                  <bdi>{c.weight}%</bdi>
                </TableCell>
                <TableCell>
                  <Button
                    variant="ghost"
                    size="icon"
                    title={t("common.delete")}
                    onClick={() => remove(c.id)}
                  >
                    <Trash2 />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        <form className="flex gap-2" onSubmit={add}>
          <Input
            placeholder={t("grading.componentName")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            type="number"
            step="0.01"
            min="0"
            max="100"
            placeholder={t("grading.weight")}
            className="w-32"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            required
          />
          <Button type="submit">
            <Plus /> {t("common.add")}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function Tasks({
  componentId,
  users,
}: {
  componentId: number;
  courseId: number;
  users: User[];
}) {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [picked, setPicked] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await api.get<Task[]>(`/grading/components/${componentId}/tasks`);
      setTasks(res.data);
    } catch (err) {
      toast.error(errorMessage(err, t("grading.tasksError")));
      setTasks([]);
    }
  }, [componentId, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  async function assign(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post(`/grading/components/${componentId}/tasks`, {
        assigned_to_id: Number(picked),
      });
      setPicked("");
      load();
    } catch (err) {
      toast.error(errorMessage(err, t("grading.assignError")));
    }
  }

  async function remove(taskId: number) {
    try {
      await api.delete(`/grading/tasks/${taskId}`);
      load();
    } catch (err) {
      toast.error(errorMessage(err, t("grading.removeError")));
    }
  }

  return (
    <div className="mt-2 flex flex-col gap-2 border-s ps-3">
      <p className="text-xs font-medium text-muted-foreground">{t("grading.graders")}</p>
      {tasks === null && <span className="text-sm text-muted-foreground">{t("common.loading")}</span>}
      {tasks?.length === 0 && <span className="text-sm text-muted-foreground">{t("common.none")}</span>}
      <div className="flex flex-wrap gap-1">
        {tasks?.map((t) => (
          <Badge key={t.id} variant="secondary" className="gap-1">
            {t.assigned_to.username}
            <button
              type="button"
              aria-label={`Remove ${t.assigned_to.username}`}
              onClick={() => remove(t.id)}
            >
              <Trash2 className="size-3" />
            </button>
          </Badge>
        ))}
      </div>
      <form className="flex gap-2" onSubmit={assign}>
        <select
          aria-label={t("grading.assignPlaceholder")}
          className="h-8 rounded-md border bg-transparent px-2 text-sm"
          value={picked}
          onChange={(e) => setPicked(e.target.value)}
        >
          <option value="">{t("grading.assignPlaceholder")}</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {label(u)}
            </option>
          ))}
        </select>
        <Button type="submit" size="sm" disabled={!picked}>
          {t("grading.assign")}
        </Button>
      </form>
    </div>
  );
}
