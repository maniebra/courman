"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { listAll } from "@/lib/api";
import { resources } from "@/lib/resources";
import { useI18n } from "@/lib/i18n";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function AdminDashboard() {
  const { t } = useI18n();
  const [counts, setCounts] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    Promise.all(
      resources.map((r) =>
        listAll(r.basePath, 1)
          .then((d) => [r.key, d.count] as const)
          .catch(() => [r.key, -1] as const),
      ),
    ).then((pairs) => setCounts(Object.fromEntries(pairs)));
  }, []);

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {resources.map((r) => (
        <Link key={r.key} href={`/admin/${r.key}`}>
          <Card className="transition-colors hover:border-foreground/20">
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-sm font-medium">{t(r.labelKey)}</CardTitle>
              <r.icon className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {counts === null ? (
                <Skeleton className="h-8 w-12" />
              ) : (
                <p className="text-3xl font-semibold">
                  {counts[r.key] < 0 ? "—" : counts[r.key]}
                </p>
              )}
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
