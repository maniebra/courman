"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { CheckCircle2, Plus, Trash2 } from "lucide-react";

import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ThemeToggle } from "@/components/theme-toggle";
import { LocaleToggle } from "@/components/locale-toggle";
import { useI18n } from "@/lib/i18n";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type SignupForm = {
  course: string;
  title: string;
  description: string;
  min_members: number;
  max_members: number;
};

/** Public: anyone with the link fills this in, no account involved. */
export default function GroupSignupPage() {
  const { token } = useParams<{ token: string }>();
  const { t } = useI18n();
  const [form, setForm] = useState<SignupForm | null>(null);
  const [ids, setIds] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .get<SignupForm>(`/courses/public/group-signups/${token}`)
      .then((res) => {
        setForm(res.data);
        setIds(Array(res.data.min_members).fill(""));
      })
      .catch((err) => setError(errorMessage(err, t("signup.closed"))));
  }, [token, t]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const res = await api.post<{ detail: string }>(
        `/courses/public/group-signups/${token}`,
        { student_ids: ids },
      );
      setDone(res.data.detail);
    } catch (err) {
      setError(errorMessage(err, t("signup.error")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-lg flex-1 flex-col justify-center gap-4 p-6">
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
            <CardDescription>{t("signup.doneHint")}</CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {form.course} · {form.title}
            </CardTitle>
            <CardDescription>
              {form.description || t("signup.subtitle")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form className="flex flex-col gap-4" onSubmit={submit}>
              <div className="flex flex-col gap-2">
                <Label>
                  {t("signup.members", {
                    min: form.min_members,
                    max: form.max_members,
                  })}
                </Label>
                {ids.map((id, i) => (
                  <div key={i} className="flex gap-2">
                    <Input
                      aria-label={t("signup.memberN", { n: i + 1 })}
                      inputMode="numeric"
                      placeholder={t("course.studentId")}
                      value={id}
                      onChange={(e) =>
                        setIds(ids.map((v, j) => (j === i ? e.target.value : v)))
                      }
                      required
                    />
                    {ids.length > form.min_members && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        title={t("common.delete")}
                        onClick={() => setIds(ids.filter((_, j) => j !== i))}
                      >
                        <Trash2 />
                      </Button>
                    )}
                  </div>
                ))}
                {ids.length < form.max_members && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setIds([...ids, ""])}
                  >
                    <Plus /> {t("signup.addMember")}
                  </Button>
                )}
              </div>

              {error && <p className="text-sm text-destructive">{error}</p>}

              <Button type="submit" disabled={saving}>
                {saving ? t("common.saving") : t("signup.submit")}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
