"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { MessageSquare } from "lucide-react";

import { api, errorMessage } from "@/lib/api";
import { ThemeToggle } from "@/components/theme-toggle";
import { LocaleToggle } from "@/components/locale-toggle";
import { useI18n } from "@/lib/i18n";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type Cell = { value?: number | null; comment?: string };
type Row = {
  student_id: string;
  cells: Cell[];
  total: number | null;
};
type PublicSheet = {
  course: string;
  component: string;
  title: string;
  subgrades: string[];
  max_scores: number[];
  rows: Row[];
};

/** Public: the published sheet, read only, student IDs and numbers only. */
export default function PublicSheetPage() {
  const { token } = useParams<{ token: string }>();
  const { t } = useI18n();
  const [sheet, setSheet] = useState<PublicSheet | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  // in a dialog, not inline: expanding a comment must not shove the table around
  const [reading, setReading] = useState<{
    student: string;
    subgrade: string;
    comment: string;
  } | null>(null);

  useEffect(() => {
    api
      .get<PublicSheet>(`/grading/public/sheets/${token}`)
      .then((res) => setSheet(res.data))
      .catch((err) => setError(errorMessage(err, t("sheet.notPublished"))));
  }, [token, t]);

  if (!sheet)
    return (
      <main className="mx-auto w-full max-w-2xl p-6">
        <p className="text-sm text-muted-foreground">
          {error ?? t("common.loading")}
        </p>
      </main>
    );

  const rows = sheet.rows.filter((row) => row.student_id.includes(filter));

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-4 p-6">
      <div className="flex items-start justify-between gap-2">
        <div>
          <h1 className="text-xl font-semibold">{sheet.title}</h1>
          <p className="text-sm text-muted-foreground">
            {sheet.course} · {sheet.component}
          </p>
        </div>
        <div className="flex gap-1">
          <LocaleToggle />
          <ThemeToggle />
        </div>
      </div>

      {/* a published sheet is long; finding your own row should not need Ctrl+F */}
      <input
        className="h-9 w-48 rounded-md border bg-transparent px-2 text-sm"
        placeholder={t("course.studentId")}
        aria-label={t("course.studentId")}
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
      />

      <div className="flex justify-center overflow-x-auto">
        <Table className="w-auto">
          <TableHeader>
            <TableRow>
              <TableHead className="h-9 px-4 py-2">{t("sheet.student")}</TableHead>
              {sheet.subgrades.map((name, i) => (
                <TableHead key={name} className="h-9 px-4 py-2 text-center">
                  {name}
                  <span className="block text-xs font-normal text-muted-foreground">
                    <bdi>/ {sheet.max_scores[i]}</bdi>
                  </span>
                </TableHead>
              ))}
              <TableHead className="h-9 px-4 py-2 text-center">
                {t("sheet.total")}
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.student_id}>
                <TableCell className="px-4 py-2 font-medium tabular-nums">
                  <bdi>{row.student_id}</bdi>
                </TableCell>
                {row.cells.map((cell, i) => (
                  // the icon sits in the corner so the number stays centred
                  <TableCell
                    key={i}
                    className="relative px-5 py-2 text-center tabular-nums"
                  >
                    <bdi>{cell.value ?? "—"}</bdi>
                    {cell.comment && (
                      <button
                        type="button"
                        title={t("sheet.comment")}
                        aria-label={t("sheet.commentFor", {
                          part: sheet.subgrades[i],
                          student: row.student_id,
                        })}
                        className="absolute end-0.5 top-0.5 text-primary"
                        onClick={() =>
                          setReading({
                            student: row.student_id,
                            subgrade: sheet.subgrades[i],
                            comment: cell.comment!,
                          })
                        }
                      >
                        <MessageSquare className="size-3" />
                      </button>
                    )}
                  </TableCell>
                ))}
                <TableCell className="px-4 py-2 text-center font-medium tabular-nums">
                  <bdi>{row.total ?? "—"}</bdi>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      <Dialog
        open={reading !== null}
        onOpenChange={(open) => !open && setReading(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="size-4 text-muted-foreground" />
              {t("sheet.comment")}
            </DialogTitle>
            <DialogDescription className="flex flex-wrap items-center gap-1.5">
              <Badge variant="secondary">{reading?.subgrade}</Badge>
              <bdi>{reading?.student}</bdi>
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm whitespace-pre-wrap">{reading?.comment}</p>
        </DialogContent>
      </Dialog>
    </main>
  );
}
