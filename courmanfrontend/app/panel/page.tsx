"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

import { listAll } from "@/lib/api";
import { resources } from "@/lib/resources";
import { useI18n } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Todo } from "@/components/todo";

export default function AdminDashboard() {
  const { t } = useI18n();
  const { can } = useSession();
  const visible = resources.filter((r) => r.visible(can));
  const [counts, setCounts] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    Promise.all(
      visible.map((r) =>
        listAll(r.basePath, 1)
          .then((d) => [r.key, d.count] as const)
          .catch(() => [r.key, -1] as const),
      ),
    ).then((pairs) => setCounts(Object.fromEntries(pairs)));
    // `visible` is derived from the session user, which is stable for the page
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          {t("nav.dashboard")}
        </h1>
        <p className="text-sm text-muted-foreground">{t("dash.subtitle")}</p>
      </div>

      <Todo />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {visible.map((r) => (
          <Link key={r.key} href={`/panel/${r.key}`} className="group">
            <Card className="h-full gap-0 transition-all group-hover:border-primary/40 group-hover:shadow-md group-hover:shadow-primary/5">
              <CardHeader className="flex! flex-row items-start justify-between">
                <div className="flex flex-col gap-1">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {t(r.labelKey)}
                  </CardTitle>
                  {counts === null ? (
                    <Skeleton className="h-9 w-14" />
                  ) : (
                    <p className="font-heading text-3xl font-semibold tabular-nums">
                      <bdi>{counts[r.key] < 0 ? "—" : counts[r.key]}</bdi>
                    </p>
                  )}
                </div>
                <span className="rounded-lg bg-primary/10 p-2 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <r.icon className="size-4" />
                </span>
              </CardHeader>
              <CardContent className="mt-2">
                <span className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors group-hover:text-primary">
                  {t("common.manage")}
                  <ArrowRight className="size-3 rtl:rotate-180" />
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </>
  );
}
