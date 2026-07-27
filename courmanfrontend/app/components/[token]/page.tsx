"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { api, errorMessage } from "@/lib/api";
import { ThemeToggle } from "@/components/theme-toggle";
import { LocaleToggle } from "@/components/locale-toggle";
import { useI18n } from "@/lib/i18n";
import { ComponentGrid, type Grid } from "@/components/component-grid";

/** Public: the published combined grid, read only, student IDs only. */
export default function PublicComponentPage() {
  const { token } = useParams<{ token: string }>();
  const { t } = useI18n();
  const [grid, setGrid] = useState<Grid | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    api
      .get<Grid>(`/grading/public/components/${token}`)
      .then((res) => setGrid(res.data))
      .catch((err) => setError(errorMessage(err, t("sheet.notPublished"))));
  }, [token, t]);

  if (!grid)
    return (
      <main className="mx-auto w-full max-w-2xl p-6">
        <p className="text-sm text-muted-foreground">
          {error ?? t("common.loading")}
        </p>
      </main>
    );

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 p-6">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">{t("sheet.combined")}</h1>
          <p className="text-sm text-muted-foreground">{grid.title}</p>
        </div>
        <div className="flex gap-1">
          <LocaleToggle />
          <ThemeToggle />
        </div>
      </div>

      <input
        className="h-9 w-48 rounded-md border bg-transparent px-2 text-sm"
        placeholder={t("course.studentId")}
        aria-label={t("course.studentId")}
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      <ComponentGrid
        grid={{
          ...grid,
          rows: grid.rows.filter((row) => row.student_id.includes(filter)),
        }}
      />
    </main>
  );
}
