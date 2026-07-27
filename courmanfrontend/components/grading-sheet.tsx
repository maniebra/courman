"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Link2, MessageSquare, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

type Student = { id: number; student_id: string; name: string };
type Sheet = {
  id: number;
  component: number;
  title: string;
  /** set while the read-only copy at /sheets/<token> is published */
  public_token: string | null;
};
type SubGrade = { id: number; name: string; max_score: string };
type Score = {
  comment: string;
  id: number;
  subgrade: number;
  student: number;
  value: string | null;
};

type Entry = { subgrade: number; student: number; value: number | null };

type Full = {
  sheet: Sheet;
  subgrades: SubGrade[];
  students: Student[];
  scores: Score[];
  can_edit: boolean;
  /** empty when every column is theirs; otherwise the only ones they may fill */
  editable_subgrades: number[];
};

/**
 * The score matrix for one grading sheet. `can_edit` comes from the API —
 * professors and head TAs always, a TA only for components they were assigned.
 */
export function GradingSheet({
  sheetId,
  canManage,
  onDeleted,
}: {
  sheetId: number;
  /** professor / head TA of the course: may restructure and delete */
  canManage: boolean;
  onDeleted: () => void;
}) {
  const { t } = useI18n();
  const [full, setFull] = useState<Full | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Full>(`/grading/sheets/${sheetId}/full`);
      setFull(res.data);
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.loadError")));
    }
  }, [sheetId, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  async function remove() {
    if (!confirm(t("sheet.deleteConfirm"))) return;
    try {
      await api.delete(`/grading/sheets/${sheetId}`);
      onDeleted();
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.deleteError")));
    }
  }

  if (!full) {
    return (
      <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-xl font-semibold">{full.sheet.title}</h1>
        {canManage && (
          <div className="flex items-center gap-2">
            {full.sheet.public_token && (
              <button
                type="button"
                className="flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline"
                onClick={() => {
                  navigator.clipboard.writeText(
                    `${location.origin}/sheets/${full.sheet.public_token}`,
                  );
                  toast.success(t("signup.copied"));
                }}
              >
                <Link2 className="size-4" /> {t("signup.copyLink")}
              </button>
            )}
            <Button
              size="sm"
              variant={full.sheet.public_token ? "secondary" : "outline"}
              title={t("sheet.publishHint")}
              onClick={async () => {
                try {
                  await api.patch(`/grading/sheets/${sheetId}`, {
                    public: !full.sheet.public_token,
                  });
                  load();
                } catch (err) {
                  toast.error(errorMessage(err, t("err.update")));
                }
              }}
            >
              <Link2 />
              {full.sheet.public_token
                ? t("sheet.unpublish")
                : t("sheet.publish")}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              title={t("common.delete")}
              onClick={remove}
            >
              <Trash2 />
            </Button>
          </div>
        )}
      </div>

      <Grid
        full={full}
        canManage={canManage}
        onChanged={load}
        sheetId={sheetId}
      />
    </div>
  );
}

function Grid({
  full,
  canManage,
  sheetId,
  onChanged,
}: {
  full: Full;
  canManage: boolean;
  sheetId: number;
  onChanged: () => void;
}) {
  const { t } = useI18n();
  // a TA assigned to q1 only may type in that column and nowhere else
  const canEditColumn = (subgradeId: number) =>
    full.can_edit &&
    (full.editable_subgrades.length === 0 ||
      full.editable_subgrades.includes(subgradeId));
  const [name, setName] = useState("");
  const [max, setMax] = useState("100");
  const cells = useRef<(HTMLInputElement | null)[][]>([]);
  const [commenting, setCommenting] = useState<{
    student: Student;
    subgrade: SubGrade;
  } | null>(null);

  const cellOf = (studentId: number, subgradeId: number) =>
    full.scores.find(
      (s) => s.student === studentId && s.subgrade === subgradeId,
    );

  const scoreOf = (studentId: number, subgradeId: number) =>
    cellOf(studentId, subgradeId)?.value ?? "";

  async function addSubgrade(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.post(`/grading/sheets/${sheetId}/subgrades`, {
        name,
        max_score: Number(max),
      });
      setName("");
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.subgradeError")));
    }
  }

  async function removeSubgrade(id: number) {
    if (!confirm(t("common.deleteConfirm", { item: t("sheet.subgradeName") })))
      return;
    try {
      await api.delete(`/grading/subgrades/${id}`);
      onChanged();
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.subgradeError")));
    }
  }

  /** One PUT per changed cell; a pasted block goes through the bulk endpoint. */
  async function saveScores(entries: Entry[]) {
    const changed = entries.filter(
      (e) => String(e.value ?? "") !== scoreOf(e.student, e.subgrade),
    );
    if (changed.length === 0) return;
    try {
      if (changed.length === 1) {
        const [one] = changed;
        await api.put(
          `/grading/subgrades/${one.subgrade}/scores/${one.student}`,
          { value: one.value },
        );
      } else {
        await api.put(`/grading/sheets/${sheetId}/scores`, { scores: changed });
      }
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.scoreError")));
    } finally {
      onChanged();
    }
  }

  const cellValue = (raw: string) => (raw.trim() === "" ? null : Number(raw));

  /** Arrow keys, Enter and Tab walk the grid the way a spreadsheet does. */
  function move(row: number, col: number, dRow: number, dCol: number) {
    const target = cells.current[row + dRow]?.[col + dCol];
    if (!target) return false;
    target.focus();
    target.select();
    return true;
  }

  function onKeyDown(
    e: React.KeyboardEvent<HTMLInputElement>,
    row: number,
    col: number,
  ) {
    const steps: Record<string, [number, number]> = {
      ArrowUp: [-1, 0],
      ArrowDown: [1, 0],
      Enter: [e.shiftKey ? -1 : 1, 0],
      Tab: [0, e.shiftKey ? -1 : 1],
    };
    const step = steps[e.key];
    if (step && move(row, col, step[0], step[1])) e.preventDefault();
    if (e.key === "Escape") {
      e.currentTarget.value = scoreOf(
        full.students[row].id,
        full.subgrades[col].id,
      );
      e.currentTarget.blur();
    }
  }

  /** Excel copies a block as tab-separated columns, newline-separated rows. */
  function onPaste(
    e: React.ClipboardEvent<HTMLInputElement>,
    row: number,
    col: number,
  ) {
    const text = e.clipboardData.getData("text/plain").replace(/\r/g, "");
    if (!text.includes("\t") && !text.includes("\n")) return; // single value: let the input take it
    e.preventDefault();

    const entries: Entry[] = [];
    text.split("\n").forEach((line, r) => {
      if (line === "") return;
      line.split("\t").forEach((raw, c) => {
        const student = full.students[row + r];
        const subgrade = full.subgrades[col + c];
        if (!student || !subgrade) return; // a paste wider than the sheet is clipped
        const input = cells.current[row + r]?.[col + c];
        if (input) input.value = raw.trim();
        entries.push({
          student: student.id,
          subgrade: subgrade.id,
          value: cellValue(raw),
        });
      });
    });
    saveScores(entries);
  }

  const total = (studentId: number) =>
    full.subgrades.reduce(
      (sum, sg) => sum + Number(scoreOf(studentId, sg.id) || 0),
      0,
    );

  if (full.students.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">{t("sheet.noStudents")}</p>
    );
  }

  return (
    <>
      <p className="text-xs text-muted-foreground">
        {full.can_edit ? t("sheet.hint") : t("sheet.readOnly")}
      </p>

      <div className="max-h-[70vh] overflow-auto rounded-md border">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr>
              <th className="sticky start-0 top-0 z-20 min-w-40 border-b border-e bg-muted px-2 py-1.5 text-start font-medium">
                {t("sheet.student")}
              </th>
              {full.subgrades.map((sg) => (
                <th
                  key={sg.id}
                  className="sticky top-0 z-10 min-w-28 border-b border-e bg-muted px-2 py-1.5 text-start font-medium"
                >
                  <span className="flex items-center gap-1">
                    {sg.name}
                    <span className="text-muted-foreground">
                      /<bdi>{sg.max_score}</bdi>
                    </span>
                    {canManage && (
                      <button
                        type="button"
                        className="ms-auto"
                        aria-label={`${t("common.delete")} ${sg.name}`}
                        onClick={() => removeSubgrade(sg.id)}
                      >
                        <Trash2 className="size-3" />
                      </button>
                    )}
                  </span>
                </th>
              ))}
              <th className="sticky top-0 z-10 border-b bg-muted px-2 py-1.5 text-start font-medium">
                {t("sheet.total")}
              </th>
            </tr>
          </thead>
          <tbody>
            {full.subgrades.length === 0 && (
              <tr>
                <td className="px-2 py-2 text-muted-foreground" colSpan={2}>
                  {t("sheet.noSubgrades")}
                </td>
              </tr>
            )}
            {full.subgrades.length > 0 &&
              full.students.map((student, row) => (
                <tr key={student.id} className="even:bg-muted/30">
                  <td className="sticky start-0 z-10 border-b border-e bg-background px-2 py-1 font-medium">
                    <bdi className="tabular-nums">{student.student_id}</bdi>
                    {student.name && (
                      <span className="ms-2 font-normal text-muted-foreground">
                        {student.name}
                      </span>
                    )}
                  </td>
                  {full.subgrades.map((sg, col) => (
                    <td
                      key={sg.id}
                      className="group relative border-b border-e p-0"
                    >
                      <button
                        type="button"
                        title={t("sheet.comment")}
                        aria-label={t("sheet.commentFor", {
                          part: sg.name,
                          student: student.student_id,
                        })}
                        onClick={() => setCommenting({ student, subgrade: sg })}
                        className={cn(
                          "absolute end-0.5 top-0.5 z-10 text-muted-foreground opacity-0 transition-opacity group-focus-within:opacity-100 group-hover:opacity-100",
                          cellOf(student.id, sg.id)?.comment &&
                            "text-primary opacity-100",
                        )}
                      >
                        <MessageSquare className="size-3" />
                      </button>
                      <input
                        ref={(el) => {
                          (cells.current[row] ??= [])[col] = el;
                        }}
                        type="text"
                        inputMode="decimal"
                        aria-label={`${student.student_id} - ${sg.name}`}
                        className="w-full bg-transparent px-2 py-1 text-start tabular-nums outline-none focus:bg-primary/10 focus:ring-1 focus:ring-primary focus:ring-inset disabled:text-muted-foreground"
                        disabled={!canEditColumn(sg.id)}
                        key={`${sg.id}-${scoreOf(student.id, sg.id)}`}
                        defaultValue={scoreOf(student.id, sg.id)}
                        onKeyDown={(e) => onKeyDown(e, row, col)}
                        onPaste={(e) => onPaste(e, row, col)}
                        onBlur={(e) =>
                          saveScores([
                            {
                              student: student.id,
                              subgrade: sg.id,
                              value: cellValue(e.target.value),
                            },
                          ])
                        }
                      />
                    </td>
                  ))}
                  <td className="border-b px-2 py-1 tabular-nums">
                    <bdi>{total(student.id)}</bdi>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {commenting && (
        <CommentDialog
          student={commenting.student}
          subgrade={commenting.subgrade}
          score={scoreOf(commenting.student.id, commenting.subgrade.id)}
          initial={
            cellOf(commenting.student.id, commenting.subgrade.id)?.comment ?? ""
          }
          readOnly={!canEditColumn(commenting.subgrade.id)}
          onClose={() => setCommenting(null)}
          onSaved={onChanged}
        />
      )}

      {canManage && (
        <form className="flex gap-2" onSubmit={addSubgrade}>
          <Input
            placeholder={t("sheet.subgradeName")}
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            type="number"
            step="0.25"
            min="0"
            className="w-24"
            placeholder={t("sheet.maxScore")}
            value={max}
            onChange={(e) => setMax(e.target.value)}
            required
          />
          <Button type="submit" size="sm">
            <Plus /> {t("common.add")}
          </Button>
        </form>
      )}
    </>
  );
}

/** Graders leave feedback per cell: which part, whose answer, what it scored. */
function CommentDialog({
  student,
  subgrade,
  score,
  initial,
  readOnly,
  onClose,
  onSaved,
}: {
  student: Student;
  subgrade: SubGrade;
  score: string;
  initial: string;
  readOnly: boolean;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const [comment, setComment] = useState(initial);
  const [saving, setSaving] = useState(false);

  async function put(value: string) {
    setSaving(true);
    try {
      await api.put(`/grading/subgrades/${subgrade.id}/scores/${student.id}`, {
        comment: value,
      });
      onSaved();
      onClose();
    } catch (err) {
      toast.error(errorMessage(err, t("sheet.commentError")));
      setSaving(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="size-4 text-muted-foreground" />
            {t("sheet.comment")}
          </DialogTitle>
          <DialogDescription className="flex flex-wrap items-center gap-1.5">
            <Badge variant="secondary">{subgrade.name}</Badge>
            <span>{student.name || student.student_id}</span>
            <span className="text-muted-foreground">·</span>
            <span className="tabular-nums">
              <bdi>
                {score === "" ? "—" : score}/{subgrade.max_score}
              </bdi>
            </span>
          </DialogDescription>
        </DialogHeader>

        <form
          className="flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            put(comment);
          }}
        >
          <Textarea
            autoFocus
            rows={6}
            className="resize-y"
            readOnly={readOnly}
            placeholder={t("sheet.commentPlaceholder")}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            // the shortcut every comment box has; the form submit stays for the mouse
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !readOnly) {
                e.preventDefault();
                put(comment);
              }
            }}
          />

          <DialogFooter className="sm:justify-between">
            {!readOnly && initial !== "" ? (
              <Button
                type="button"
                variant="ghost"
                className="text-destructive"
                disabled={saving}
                onClick={() => put("")}
              >
                <Trash2 /> {t("sheet.clearComment")}
              </Button>
            ) : (
              <span className="hidden text-xs text-muted-foreground sm:block">
                {readOnly ? "" : t("sheet.commentHint")}
              </span>
            )}
            <div className="flex gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                {readOnly ? t("common.done") : t("common.cancel")}
              </Button>
              {!readOnly && (
                <Button type="submit" disabled={saving}>
                  {saving ? t("common.saving") : t("common.save")}
                </Button>
              )}
            </div>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
