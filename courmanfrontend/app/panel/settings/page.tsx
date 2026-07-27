"use client";

import { Languages, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { toast } from "sonner";

import { ACTIONS, errorMessage } from "@/lib/api";
import { useSession } from "@/lib/session";
import { LOCALES, useI18n, type Locale } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function SettingsPage() {
  const { t, locale, setLocale } = useI18n();
  const { resolvedTheme, setTheme } = useTheme();
  const { can } = useSession();
  const mayChangeLanguage = can(ACTIONS.settingsManage);

  return (
    <>
      <div>
        <h1 className="font-heading text-2xl font-semibold tracking-tight">
          {t("settings.title")}
        </h1>
        <p className="text-sm text-muted-foreground">
          {t("settings.subtitle")}
        </p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sun className="size-4 text-muted-foreground" />
            {t("settings.appearance")}
          </CardTitle>
          <CardDescription>{t("settings.appearanceHint")}</CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {(["light", "dark"] as const).map((option) => (
            <Button
              key={option}
              variant={resolvedTheme === option ? "default" : "outline"}
              size="sm"
              onClick={() => setTheme(option)}
            >
              {option === "light" ? <Sun /> : <Moon />}
              {t(option === "light" ? "settings.light" : "settings.dark")}
            </Button>
          ))}
        </CardContent>
      </Card>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Languages className="size-4 text-muted-foreground" />
            {t("settings.language")}
          </CardTitle>
          <CardDescription>
            {t(
              mayChangeLanguage
                ? "settings.languageHint"
                : "settings.languageLocked",
            )}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex gap-2">
          {(Object.keys(LOCALES) as Locale[]).map((option) => (
            <Button
              key={option}
              variant={locale === option ? "default" : "outline"}
              size="sm"
              disabled={!mayChangeLanguage}
              onClick={() =>
                setLocale(option).catch((err) =>
                  toast.error(errorMessage(err, t("err.save"))),
                )
              }
            >
              {LOCALES[option]}
            </Button>
          ))}
        </CardContent>
      </Card>
    </>
  );
}
