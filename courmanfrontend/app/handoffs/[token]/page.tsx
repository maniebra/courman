"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CheckCircle2 } from "lucide-react";

import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import { LocaleToggle } from "@/components/locale-toggle";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type Slot = {
  id: number;
  start: string;
  end: string;
  ta: string;
  taken: boolean;
};
type HandoffForm = {
  course: string;
  title: string;
  description: string;
  group_type: string;
  slots: Slot[];
};

/** Public: a group member picks a slot, no account involved. */
export default function HandoffBookingPage() {
  const { token } = useParams<{ token: string }>();
  const { t, locale } = useI18n();
  const [form, setForm] = useState<HandoffForm | null>(null);
  const [studentId, setStudentId] = useState("");
  const [slotId, setSlotId] = useState<number | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get<HandoffForm>(`/courses/public/handoff-forms/${token}`)
      .then((res) => setForm(res.data))
      .catch((err) => setError(errorMessage(err, t("handoff.closed"))));
  }, [token, t]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const res = await api.post<{ detail: string }>(
        `/courses/public/handoff-forms/${token}`,
        {
          student_id: studentId,
          slot_id: slotId,
          teammates_confirmed: confirmed,
        },
      );
      setDone(res.data.detail);
    } catch (err) {
      setError(errorMessage(err, t("handoff.error")));
    } finally {
      setSaving(false);
    }
  }

  const time = (value: string) =>
    new Date(value).toLocaleTimeString(locale, { timeStyle: "short" });

  const days = new Map<string, Slot[]>();
  for (const slot of form?.slots ?? []) {
    const day = new Date(slot.start).toLocaleDateString(locale, {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
    days.set(day, [...(days.get(day) ?? []), slot]);
  }

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center gap-4 p-6">
      <div className="flex justify-end gap-1">
        <LocaleToggle />
        <ThemeToggle />
      </div>

      {!form ? (
        <p className="text-sm text-muted-foreground">
          {error ?? t("common.loading")}
        </p>
      ) : done ? (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <CheckCircle2 className="size-5" /> {done}
            </CardTitle>
            <CardDescription>{t("handoff.doneHint")}</CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {form.course} · {form.title}
            </CardTitle>
            <CardDescription>
              {form.description || t("handoff.subtitle")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-4" onSubmit={submit}>
              <div className="flex flex-col gap-2">
                <Label htmlFor="student-id">{t("course.studentId")}</Label>
                <Input
                  id="student-id"
                  inputMode="numeric"
                  value={studentId}
                  onChange={(e) => setStudentId(e.target.value)}
                  required
                />
                <p className="text-sm text-muted-foreground">
                  {t("handoff.idHint", { type: form.group_type })}
                </p>
              </div>

              <fieldset className="flex flex-col gap-3">
                <legend className="mb-2 text-sm font-medium">
                  {t("handoff.pickSlot")}
                </legend>
                {form.slots.length === 0 && (
                  <p className="text-sm text-muted-foreground">
                    {t("handoff.noSlots")}
                  </p>
                )}
                {/* a column per day: the same schedule the staff see */}
                <div className="grid gap-4 sm:grid-cols-2">
                  {[...days].map(([day, slots]) => (
                    <div key={day} className="flex flex-col gap-2">
                      <p className="text-sm font-medium">{day}</p>
                      {slots.map((slot) => (
                        <label
                          key={slot.id}
                          className={cn(
                            "flex cursor-pointer items-center gap-2 rounded-md border px-2 py-1.5 text-sm transition-colors",
                            "has-checked:border-primary has-checked:bg-primary/10",
                            slot.taken &&
                              "cursor-not-allowed bg-muted/40 text-muted-foreground",
                          )}
                        >
                          <input
                            type="radio"
                            name="slot"
                            className="sr-only"
                            value={slot.id}
                            disabled={slot.taken}
                            checked={slotId === slot.id}
                            onChange={() => setSlotId(slot.id)}
                          />
                          <span className="flex-1 tabular-nums">
                            <bdi>
                              {time(slot.start)}–{time(slot.end)}
                            </bdi>
                          </span>
                          {slot.taken ? (
                            <span className="text-xs">
                              {t("handoff.taken")}
                            </span>
                          ) : (
                            slot.ta && (
                              <span className="text-xs text-muted-foreground">
                                {slot.ta}
                              </span>
                            )
                          )}
                        </label>
                      ))}
                    </div>
                  ))}
                </div>
              </fieldset>

              <label className="flex items-start gap-2 text-sm">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                  required
                />
                {t("handoff.confirm")}
              </label>

              {error && <p className="text-sm text-destructive">{error}</p>}

              <Button type="submit" disabled={saving || !slotId}>
                {saving ? t("common.saving") : t("handoff.submit")}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
