"use client";

import { useCallback, useEffect, useState } from "react";
import { Link2 } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type Component = {
  id: number;
  name: string;
  weight: number;
  max_score: number;
};
type Row = {
  student_id: string;
  name: string;
  totals: (number | null)[];
  grade: number | null;
};
export type Summary = {
  course: string;
  components: Component[];
  rows: Row[];
  summary_token: string | null;
};

/** Every component of the course side by side, plus the weighted grade. */
export function GradeSummary({
  courseId,
  canPublish,
}: {
  courseId: number;
  canPublish: boolean;
}) {
  const { t } = useI18n();
  const [summary, setSummary] = useState<Summary | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Summary>(`/grading/courses/${courseId}/summary`);
      setSummary(res.data);
    } catch (err) {
      toast.error(errorMessage(err, t("summary.loadError")));
    }
  }, [courseId, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  if (!summary || summary.components.length === 0) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("summary.title")}</CardTitle>
        <CardDescription>{t("summary.hint")}</CardDescription>
        {canPublish && (
          <CardAction className="flex items-center gap-2">
            {summary.summary_token && (
              <button
                type="button"
                className="flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline"
                onClick={() => {
                  navigator.clipboard.writeText(
                    `${location.origin}/grades/${summary.summary_token}`,
                  );
                  toast.success(t("signup.copied"));
                }}
              >
                <Link2 className="size-4" /> {t("signup.copyLink")}
              </button>
            )}
            <Button
              size="sm"
              variant={summary.summary_token ? "secondary" : "outline"}
              title={t("summary.publishHint")}
              onClick={async () => {
                try {
                  const res = await api.patch<Summary>(
                    `/grading/courses/${courseId}/summary`,
                    { public: !summary.summary_token },
                  );
                  setSummary(res.data);
                } catch (err) {
                  toast.error(errorMessage(err, t("err.update")));
                }
              }}
            >
              <Link2 />
              {summary.summary_token
                ? t("sheet.unpublish")
                : t("sheet.publish")}
            </Button>
          </CardAction>
        )}
      </CardHeader>
      <CardContent>
        <SummaryTable summary={summary} />
      </CardContent>
    </Card>
  );
}

export function SummaryTable({ summary }: { summary: Summary }) {
  const { t } = useI18n();

  return (
    <div className="overflow-x-auto">
      <table className="w-auto border-collapse text-sm">
        <thead>
          <tr className="border-b">
            <th className="px-4 py-2 text-start">{t("sheet.student")}</th>
            {summary.components.map((component) => (
              <th key={component.id} className="px-4 py-2 text-center">
                {component.name}
                <span className="block text-xs font-normal text-muted-foreground">
                  <bdi>
                    / {component.max_score} · {component.weight}%
                  </bdi>
                </span>
              </th>
            ))}
            <th className="px-4 py-2 text-center">{t("summary.grade")}</th>
          </tr>
        </thead>
        <tbody>
          {summary.rows.map((row) => (
            <tr key={row.student_id} className="border-b last:border-0">
              <td className="px-4 py-2 font-medium tabular-nums">
                <bdi>{row.student_id}</bdi>
                {row.name && (
                  <span className="ms-2 font-normal text-muted-foreground">
                    {row.name}
                  </span>
                )}
              </td>
              {row.totals.map((total, i) => (
                <td key={i} className="px-4 py-2 text-center tabular-nums">
                  <bdi>{total ?? "—"}</bdi>
                </td>
              ))}
              <td className="px-4 py-2 text-center font-medium tabular-nums">
                <bdi>{row.grade ?? "—"}</bdi>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
