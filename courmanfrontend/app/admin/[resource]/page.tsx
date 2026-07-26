"use client";

import { useCallback, useEffect, useState } from "react";
import { notFound, useParams } from "next/navigation";
import { Pencil, Plus, Trash2, Link2 } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage, listAll } from "@/lib/api";
import { getResource, type Field, type Resource, type Row } from "@/lib/resources";
import { Button } from "@/components/ui/button";
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
  const resource = getResource(key);
  if (!resource) notFound();
  // key in the route changes => remount, so per-resource state never leaks
  return <ResourceCrud key={key} resource={resource} />;
}

function ResourceCrud({ resource }: { resource: Resource }) {
  const [rows, setRows] = useState<Row[] | null>(null);
  const [editing, setEditing] = useState<Row | "new" | null>(null);
  const [linking, setLinking] = useState<Row | null>(null);

  const load = useCallback(async () => {
    try {
      const { items } = await listAll<Row>(resource.basePath);
      setRows(items);
    } catch (err) {
      toast.error(errorMessage(err, `Could not load ${resource.label.toLowerCase()}`));
      setRows([]);
    }
  }, [resource]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  async function handleDelete(row: Row) {
    if (!confirm(`Delete this ${resource.label.slice(0, -1).toLowerCase()}?`)) return;
    try {
      await api.delete(`${resource.basePath}/${row.id}`);
      toast.success("Deleted");
      load();
    } catch (err) {
      toast.error(errorMessage(err, "Could not delete"));
    }
  }

  return (
    <>
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">{resource.label}</h1>
        <Button onClick={() => setEditing("new")}>
          <Plus /> New
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            {resource.columns.map((c) => (
              <TableHead key={c.label}>{c.label}</TableHead>
            ))}
            <TableHead className="w-0" />
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows === null && (
            <TableRow>
              <TableCell colSpan={resource.columns.length + 1}>Loading…</TableCell>
            </TableRow>
          )}
          {rows?.length === 0 && (
            <TableRow>
              <TableCell colSpan={resource.columns.length + 1}>Nothing here yet.</TableCell>
            </TableRow>
          )}
          {rows?.map((row) => (
            <TableRow key={row.id}>
              {resource.columns.map((c) => (
                <TableCell key={c.label}>{c.render(row)}</TableCell>
              ))}
              <TableCell className="flex justify-end gap-1">
                {resource.link && (
                  <Button
                    variant="ghost"
                    size="icon"
                    title={`Edit ${resource.link.label}`}
                    onClick={() => setLinking(row)}
                  >
                    <Link2 />
                  </Button>
                )}
                <Button variant="ghost" size="icon" title="Edit" onClick={() => setEditing(row)}>
                  <Pencil />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  title="Delete"
                  onClick={() => handleDelete(row)}
                >
                  <Trash2 />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

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
  const fields = row ? resource.updateFields : resource.createFields;
  const [values, setValues] = useState<Record<string, string | boolean>>(() =>
    Object.fromEntries(
      fields.map((f) => [
        f.name,
        f.type === "checkbox" ? Boolean(row?.[f.name] ?? true) : String(row?.[f.name] ?? ""),
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
      toast.success(row ? "Saved" : "Created");
      onSaved();
      onClose();
    } catch (err) {
      toast.error(errorMessage(err, "Could not save"));
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
            {row ? "Edit" : "New"} {resource.label.slice(0, -1).toLowerCase()}
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
                  {f.label}
                </label>
              ) : (
                <>
                  <Label htmlFor={f.name}>{f.label}</Label>
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
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save"}
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
      toast.error(errorMessage(err, "Could not update"));
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {link.label} for {String(row.username ?? row.name ?? row.id)}
          </DialogTitle>
        </DialogHeader>
        <div className="flex max-h-80 flex-col gap-2 overflow-y-auto">
          {options === null && <p className="text-sm text-muted-foreground">Loading…</p>}
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
          <Button onClick={onClose}>Done</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
