"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CalendarClock, FileSpreadsheet, GraduationCap } from "lucide-react";

import { api } from "@/lib/api";
import { useI18n, type Key } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type Slot = {
  id: number;
  course_id: number;
  course: string;
  item: string;
  start: string;
  end: string;
  /** empty while nobody has booked the slot */
  group: string;
  members: string[];
};
type Grading = {
  component_id: number;
  course_id: number;
  course: string;
  component: string;
  sheet_id: number | null;
};
type CourseRow = {
  id: number;
  code: string;
  name: string;
  role: "professor" | "head_ta" | "ta";
  students: number;
  open_forms: number;
};
type Todo = { handoffs: Slot[]; grading: Grading[]; courses: CourseRow[] };

const ROLE: Record<CourseRow["role"], Key> = {
  professor: "course.professors",
  head_ta: "course.headTas",
  ta: "course.tas",
};

/** What the signed-in staff member owes: their sessions, their grading, their courses. */
export function Todo() {
  const { t, locale } = useI18n();
  const [todo, setTodo] = useState<Todo | null>(null);

  useEffect(() => {
    api
      .get<Todo>("/courses/me/todo")
      .then((res) => setTodo(res.data))
      .catch(() => setTodo({ handoffs: [], grading: [], courses: [] }));
  }, []);

  if (todo === null) return <Skeleton className="h-40 w-full" />;
  if (!todo.courses.length && !todo.grading.length && !todo.handoffs.length)
    return null;

  const when = (slot: Slot) =>
    `${new Date(slot.start).toLocaleString(locale, {
      weekday: "short",
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    })} – ${new Date(slot.end).toLocaleTimeString(locale, { timeStyle: "short" })}`;

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <CalendarClock className="size-4" /> {t("todo.schedule")}
          </CardTitle>
          <CardDescription>{t("todo.scheduleHint")}</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          {todo.handoffs.length === 0 && (
            <p className="text-sm text-muted-foreground">
              {t("todo.noSchedule")}
            </p>
          )}
          {todo.handoffs.map((slot) => (
            <Link
              key={slot.id}
              href={`/panel/courses/${slot.course_id}`}
              className="flex flex-wrap items-center gap-2 rounded-md border px-3 py-2 text-sm hover:border-primary/40"
            >
              <span className="tabular-nums">
                <bdi>{when(slot)}</bdi>
              </span>
              <Badge variant="secondary">{slot.course}</Badge>
              <span className="text-muted-foreground">{slot.item}</span>
              {slot.group ? (
                <span className="ms-auto flex items-center gap-2">
                  <span className="font-medium">{slot.group}</span>
                  <span className="text-xs text-muted-foreground">
                    <bdi>{slot.members.join(", ")}</bdi>
                  </span>
                </span>
              ) : (
                <span className="ms-auto text-xs text-muted-foreground">
                  {t("handoff.free")}
                </span>
              )}
            </Link>
          ))}
        </CardContent>
      </Card>

      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileSpreadsheet className="size-4" /> {t("todo.grading")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {todo.grading.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {t("todo.noGrading")}
              </p>
            )}
            {todo.grading.map((task) => (
              <Link
                key={task.component_id}
                href={
                  task.sheet_id
                    ? `/panel/courses/${task.course_id}/sheets/${task.sheet_id}`
                    : `/panel/courses/${task.course_id}`
                }
                className="flex items-center gap-2 rounded-md border px-3 py-2 text-sm hover:border-primary/40"
              >
                <Badge variant="secondary">{task.course}</Badge>
                <span className="flex-1">{task.component}</span>
                {!task.sheet_id && (
                  <span className="text-xs text-muted-foreground">
                    {t("sheet.none")}
                  </span>
                )}
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <GraduationCap className="size-4" /> {t("todo.courses")}
            </CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-2">
            {todo.courses.map((course) => (
              <Link
                key={course.id}
                href={`/panel/courses/${course.id}`}
                className="flex flex-wrap items-center gap-2 rounded-md border px-3 py-2 text-sm hover:border-primary/40"
              >
                <span className="font-medium">{course.code}</span>
                <Badge variant="outline">{t(ROLE[course.role])}</Badge>
                <span className="ms-auto text-xs text-muted-foreground">
                  {t("course.assigned", { count: course.students })}
                  {course.open_forms > 0 &&
                    ` · ${t("todo.openForms", { count: course.open_forms })}`}
                </span>
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
