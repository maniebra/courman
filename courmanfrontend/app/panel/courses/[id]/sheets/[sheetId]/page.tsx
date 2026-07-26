"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import { GradingSheet } from "@/components/grading-sheet";
import { Button } from "@/components/ui/button";

type Brief = { id: number };
type CourseDetail = {
  id: number;
  code: string;
  name: string;
  professors: Brief[];
  head_tas: Brief[];
};

export default function SheetPage() {
  const { id, sheetId } = useParams<{ id: string; sheetId: string }>();
  const router = useRouter();
  const { t } = useI18n();
  const { user } = useSession();
  const [course, setCourse] = useState<CourseDetail | null>(null);

  useEffect(() => {
    api
      .get<CourseDetail>(`/courses/${id}`)
      .then((res) => setCourse(res.data))
      .catch(() => setCourse(null));
  }, [id]);

  const canManage =
    course !== null &&
    [...course.professors, ...course.head_tas].some((m) => m.id === user.id);

  return (
    <>
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          render={<Link href={`/panel/courses/${id}`} />}
        >
          <ArrowLeft className="rtl:rotate-180" />
        </Button>
        {course && (
          <p className="text-sm text-muted-foreground">
            {course.code} · {course.name}
          </p>
        )}
      </div>

      {course && (
        <GradingSheet
          sheetId={Number(sheetId)}
          canManage={canManage}
          onDeleted={() => router.replace(`/panel/courses/${id}`)}
        />
      )}
      {!course && (
        <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
      )}
    </>
  );
}
