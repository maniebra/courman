"use client";

import { useCallback, useEffect, useState } from "react";
import { Check, Plus } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import type { Row } from "@/lib/resources";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

type CatalogueEntry = { name: string; description: string };

/**
 * The actions table takes free text, but only names the backend checks do
 * anything. This lists those names so an operator can create the ones they
 * need instead of inventing dead ones.
 */
export function ActionsHelp({
  rows,
  canWrite,
  onChanged,
}: {
  rows: Row[] | null;
  canWrite: boolean;
  onChanged: () => void;
}) {
  const { t } = useI18n();
  const [catalogue, setCatalogue] = useState<CatalogueEntry[] | null>(null);
  const [creating, setCreating] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<CatalogueEntry[]>("/iam/actions/catalogue")
      .then((res) => setCatalogue(res.data))
      .catch(() => setCatalogue([]));
  }, []);

  const existing = new Set((rows ?? []).map((r) => String(r.name)));

  const create = useCallback(
    async (name: string) => {
      setCreating(name);
      try {
        await api.post("/iam/actions/", { name });
        toast.success(t("common.created"));
        onChanged();
      } catch (err) {
        toast.error(errorMessage(err, t("err.save")));
      } finally {
        setCreating(null);
      }
    },
    [onChanged, t],
  );

  const missing = (catalogue ?? []).filter((a) => !existing.has(a.name));

  async function createAll() {
    for (const action of missing) await create(action.name);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("actionsHelp.title")}</CardTitle>
        <CardDescription>{t("actionsHelp.subtitle")}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-3">
        {catalogue === null && (
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        )}

        <ul className="flex flex-col divide-y">
          {catalogue?.map((action) => {
            const created = existing.has(action.name);
            return (
              <li
                key={action.name}
                className="flex flex-wrap items-center gap-3 py-2 first:pt-0"
              >
                <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                  <bdi>{action.name}</bdi>
                </code>
                <span className="min-w-40 flex-1 text-sm text-muted-foreground">
                  {action.description}
                </span>
                {created ? (
                  <span className="flex items-center gap-1 text-xs text-emerald-600 dark:text-emerald-500">
                    <Check className="size-3" /> {t("actionsHelp.created")}
                  </span>
                ) : canWrite ? (
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={creating === action.name}
                    onClick={() => create(action.name)}
                  >
                    <Plus /> {t("common.add")}
                  </Button>
                ) : (
                  <span className="text-xs text-muted-foreground">
                    {t("actionsHelp.missing")}
                  </span>
                )}
              </li>
            );
          })}
        </ul>

        {canWrite && missing.length > 1 && (
          <div>
            <Button size="sm" onClick={createAll} disabled={creating !== null}>
              <Plus /> {t("actionsHelp.createAll", { count: missing.length })}
            </Button>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          {t("actionsHelp.footnote")}
        </p>
      </CardContent>
    </Card>
  );
}
