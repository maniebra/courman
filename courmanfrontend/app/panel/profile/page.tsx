"use client";

import { useRef, useState } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";

import { api, errorMessage } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function ProfilePage() {
  const { t } = useI18n();
  const { user, profile, reloadProfile } = useSession();
  const fileInput = useRef<HTMLInputElement>(null);
  const [bio, setBio] = useState(profile?.bio ?? "");
  const [phone, setPhone] = useState(profile?.phone_number ?? "");
  const [saving, setSaving] = useState(false);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.patch("/profiles/me", { bio, phone_number: phone });
      reloadProfile();
      toast.success(t("common.saved"));
    } catch (err) {
      toast.error(errorMessage(err, t("profile.saveError")));
    } finally {
      setSaving(false);
    }
  }

  async function upload(file: File) {
    const body = new FormData();
    body.append("avatar", file);
    try {
      await api.post("/profiles/me/avatar", body);
      reloadProfile();
    } catch (err) {
      toast.error(errorMessage(err, t("profile.avatarError")));
    }
  }

  return (
    <>
      <div>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          {t("profile.title")}
        </h1>
        <p className="text-sm text-muted-foreground">{t("profile.subtitle")}</p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader className="flex! flex-row items-center gap-4">
          <Avatar size="lg" className="size-16">
            {profile?.avatar && <AvatarImage src={profile.avatar} alt="" />}
            <AvatarFallback className="text-lg font-semibold uppercase">
              {user.username.slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <div className="flex flex-col gap-1">
            <CardTitle className="text-lg">{user.username}</CardTitle>
            <CardDescription className="flex flex-wrap items-center gap-1">
              {user.email || "—"}
              {user.roles.map((role) => (
                <Badge key={role.id} variant="secondary">
                  {role.name}
                </Badge>
              ))}
            </CardDescription>
            <div>
              <Button
                variant="outline"
                size="sm"
                className="mt-1"
                onClick={() => fileInput.current?.click()}
              >
                <Upload /> {t("profile.changeAvatar")}
              </Button>
              <input
                ref={fileInput}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) upload(file);
                  e.target.value = "";
                }}
              />
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <form className="flex flex-col gap-4" onSubmit={save}>
            <div className="flex flex-col gap-2">
              <Label htmlFor="bio">{t("profile.bio")}</Label>
              <Textarea
                id="bio"
                rows={4}
                value={bio}
                onChange={(e) => setBio(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="phone">{t("profile.phone")}</Label>
              <Input
                id="phone"
                inputMode="tel"
                className="max-w-xs"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
            <div className="flex justify-end">
              <Button type="submit" disabled={saving}>
                {saving ? t("common.saving") : t("common.save")}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </>
  );
}
