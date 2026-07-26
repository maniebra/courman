"use client";

import { useCallback, useEffect, useState } from "react";
import NextLink from "next/link";
import { notFound, useParams } from "next/navigation";
import { ExternalLink, Pencil, Plus, Trash2, Link2 } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage, listAll } from "@/lib/api";
import {
  getResource,
  type Column,
  type Field,
  type Resource,
  type Row,
} from "@/lib/resources";
import { useI18n } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogFooter,
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

export default function ResourcePage() {
  const { resource: key } = useParams<{ resource: string }>();
  const { user } = useSession();
  const resource = getResource(key);
  if (!resource || !resource.visible(user)) notFound();
  // key in the route changes => remount, so per-resource state never leaks
  return <ResourceCrud key={key} resource={resource} />;
}

function ResourceCrud({ resource }: { resource: Resource }) {
  const { t } = useI18n();
  const { user } = useSession();
  const canWrite = resource.canWrite(user);
  const [rows, setRows] = useState<Row[] | null>(null);
  const [editing, setEditing] = useState<Row | "new" | null>(null);
  const [linking, setLinking] = useState<Row | null>(null);

  const load = useCallback(async () => {
    try {
      const { items } = await listAll<Row>(resource.basePath);
      setRows(items);
    } catch (err) {
      toast.error(
        errorMessage(err, t("err.load", { item: t(resource.labelKey) })),
      );
      setRows([]);
    }
  }, [resource, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  async function handleDelete(row: Row) {
    if (!confirm(t("common.deleteConfirm", { item: t(resource.singularKey) })))
      return;
    try {
      await api.delete(`${resource.basePath}/${row.id}`);
      toast.success(t("common.deleted"));
      load();
    } catch (err) {
      toast.error(errorMessage(err, t("err.delete")));
    }
  }

  return (
    <>
      <Card className="[--card-spacing:0px] overflow-hidden">
        <div className="flex items-center justify-between gap-4 border-b px-5 py-4">
          <div>
            <h1 className="font-heading text-lg font-semibold">
              {t(resource.labelKey)}
            </h1>
            <p className="text-sm text-muted-foreground">
              {rows === null
                ? t("common.loading")
                : t("list.count", { count: rows.length })}
            </p>
          </div>
          {canWrite && (
            <Button onClick={() => setEditing("new")}>
              <Plus /> {t("common.new")}
            </Button>
          )}
        </div>

        <Table>
          <TableHeader>
            <TableRow>
              {resource.columns.map((c) => (
                <TableHead
                  key={c.labelKey}
                  className="h-9 px-5 text-xs font-medium tracking-wide text-muted-foreground uppercase"
                >
                  {t(c.labelKey)}
                </TableHead>
              ))}
              <TableHead className="w-0" />
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows === null && (
              <TableRow>
                <TableCell
                  colSpan={resource.columns.length + 1}
                  className="px-5 py-10 text-center text-muted-foreground"
                >
                  {t("common.loading")}
                </TableCell>
              </TableRow>
            )}
            {rows?.length === 0 && (
              <TableRow>
                <TableCell
                  colSpan={resource.columns.length + 1}
                  className="px-5 py-10 text-center text-muted-foreground"
                >
                  {t("common.nothingHere")}
                </TableCell>
              </TableRow>
            )}
            {rows?.map((row) => (
              <TableRow key={row.id} className="group/row">
                {resource.columns.map((c, i) => (
                  <TableCell key={c.labelKey} className="px-5 py-3">
                    {i === 0 && resource.detailPath ? (
                      <NextLink
                        href={resource.detailPath(row.id)}
                        className="font-medium text-primary underline-offset-4 hover:underline"
                      >
                        {c.render(row, t)}
                      </NextLink>
                    ) : (
                      <Cell column={c} row={row} />
                    )}
                  </TableCell>
                ))}
                <TableCell className="flex justify-end gap-1 px-5 py-3">
                  {resource.detailPath && (
                    <Button
                      variant="outline"
                      size="sm"
                      render={<NextLink href={resource.detailPath(row.id)} />}
                    >
                      <ExternalLink /> {t("common.manage")}
                    </Button>
                  )}
                  {canWrite && resource.link && (
                    <Button
                      variant="ghost"
                      size="icon"
                      title={t(resource.link.labelKey)}
                      onClick={() => setLinking(row)}
                    >
                      <Link2 />
                    </Button>
                  )}
                  {canWrite && (
                    <>
                      <Button
                        variant="ghost"
                        size="icon"
                        title={t("common.edit")}
                        onClick={() => setEditing(row)}
                      >
                        <Pencil />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        title={t("common.delete")}
                        onClick={() => handleDelete(row)}
                      >
                        <Trash2 />
                      </Button>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>

      {editing && (
        <RowDialog
          resource={resource}
          row={editing === "new" ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={load}
        />
      )}
      {linking && (
        <LinkDialog
          resource={resource}
          row={linking}
          onClose={() => setLinking(null)}
          onSaved={load}
        />
      )}
    </>
  );
}

/** Chips for lists, a status dot for booleans, plain text otherwise. */
function Cell({ column, row }: { column: Column; row: Row }) {
  const { t } = useI18n();

  if (column.bool) {
    const on = column.bool(row);
    return (
      <span className="flex items-center gap-2">
        <span
          className={cn(
            "size-1.5 rounded-full",
            on ? "bg-emerald-500" : "bg-muted-foreground/40",
          )}
        />
        <span className={on ? "" : "text-muted-foreground"}>
          {t(on ? "common.yes" : "common.no")}
        </span>
      </span>
    );
  }

  if (column.chips) {
    const items = column.chips(row);
    if (items.length === 0)
      return <span className="text-muted-foreground">—</span>;
    return (
      <span className="flex flex-wrap gap-1">
        {items.map((item) => (
          <Badge key={item} variant="secondary">
            {item}
          </Badge>
        ))}
      </span>
    );
  }

  const text = column.render(row, t);
  return text === "—" ? (
    <span className="text-muted-foreground">—</span>
  ) : (
    <>{text}</>
  );
}

function RowDialog({
  resource,
  row,
  onClose,
  onSaved,
}: {
  resource: Resource;
  row: Row | null;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const fields = row ? resource.updateFields : resource.createFields;
  const [values, setValues] = useState<Record<string, string | boolean>>(() =>
    Object.fromEntries(
      fields.map((f) => [
        f.name,
        f.type === "checkbox"
          ? Boolean(row?.[f.name] ?? true)
          : String(row?.[f.name] ?? ""),
      ]),
    ),
  );
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (row) await api.patch(`${resource.basePath}/${row.id}`, values);
      else await api.post(`${resource.basePath}/`, values);
      toast.success(t(row ? "common.saved" : "common.created"));
      onSaved();
      onClose();
    } catch (err) {
      toast.error(errorMessage(err, t("err.save")));
    } finally {
      setSaving(false);
    }
  }

  const set = (f: Field, v: string | boolean) =>
    setValues((prev) => ({ ...prev, [f.name]: v }));

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {t(row ? "common.editTitle" : "common.newTitle", {
              item: t(resource.singularKey),
            })}
          </DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={handleSubmit}>
          {fields.map((f) => (
            <div key={f.name} className="flex flex-col gap-2">
              {f.type === "checkbox" ? (
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={Boolean(values[f.name])}
                    onChange={(e) => set(f, e.target.checked)}
                  />
                  {t(f.labelKey)}
                </label>
              ) : (
                <>
                  <Label htmlFor={f.name}>{t(f.labelKey)}</Label>
                  {f.type === "textarea" ? (
                    <Textarea
                      id={f.name}
                      value={String(values[f.name])}
                      onChange={(e) => set(f, e.target.value)}
                      required={f.required}
                    />
                  ) : (
                    <Input
                      id={f.name}
                      type={f.type ?? "text"}
                      value={String(values[f.name])}
                      onChange={(e) => set(f, e.target.value)}
                      required={f.required}
                    />
                  )}
                </>
              )}
            </div>
          ))}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? t("common.saving") : t("common.save")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function LinkDialog({
  resource,
  row,
  onClose,
  onSaved,
}: {
  resource: Resource;
  row: Row;
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const link = resource.link!;
  const target = getResource(link.options)!;
  const [options, setOptions] = useState<Row[] | null>(null);
  const [linked, setLinked] = useState<number[]>(() =>
    ((row[link.field] as Row[] | undefined) ?? []).map((o) => o.id),
  );

  useEffect(() => {
    listAll<Row>(target.basePath)
      .then((d) => setOptions(d.items))
      .catch(() => setOptions([]));
  }, [target]);

  async function toggle(id: number, on: boolean) {
    const url = `${resource.basePath}/${row.id}/${link.path}/${id}`;
    try {
      if (on) await api.post(url);
      else await api.delete(url);
      setLinked((prev) => (on ? [...prev, id] : prev.filter((x) => x !== id)));
      onSaved();
    } catch (err) {
      toast.error(errorMessage(err, t("err.update")));
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {t(link.labelKey)} · {String(row.username ?? row.name ?? row.id)}
          </DialogTitle>
        </DialogHeader>
        <div className="flex max-h-80 flex-col gap-2 overflow-y-auto">
          {options === null && (
            <p className="text-sm text-muted-foreground">
              {t("common.loading")}
            </p>
          )}
          {options?.map((o) => (
            <label key={o.id} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={linked.includes(o.id)}
                onChange={(e) => toggle(o.id, e.target.checked)}
              />
              {String(o.name)}
            </label>
          ))}
        </div>
        <DialogFooter>
          <Button onClick={onClose}>{t("common.done")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
