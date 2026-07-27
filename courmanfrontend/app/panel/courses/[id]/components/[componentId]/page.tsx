"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, Link2 } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";
import { ComponentGrid, type Grid } from "@/components/component-grid";

/** Every sheet of one component (q1, q2, q3) side by side, publishable. */
export default function ComponentSummaryPage() {
  const { id, componentId } = useParams<{ id: string; componentId: string }>();
  const { t } = useI18n();
  const [grid, setGrid] = useState<Grid | null>(null);

  useEffect(() => {
    api
      .get<Grid>(`/grading/components/${componentId}/summary`)
      .then((res) => setGrid(res.data))
      .catch((err) => toast.error(errorMessage(err, t("summary.loadError"))));
  }, [componentId, t]);

  async function togglePublic() {
    if (!grid) return;
    try {
      const res = await api.patch<{ public_token: string | null }>(
        `/grading/components/${componentId}`,
        { public: !grid.public_token },
      );
      setGrid({ ...grid, public_token: res.data.public_token });
    } catch (err) {
      toast.error(errorMessage(err, t("err.update")));
    }
  }

  return (
    <>
      <div className="flex items-center gap-3">
        <Button
          variant="ghost"
          size="icon"
          render={<Link href={`/panel/courses/${id}`} />}
        >
          <ArrowLeft className="rtl:rotate-180" />
        </Button>
        <div className="flex-1">
          <h1 className="text-xl font-semibold">{t("sheet.combined")}</h1>
          <p className="text-sm text-muted-foreground">{grid?.title}</p>
        </div>
        {grid && (
          <div className="flex items-center gap-2">
            {grid.public_token && (
              <button
                type="button"
                className="flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline"
                onClick={() => {
                  navigator.clipboard.writeText(
                    `${location.origin}/components/${grid.public_token}`,
                  );
                  toast.success(t("signup.copied"));
                }}
              >
                <Link2 className="size-4" /> {t("signup.copyLink")}
              </button>
            )}
            <Button
              size="sm"
              variant={grid.public_token ? "secondary" : "outline"}
              title={t("sheet.publishHint")}
              onClick={togglePublic}
            >
              <Link2 />
              {grid.public_token ? t("sheet.unpublish") : t("sheet.publish")}
            </Button>
          </div>
        )}
      </div>

      {grid ? (
        <ComponentGrid grid={grid} />
      ) : (
        <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
      )}
    </>
  );
}
