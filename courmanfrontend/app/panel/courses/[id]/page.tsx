"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, FileSpreadsheet, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { ACTIONS, api, errorMessage, type User } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useI18n, type Key } from "@/lib/i18n";
import { useSession } from "@/lib/session";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Card,
  CardAction,
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

type Student = { id: number; student_id: string; name: string };
/** One numbered team of a type ("Project 1"); a student joins one group per type. */
type Group = { id: number; number: number; members: Student[] };
type GroupType = {
  id: number;
  title: string;
  description: string;
  min_members: number;
  max_members: number;
  groups: Group[];
};
type Brief = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};
type CourseDetail = {
  id: number;
  code: string;
  name: string;
  semester: string;
  description: string;
  professors: Brief[];
  head_tas: Brief[];
  tas: Brief[];
  students: Student[];
};
type Component = {
  id: number;
  name: string;
  weight: string;
  sheet_id: number | null;
};
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
  const { user, can } = useSession();
  const [course, setCourse] = useState<CourseDetail | null>(null);
  const [users, setUsers] = useState<Brief[]>([]);
  const [types, setTypes] = useState<GroupType[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Roster and groups move together: assigning a student changes both.
  const load = useCallback(async () => {
    try {
      const [courseRes, typesRes] = await Promise.all([
        api.get<CourseDetail>(`/courses/${id}`),
        api.get<GroupType[]>(`/courses/${id}/group-types`),
      ]);
      setCourse(courseRes.data);
      setTypes(typesRes.data);
    } catch (err) {
      setError(errorMessage(err, t("course.notFound")));
    }
  }, [id, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
    api
      .get<Brief[]>("/iam/users/lookup", { params: { limit: 50 } })
      .then((res) => setUsers(res.data))
      .catch(() => setUsers([]));
  }, [load]);

  // Staff edits the roster; grading is limited to this course's professors and
  // head TAs — superusers included, which is what the API enforces.
  const canManageGrading =
    course !== null &&
    [...course.professors, ...course.head_tas].some((m) => m.id === user.id);
  const canEditStaff = can(ACTIONS.courseStaffManage);
  // Enrolment is run by whoever runs the course, staff included.
  const canEditStudents = can(ACTIONS.studentsManage) && (canManageGrading || can(ACTIONS.coursesManage));
  if (error) return <p className="text-sm text-destructive">{error}</p>;
  if (!course)
    return (
      <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
    );

  return (
    <>
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          render={<Link href="/panel/courses" />}
        >
          <ArrowLeft className="rtl:rotate-180" />
        </Button>
        <div>
          <h1 className="flex items-center gap-2 text-xl font-semibold">
            {course.code}{" "}
            <span className="text-muted-foreground">· {course.name}</span>
            {course.semester && (
              <Badge variant="secondary">{course.semester}</Badge>
            )}
          </h1>
          {course.description && (
            <p className="text-sm text-muted-foreground">
              {course.description}
            </p>
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
            editable={canEditStaff}
            onChanged={load}
          />
        ))}
      </div>

      <Students
        courseId={course.id}
        students={course.students}
        types={types}
        editable={canEditStudents}
        onChanged={load}
      />

      <Groups
        courseId={course.id}
        types={types}
        students={course.students}
        editable={canEditStudents}
        onChanged={load}
      />

      <Grading
        courseId={course.id}
        graders={users}
        editable={canManageGrading}
      />
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
  editable,
  onChanged,
}: {
  courseId: number;
  path: string;
  label: string;
  members: Brief[];
  users: Brief[];
  editable: boolean;
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
        <CardDescription>
          {t("course.assigned", { count: members.length })}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-1">
          {members.length === 0 && (
            <span className="text-sm text-muted-foreground">
              {t("common.none")}
            </span>
          )}
          {members.map((m) => (
            <Badge key={m.id} variant="secondary" className="gap-1">
              {m.username}
              {editable && (
                <button
                  type="button"
                  aria-label={`Remove ${m.username}`}
                  onClick={() => mutate("delete", m.id)}
                >
                  <Trash2 className="size-3" />
                </button>
              )}
            </Badge>
          ))}
        </div>
        {editable && (
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
        )}
      </CardContent>
    </Card>
  );
}

function Students({
  courseId,
  students,
  types,
  editable,
  onChanged,
}: {
  courseId: number;
  students: Student[];
  types: GroupType[];
  editable: boolean;
  onChanged: () => void;
}) {
  const { t } = useI18n();
  const [studentId, setStudentId] = useState("");
  const [name, setName] = useState("");

  async function add(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post(`/courses/${courseId}/students`, {
        student_id: studentId,
        name,
      });
      setStudentId("");
      setName("");
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("course.addStudentError")));
    }
  }

  async function remove(student: Student) {
    if (!confirm(t("common.deleteConfirm", { item: student.student_id })))
      return;
    try {
      await api.delete(`/courses/${courseId}/students/${student.id}`);
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("course.removeStudentError")));
    }
  }

  const groupOf = (type: GroupType, student: Student) =>
    type.groups.find((g) => g.members.some((m) => m.id === student.id)) ?? null;

  const [assigning, setAssigning] = useState<Student | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("course.students")}</CardTitle>
        <CardDescription>
          {t("course.assigned", { count: students.length })}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("course.studentId")}</TableHead>
              <TableHead>{t("field.name")}</TableHead>
              {types.length > 0 && <TableHead>{t("group.title")}</TableHead>}
              <TableHead className="w-0" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {students.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>{t("common.nothingHere")}</TableCell>
              </TableRow>
            )}
            {students.map((student) => (
              <TableRow key={student.id}>
                <TableCell className="font-medium tabular-nums">
                  <bdi>{student.student_id}</bdi>
                </TableCell>
                <TableCell>{student.name || "—"}</TableCell>
                {types.length > 0 && (
                  <TableCell>
                    <div className="flex flex-wrap items-center gap-1">
                      {types.map((type) => {
                        const mine = groupOf(type, student);
                        return mine ? (
                          <Badge key={type.id} variant="secondary">
                            <bdi>
                              {type.title} {mine.number}
                            </bdi>
                          </Badge>
                        ) : null;
                      })}
                      {types.every((type) => !groupOf(type, student)) && (
                        <span className="text-sm text-muted-foreground">
                          {t("group.noGroup")}
                        </span>
                      )}
                      {editable && (
                        <Button
                          variant="ghost"
                          size="icon"
                          title={t("group.manage")}
                          onClick={() => setAssigning(student)}
                        >
                          <Pencil />
                        </Button>
                      )}
                    </div>
                  </TableCell>
                )}
                <TableCell>
                  {editable && (
                    <Button
                      variant="ghost"
                      size="icon"
                      title={t("common.delete")}
                      onClick={() => remove(student)}
                    >
                      <Trash2 />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {editable && (
          <form className="flex gap-2" onSubmit={add}>
            <Input
              className="w-40"
              placeholder={t("course.studentId")}
              value={studentId}
              onChange={(e) => setStudentId(e.target.value)}
              required
            />
            <Input
              placeholder={t("course.studentName")}
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
            <Button type="submit">
              <Plus /> {t("common.add")}
            </Button>
          </form>
        )}
      </CardContent>

      {assigning && (
        <StudentGroupsDialog
          courseId={courseId}
          student={assigning}
          types={types}
          onClose={() => setAssigning(null)}
          onChanged={onChanged}
        />
      )}
    </Card>
  );
}

/** Every type in one place, so ten of them cost a dialog instead of ten columns. */
function StudentGroupsDialog({
  courseId,
  student,
  types,
  onClose,
  onChanged,
}: {
  courseId: number;
  student: Student;
  types: GroupType[];
  onClose: () => void;
  onChanged: () => void;
}) {
  const { t } = useI18n();

  /** One control per type does join, move and leave: joining leaves the sibling. */
  async function assign(from: Group | null, to: number | null) {
    try {
      if (to === null)
        await api.delete(
          `/courses/${courseId}/groups/${from!.id}/members/${student.id}`,
        );
      else
        await api.post(
          `/courses/${courseId}/groups/${to}/members/${student.id}`,
        );
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("group.error")));
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            <bdi>{student.name || student.student_id}</bdi>
          </DialogTitle>
        </DialogHeader>
        <div className="flex flex-col gap-3">
          {types.map((type) => {
            const mine =
              type.groups.find((g) =>
                g.members.some((m) => m.id === student.id),
              ) ?? null;
            return (
              <div key={type.id} className="flex items-center justify-between gap-4">
                <Label htmlFor={`type-${type.id}`}>{type.title}</Label>
                {type.groups.length === 0 ? (
                  <span className="text-sm text-muted-foreground">
                    {t("group.noGroupsYet")}
                  </span>
                ) : (
                  <select
                    id={`type-${type.id}`}
                    className="h-9 w-48 rounded-md border bg-transparent px-2 text-sm"
                    value={mine?.id ?? ""}
                    onChange={(e) =>
                      assign(mine, e.target.value ? Number(e.target.value) : null)
                    }
                  >
                    <option value="">{t("group.noGroup")}</option>
                    {type.groups.map((g) => (
                      <option
                        key={g.id}
                        value={g.id}
                        // a full group stays selectable if it is already theirs
                        disabled={
                          g.id !== mine?.id &&
                          g.members.length >= type.max_members
                        }
                      >
                        {type.title} {g.number} ({g.members.length}/
                        {type.max_members})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            );
          })}
        </div>
        <DialogFooter>
          <Button type="button" onClick={onClose}>
            {t("common.done")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function Groups({
  courseId,
  types,
  students,
  editable,
  onChanged,
}: {
  courseId: number;
  types: GroupType[];
  students: Student[];
  editable: boolean;
  onChanged: () => void;
}) {
  const { t } = useI18n();
  const [editing, setEditing] = useState<GroupType | "new" | null>(null);

  async function call(fn: () => Promise<unknown>) {
    try {
      await fn();
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("group.error")));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("group.title")}</CardTitle>
        <CardDescription>{t("group.hint")}</CardDescription>
        {editable && (
          <CardAction>
            <Button size="sm" onClick={() => setEditing("new")}>
              <Plus /> {t("group.newType")}
            </Button>
          </CardAction>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {types.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {t("common.nothingHere")}
          </p>
        )}
        {types.map((type) => {
          const grouped = new Set(
            type.groups.flatMap((g) => g.members.map((m) => m.id)),
          );
          const ungrouped = students.filter((s) => !grouped.has(s.id)).length;
          return (
            <div key={type.id} className="flex flex-col gap-3 rounded-md border p-3">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <p className="font-medium">{type.title}</p>
                  <p className="text-sm text-muted-foreground">
                    {t("group.limits", {
                      min: type.min_members,
                      max: type.max_members,
                    })}
                    {ungrouped > 0 &&
                      ` · ${t("group.ungroupedCount", { count: ungrouped })}`}
                  </p>
                  {type.description && (
                    <p className="text-sm text-muted-foreground">
                      {type.description}
                    </p>
                  )}
                </div>
                {editable && (
                  <div className="flex items-center gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        call(() =>
                          api.post(
                            `/courses/${courseId}/group-types/${type.id}/groups`,
                          ),
                        )
                      }
                    >
                      <Plus /> {t("group.addGroup")}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title={t("common.edit")}
                      onClick={() => setEditing(type)}
                    >
                      <Pencil />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      title={t("common.delete")}
                      onClick={() => {
                        if (
                          !confirm(
                            t("common.deleteConfirm", { item: type.title }),
                          )
                        )
                          return;
                        call(() =>
                          api.delete(
                            `/courses/${courseId}/group-types/${type.id}`,
                          ),
                        );
                      }}
                    >
                      <Trash2 />
                    </Button>
                  </div>
                )}
              </div>

              {type.groups.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t("group.noGroupsYet")}
                </p>
              ) : (
                <div className="grid gap-2 lg:grid-cols-2">
                  {type.groups.map((group) => (
                    <div
                      key={group.id}
                      className="flex items-start gap-2 rounded-md bg-muted/40 p-2"
                    >
                      <span className="font-medium tabular-nums">
                        <bdi>
                          {type.title} {group.number}
                        </bdi>
                      </span>
                      <div className="flex flex-1 flex-wrap gap-1">
                        {group.members.length === 0 && (
                          <span className="text-sm text-muted-foreground">
                            {t("common.none")}
                          </span>
                        )}
                        {group.members.map((m) => (
                          <Badge key={m.id} variant="secondary">
                            <bdi>{m.name || m.student_id}</bdi>
                          </Badge>
                        ))}
                        {group.members.length < type.min_members && (
                          <Badge variant="outline">
                            {t("group.belowMin", { min: type.min_members })}
                          </Badge>
                        )}
                      </div>
                      {editable && (
                        <Button
                          variant="ghost"
                          size="icon"
                          title={t("common.delete")}
                          onClick={() => {
                            if (
                              !confirm(
                                t("common.deleteConfirm", {
                                  item: `${type.title} ${group.number}`,
                                }),
                              )
                            )
                              return;
                            call(() =>
                              api.delete(
                                `/courses/${courseId}/groups/${group.id}`,
                              ),
                            );
                          }}
                        >
                          <Trash2 />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </CardContent>

      {editing && (
        <GroupTypeDialog
          courseId={courseId}
          type={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            onChanged();
          }}
        />
      )}
    </Card>
  );
}

function GroupTypeDialog({
  courseId,
  type,
  onClose,
  onSaved,
}: {
  courseId: number;
  type: GroupType | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const [title, setTitle] = useState(type?.title ?? "");
  const [description, setDescription] = useState(type?.description ?? "");
  const [min, setMin] = useState(String(type?.min_members ?? 1));
  const [max, setMax] = useState(String(type?.max_members ?? 3));
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const body = {
      title,
      description,
      min_members: Number(min),
      max_members: Number(max),
    };
    setSaving(true);
    try {
      if (type)
        await api.patch(`/courses/${courseId}/group-types/${type.id}`, body);
      else await api.post(`/courses/${courseId}/group-types`, body);
      onSaved();
    } catch (err) {
      toast.error(errorMessage(err, t("group.error")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {t(type ? "common.editTitle" : "common.newTitle", {
              item: t("group.item"),
            })}
          </DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={submit}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="group-title">{t("group.name")}</Label>
            <Input
              id="group-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-2">
            <Label htmlFor="group-description">{t("field.description")}</Label>
            <Textarea
              id="group-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div className="flex gap-4">
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="group-min">{t("group.min")}</Label>
              <Input
                id="group-min"
                type="number"
                min={1}
                value={min}
                onChange={(e) => setMin(e.target.value)}
              />
            </div>
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="group-max">{t("group.max")}</Label>
              <Input
                id="group-max"
                type="number"
                min={Number(min) || 1}
                value={max}
                onChange={(e) => setMax(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? t("common.saving") : t("common.save")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function Grading({
  courseId,
  graders,
  editable,
}: {
  courseId: number;
  graders: (Brief | User)[];
  editable: boolean;
}) {
  const { t } = useI18n();
  const [components, setComponents] = useState<Component[] | null>(null);
  const [name, setName] = useState("");
  const [weight, setWeight] = useState("");
  const [open, setOpen] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Component[]>(
        `/grading/courses/${courseId}/components`,
      );
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

  const total = (components ?? []).reduce(
    (sum, c) => sum + Number(c.weight),
    0,
  );

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
              <TableHead>{t("sheet.title")}</TableHead>
              <TableHead className="w-0" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {components === null && (
              <TableRow>
                <TableCell colSpan={4}>{t("common.loading")}</TableCell>
              </TableRow>
            )}
            {components?.length === 0 && (
              <TableRow>
                <TableCell colSpan={4}>{t("grading.noComponents")}</TableCell>
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
                    <Tasks
                      componentId={c.id}
                      graders={graders}
                      editable={editable}
                    />
                  )}
                </TableCell>
                <TableCell>
                  {/* keep "12.50%" from being reordered in RTL */}
                  <bdi>{c.weight}%</bdi>
                </TableCell>
                <TableCell>
                  <SheetLink
                    component={c}
                    courseId={courseId}
                    editable={editable}
                  />
                </TableCell>
                <TableCell>
                  {editable && (
                    <Button
                      variant="ghost"
                      size="icon"
                      title={t("common.delete")}
                      onClick={() => remove(c.id)}
                    >
                      <Trash2 />
                    </Button>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>

        {editable && (
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
        )}
      </CardContent>
    </Card>
  );
}

function SheetLink({
  component,
  courseId,
  editable,
}: {
  component: Component;
  courseId: number;
  editable: boolean;
}) {
  const { t } = useI18n();
  const router = useRouter();
  const [creating, setCreating] = useState(false);

  const href = `/panel/courses/${courseId}/sheets/${component.sheet_id}`;
  if (component.sheet_id) {
    return (
      <Button variant="outline" size="sm" render={<Link href={href} />}>
        <FileSpreadsheet /> {t("sheet.open")}
      </Button>
    );
  }
  if (!editable) {
    return (
      <span className="text-sm text-muted-foreground">{t("sheet.none")}</span>
    );
  }

  async function create() {
    setCreating(true);
    try {
      const res = await api.post<{ id: number }>(
        `/grading/components/${component.id}/sheet`,
        { title: component.name },
      );
      router.push(`/panel/courses/${courseId}/sheets/${res.data.id}`);
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.createError")));
      setCreating(false);
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={create} disabled={creating}>
      <Plus /> {t("sheet.create")}
    </Button>
  );
}

function Tasks({
  componentId,
  graders,
  editable,
}: {
  componentId: number;
  graders: (Brief | User)[];
  editable: boolean;
}) {
  const { t } = useI18n();
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [picked, setPicked] = useState("");

  const load = useCallback(async () => {
    try {
      const res = await api.get<Task[]>(
        `/grading/components/${componentId}/tasks`,
      );
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
      <p className="text-xs font-medium text-muted-foreground">
        {t("grading.graders")}
      </p>
      {tasks === null && (
        <span className="text-sm text-muted-foreground">
          {t("common.loading")}
        </span>
      )}
      {tasks?.length === 0 && (
        <span className="text-sm text-muted-foreground">
          {t("common.none")}
        </span>
      )}
      <div className="flex flex-wrap gap-1">
        {tasks?.map((t) => (
          <Badge key={t.id} variant="secondary" className="gap-1">
            {t.assigned_to.username}
            {editable && (
              <button
                type="button"
                aria-label={`Remove ${t.assigned_to.username}`}
                onClick={() => remove(t.id)}
              >
                <Trash2 className="size-3" />
              </button>
            )}
          </Badge>
        ))}
      </div>
      {editable && (
        <form className="flex gap-2" onSubmit={assign}>
          <select
            aria-label={t("grading.assignPlaceholder")}
            className="h-8 rounded-md border bg-transparent px-2 text-sm"
            value={picked}
            onChange={(e) => setPicked(e.target.value)}
          >
            <option value="">{t("grading.assignPlaceholder")}</option>
            {graders.map((u) => (
              <option key={u.id} value={u.id}>
                {label(u)}
              </option>
            ))}
          </select>
          <Button type="submit" size="sm" disabled={!picked}>
            {t("grading.assign")}
          </Button>
        </form>
      )}
    </div>
  );
}
