"use client";

import { Fragment, useState } from "react";
import { MessageSquare } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export type Cell = { value?: number | null; comment?: string };
export type SubGrade = { id: number; name: string; max_score: number };
export type Sheet = { id: number; title: string; subgrades: SubGrade[] };
export type Row = {
  student_id: string;
  name: string;
  cells: Cell[];
  sheet_totals: (number | null)[];
  total: number | null;
};
export type Grid = {
  title: string;
  sheets: Sheet[];
  rows: Row[];
  /** set while the read-only copy at /components/<token> is published */
  public_token: string | null;
};

/** Every sheet of a component (q1, q2, q3) down to its columns and comments. */
export function ComponentGrid({ grid }: { grid: Grid }) {
  const { t } = useI18n();
  const [reading, setReading] = useState<{
    student: string;
    column: string;
    comment: string;
  } | null>(null);

  return (
    <>
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr>
                <th
                  rowSpan={2}
                  className="sticky start-0 z-10 w-px border-b bg-background px-3 py-2 text-start align-bottom whitespace-nowrap"
                >
                  {t("sheet.student")}
                </th>
                {grid.sheets.map((sheet, i) => (
                  <th
                    key={sheet.id}
                    colSpan={sheet.subgrades.length + 1}
                    className={cn(
                      "border-b px-3 py-1.5 text-center font-medium",
                      // a faint tint per sheet reads better than a hard divider
                      i % 2 === 1 && "bg-muted/30",
                    )}
                  >
                    {sheet.title}
                  </th>
                ))}
                <th
                  rowSpan={2}
                  className="border-b bg-primary/5 px-3 py-2 text-center align-bottom font-medium"
                >
                  {t("sheet.overall")}
                </th>
              </tr>
              <tr className="text-xs text-muted-foreground">
                {grid.sheets.map((sheet, i) => (
                  <Fragment key={sheet.id}>
                    {sheet.subgrades.map((subgrade) => (
                      <th
                        key={subgrade.id}
                        className={cn(
                          "border-b px-3 pb-1.5 font-normal whitespace-nowrap",
                          i % 2 === 1 && "bg-muted/30",
                        )}
                      >
                        <span className="block text-sm text-foreground">
                          {subgrade.name}
                        </span>
                        <bdi>/ {subgrade.max_score}</bdi>
                      </th>
                    ))}
                    <th
                      className={cn(
                        "border-b px-3 pb-1.5 font-normal whitespace-nowrap",
                        i % 2 === 1 && "bg-muted/30",
                      )}
                    >
                      <span className="block text-sm text-foreground">
                        {t("sheet.total")}
                      </span>
                    </th>
                  </Fragment>
                ))}
              </tr>
            </thead>
            <tbody>
              {grid.rows.map((row) => {
                // the flat cell list follows the sheets in order, so walking it
                // alongside the headers keeps every score under its column
                let cursor = 0;
                return (
                  <tr
                    key={row.student_id}
                    className="border-b last:border-0 hover:bg-muted/20"
                  >
                    <td className="sticky start-0 z-10 bg-background px-3 py-1.5 whitespace-nowrap">
                      <span className="font-medium tabular-nums">
                        <bdi>{row.student_id}</bdi>
                      </span>
                      {row.name && (
                        <span className="ms-2 text-muted-foreground">
                          {row.name}
                        </span>
                      )}
                    </td>
                    {grid.sheets.map((sheet, sheetIndex) => (
                      <Fragment key={sheet.id}>
                        {sheet.subgrades.map((subgrade) => {
                          const cell = row.cells[cursor++] ?? {};
                          return (
                            <td
                              key={subgrade.id}
                              className={cn(
                                "px-3 py-1.5 text-center tabular-nums",
                                sheetIndex % 2 === 1 && "bg-muted/20",
                              )}
                            >
                              {cell.value == null ? (
                                <span className="text-muted-foreground">—</span>
                              ) : cell.comment ? (
                                // the score itself opens the note: no floating icon
                                // to knock the column out of alignment
                                <button
                                  type="button"
                                  title={cell.comment}
                                  aria-label={t("sheet.commentFor", {
                                    part: `${sheet.title} ${subgrade.name}`,
                                    student: row.student_id,
                                  })}
                                  className="underline decoration-primary decoration-dotted decoration-2 underline-offset-4"
                                  onClick={() =>
                                    setReading({
                                      student: row.student_id,
                                      column: `${sheet.title} · ${subgrade.name}`,
                                      comment: cell.comment!,
                                    })
                                  }
                                >
                                  <bdi>{cell.value}</bdi>
                                </button>
                              ) : (
                                <bdi>{cell.value}</bdi>
                              )}
                            </td>
                          );
                        })}
                        <td
                          className={cn(
                            "px-3 py-1.5 text-center font-medium tabular-nums",
                            sheetIndex % 2 === 1 && "bg-muted/20",
                          )}
                        >
                          {row.sheet_totals[sheetIndex] == null ? (
                            <span className="font-normal text-muted-foreground">
                              —
                            </span>
                          ) : (
                            <bdi>{row.sheet_totals[sheetIndex]}</bdi>
                          )}
                        </td>
                      </Fragment>
                    ))}
                    <td className="bg-primary/5 px-3 py-1.5 text-center font-medium tabular-nums">
                      {row.total == null ? (
                        <span className="font-normal text-muted-foreground">
                          —
                        </span>
                      ) : (
                        <bdi>{row.total}</bdi>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
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
              <Badge variant="secondary">{reading?.column}</Badge>
              <bdi>{reading?.student}</bdi>
            </DialogDescription>
          </DialogHeader>
          <p className="text-sm whitespace-pre-wrap">{reading?.comment}</p>
        </DialogContent>
      </Dialog>
    </>
  );
}
