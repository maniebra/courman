"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CalendarPlus,
  Eye,
  EyeOff,
  Link2,
  Pencil,
  Plus,
  Trash2,
  X,
} from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type Brief = { id: number; username: string };
type Slot = {
  id: number;
  start: string;
  end: string;
  ta: Brief;
  group: { id: number; number: number } | null;
  booked_by: { student_id: string } | null;
};
type Item = {
  id: number;
  title: string;
  description: string;
  group_type: number;
  signup_token: string | null;
  hide_ta: boolean;
  slot_minutes: number;
  break_minutes: number;
  slots: Slot[];
};
type GroupType = { id: number; title: string };

export function Handoffs({
  courseId,
  types,
  staff,
  canAssignTa,
  editable,
}: {
  courseId: number;
  /** handoffs hang off a group type, since a booking belongs to the whole team */
  types: GroupType[];
  /** professors, head TAs and TAs of this course: who a slot may be offered for */
  staff: Brief[];
  canAssignTa: boolean;
  editable: boolean;
}) {
  const { t } = useI18n();
  const [items, setItems] = useState<Item[] | null>(null);
  const [editing, setEditing] = useState<Item | "new" | null>(null);
  const [offering, setOffering] = useState<Item | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await api.get<Item[]>(`/courses/${courseId}/handoffs`);
      setItems(res.data);
    } catch (err) {
      toast.error(errorMessage(err, t("handoff.loadError")));
      setItems([]);
    }
  }, [courseId, t]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- setState happens after await
    load();
  }, [load]);

  async function call(fn: () => Promise<unknown>) {
    try {
      await fn();
      await load();
    } catch (err) {
      toast.error(errorMessage(err, t("handoff.error")));
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{t("handoff.title")}</CardTitle>
        <CardDescription>{t("handoff.hint")}</CardDescription>
        {editable && types.length > 0 && (
          <CardAction>
            <Button size="sm" onClick={() => setEditing("new")}>
              <Plus /> {t("common.new")}
            </Button>
          </CardAction>
        )}
      </CardHeader>
      <CardContent className="flex flex-col gap-6">
        {types.length === 0 && (
          <p className="text-sm text-muted-foreground">
            {t("handoff.needsType")}
          </p>
        )}
        {items?.length === 0 && types.length > 0 && (
          <p className="text-sm text-muted-foreground">
            {t("common.nothingHere")}
          </p>
        )}
        {items?.map((item) => (
          <HandoffCard
            key={item.id}
            courseId={courseId}
            item={item}
            typeTitle={
              types.find((type) => type.id === item.group_type)?.title ?? ""
            }
            editable={editable}
            onOffer={() => setOffering(item)}
            onEdit={() => setEditing(item)}
            call={call}
          />
        ))}
      </CardContent>

      {editing && (
        <ItemDialog
          courseId={courseId}
          item={editing === "new" ? null : editing}
          types={types}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            load();
          }}
        />
      )}

      {offering && (
        <AvailabilityDialog
          courseId={courseId}
          item={offering}
          staff={canAssignTa ? staff : []}
          onClose={() => setOffering(null)}
          onSaved={() => {
            setOffering(null);
            load();
          }}
        />
      )}
    </Card>
  );
}

function HandoffCard({
  courseId,
  item,
  typeTitle,
  editable,
  onOffer,
  onEdit,
  call,
}: {
  courseId: number;
  item: Item;
  typeTitle: string;
  editable: boolean;
  onOffer: () => void;
  onEdit: () => void;
  call: (fn: () => Promise<unknown>) => void;
}) {
  const { t, locale } = useI18n();
  const free = item.slots.filter((slot) => !slot.group).length;

  // one heading per day keeps a week of 20 minute slots readable
  const days = new Map<string, Slot[]>();
  for (const slot of item.slots) {
    const day = new Date(slot.start).toLocaleDateString(locale, {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
    days.set(day, [...(days.get(day) ?? []), slot]);
  }

  const time = (value: string) =>
    new Date(value).toLocaleTimeString(locale, { timeStyle: "short" });

  return (
    <section className="flex flex-col gap-4 rounded-lg border p-4">
      <div className="flex flex-col gap-2">
        <h3 className="font-medium">{item.title}</h3>
        <div className="flex flex-wrap items-center gap-1.5">
          <Badge variant="secondary">{typeTitle}</Badge>
          <Badge variant="outline">
            {t("handoff.slotLength", { minutes: item.slot_minutes })}
          </Badge>
          {item.break_minutes > 0 && (
            <Badge variant="outline">
              {t("handoff.restLength", { minutes: item.break_minutes })}
            </Badge>
          )}
          <span className="text-sm text-muted-foreground">
            {t("handoff.slotCount", { count: item.slots.length, free })}
          </span>
        </div>
        {item.description && (
          <p className="text-sm text-muted-foreground">{item.description}</p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button size="sm" variant="outline" onClick={onOffer}>
          <CalendarPlus /> {t("handoff.addAvailability")}
        </Button>
        {editable && (
          <>
            <Button
              size="sm"
              variant={item.signup_token ? "secondary" : "outline"}
              onClick={() =>
                call(() =>
                  api.patch(`/courses/${courseId}/handoffs/${item.id}`, {
                    signup_open: !item.signup_token,
                  }),
                )
              }
            >
              <Link2 />
              {item.signup_token ? t("signup.close") : t("signup.open")}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              title={t("handoff.hideTaHint")}
              onClick={() =>
                call(() =>
                  api.patch(`/courses/${courseId}/handoffs/${item.id}`, {
                    hide_ta: !item.hide_ta,
                  }),
                )
              }
            >
              {item.hide_ta ? <EyeOff /> : <Eye />}
              {item.hide_ta ? t("handoff.taHidden") : t("handoff.taShown")}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              title={t("common.edit")}
              onClick={onEdit}
            >
              <Pencil />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              title={t("common.delete")}
              onClick={() => {
                if (!confirm(t("common.deleteConfirm", { item: item.title })))
                  return;
                call(() =>
                  api.delete(`/courses/${courseId}/handoffs/${item.id}`),
                );
              }}
            >
              <Trash2 />
            </Button>
            {item.signup_token && (
              <button
                type="button"
                className="flex items-center gap-1 text-sm text-primary underline-offset-4 hover:underline"
                onClick={() => {
                  navigator.clipboard.writeText(
                    `${location.origin}/handoffs/${item.signup_token}`,
                  );
                  toast.success(t("signup.copied"));
                }}
              >
                <Link2 className="size-4" /> {t("signup.copyLink")}
              </button>
            )}
          </>
        )}
      </div>

      {item.slots.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t("handoff.noSlots")}</p>
      ) : (
        // a column per day, slots down it in time order: a schedule, not a chip wall
        <div className="overflow-x-auto">
          <div className="flex gap-3">
            {[...days].map(([day, slots]) => (
              <div key={day} className="flex w-52 shrink-0 flex-col gap-2">
                <p className="text-sm font-medium">{day}</p>
                {slots.map((slot) => (
                  <div
                    key={slot.id}
                    className={cn(
                      "group/slot flex flex-col gap-0.5 rounded-md border px-2 py-1.5 text-sm",
                      slot.group
                        ? "border-primary/40 bg-primary/10"
                        : "bg-muted/40",
                    )}
                  >
                    <div className="flex items-center gap-2">
                      <span className="flex-1 tabular-nums">
                        <bdi>
                          {time(slot.start)}–{time(slot.end)}
                        </bdi>
                      </span>
                      <button
                        type="button"
                        aria-label={t("common.delete")}
                        className="text-muted-foreground opacity-0 transition-opacity group-hover/slot:opacity-100 focus-visible:opacity-100 hover:text-destructive"
                        onClick={() =>
                          call(() =>
                            api.delete(
                              `/courses/${courseId}/handoff-slots/${slot.id}`,
                            ),
                          )
                        }
                      >
                        <Trash2 className="size-3.5" />
                      </button>
                    </div>
                    <div className="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                      <span>{slot.ta.username}</span>
                      {slot.group ? (
                        <span className="flex items-center gap-1 font-medium text-foreground">
                          #{slot.group.number}
                          {slot.booked_by && ` · ${slot.booked_by.student_id}`}
                          {editable && (
                            <button
                              type="button"
                              title={t("handoff.clearBooking")}
                              aria-label={t("handoff.clearBooking")}
                              className="text-muted-foreground hover:text-destructive"
                              onClick={() => {
                                if (!confirm(t("handoff.clearConfirm"))) return;
                                call(() =>
                                  api.delete(
                                    `/courses/${courseId}/handoff-slots/${slot.id}/booking`,
                                  ),
                                );
                              }}
                            >
                              <X className="size-3.5" />
                            </button>
                          )}
                        </span>
                      ) : (
                        <span>{t("handoff.free")}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

/** A TA offers a window; the API slices it into slots of the item's length. */
function AvailabilityDialog({
  courseId,
  item,
  staff,
  onClose,
  onSaved,
}: {
  courseId: number;
  item: Item;
  staff: Brief[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  // a day plus two clock times beats two datetime pickers: same window, three taps
  const [day, setDay] = useState(() => new Date().toISOString().slice(0, 10));
  const [from, setFrom] = useState("09:00");
  const [to, setTo] = useState("12:00");
  const [ta, setTa] = useState("");
  const [saving, setSaving] = useState(false);

  const step = item.slot_minutes + item.break_minutes;
  const minutes =
    (new Date(`${day}T${to}`).getTime() - new Date(`${day}T${from}`).getTime()) /
    60000;
  const willMake =
    minutes >= item.slot_minutes
      ? Math.floor((minutes - item.slot_minutes) / step) + 1
      : 0;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post(`/courses/${courseId}/handoffs/${item.id}/slots`, {
        start: new Date(`${day}T${from}`).toISOString(),
        end: new Date(`${day}T${to}`).toISOString(),
        ta: ta ? Number(ta) : null,
      });
      onSaved();
    } catch (err) {
      toast.error(errorMessage(err, t("handoff.error")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t("handoff.addAvailability")}</DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={submit}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="slot-day">{t("handoff.day")}</Label>
            <Input
              id="slot-day"
              type="date"
              value={day}
              onChange={(e) => setDay(e.target.value)}
              required
            />
          </div>

          <div className="flex gap-4">
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="slot-from">{t("handoff.from")}</Label>
              <Input
                id="slot-from"
                type="time"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="slot-to">{t("handoff.to")}</Label>
              <Input
                id="slot-to"
                type="time"
                value={to}
                onChange={(e) => setTo(e.target.value)}
                required
              />
            </div>
          </div>

          {staff.length > 0 && (
            <div className="flex flex-col gap-2">
              <Label htmlFor="slot-ta">{t("handoff.ta")}</Label>
              <select
                id="slot-ta"
                className="h-9 rounded-md border bg-transparent px-2 text-sm"
                value={ta}
                onChange={(e) => setTa(e.target.value)}
              >
                <option value="">{t("handoff.myself")}</option>
                {staff.map((member) => (
                  <option key={member.id} value={member.id}>
                    {member.username}
                  </option>
                ))}
              </select>
            </div>
          )}

          <p className="text-sm text-muted-foreground">
            {willMake > 0
              ? t("handoff.willMake", {
                  count: willMake,
                  minutes: item.slot_minutes,
                  rest: item.break_minutes,
                })
              : t("handoff.tooShort", { minutes: item.slot_minutes })}
          </p>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              {t("common.cancel")}
            </Button>
            <Button type="submit" disabled={saving || willMake === 0}>
              {saving ? t("common.saving") : t("common.add")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

function ItemDialog({
  courseId,
  item,
  types,
  onClose,
  onSaved,
}: {
  courseId: number;
  item: Item | null;
  types: GroupType[];
  onClose: () => void;
  onSaved: () => void;
}) {
  const { t } = useI18n();
  const [title, setTitle] = useState(item?.title ?? "");
  const [description, setDescription] = useState(item?.description ?? "");
  const [groupType, setGroupType] = useState(
    String(item?.group_type ?? types[0]?.id ?? ""),
  );
  const [slotMinutes, setSlotMinutes] = useState(
    String(item?.slot_minutes ?? 20),
  );
  const [breakMinutes, setBreakMinutes] = useState(
    String(item?.break_minutes ?? 0),
  );
  const [saving, setSaving] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const body = {
      title,
      description,
      slot_minutes: Number(slotMinutes),
      break_minutes: Number(breakMinutes),
    };
    setSaving(true);
    try {
      if (item) await api.patch(`/courses/${courseId}/handoffs/${item.id}`, body);
      else
        await api.post(`/courses/${courseId}/handoffs`, {
          ...body,
          group_type: Number(groupType),
        });
      onSaved();
    } catch (err) {
      toast.error(errorMessage(err, t("handoff.error")));
    } finally {
      setSaving(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {t(item ? "common.editTitle" : "common.newTitle", {
              item: t("handoff.item"),
            })}
          </DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={submit}>
          <div className="flex flex-col gap-2">
            <Label htmlFor="handoff-title">{t("field.name")}</Label>
            <Input
              id="handoff-title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>

          {/* the group type is what the bookings hang off, so it is fixed once set */}
          {!item && (
            <div className="flex flex-col gap-2">
              <Label htmlFor="handoff-type">{t("handoff.groupType")}</Label>
              <select
                id="handoff-type"
                className="h-9 rounded-md border bg-transparent px-2 text-sm"
                value={groupType}
                onChange={(e) => setGroupType(e.target.value)}
              >
                {types.map((type) => (
                  <option key={type.id} value={type.id}>
                    {type.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-4">
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="handoff-minutes">{t("handoff.slotField")}</Label>
              <Input
                id="handoff-minutes"
                type="number"
                min={1}
                value={slotMinutes}
                onChange={(e) => setSlotMinutes(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-1 flex-col gap-2">
              <Label htmlFor="handoff-break">{t("handoff.restField")}</Label>
              <Input
                id="handoff-break"
                type="number"
                min={0}
                value={breakMinutes}
                onChange={(e) => setBreakMinutes(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Label htmlFor="handoff-description">
              {t("field.description")}
            </Label>
            <Textarea
              id="handoff-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

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
