"use client";

import { Languages } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";

export function LocaleToggle() {
  const { locale, setLocale, t } = useI18n();

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label={t("common.language")}
      title={t("common.language")}
      onClick={() => setLocale(locale === "fa" ? "en" : "fa")}
    >
      <Languages />
    </Button>
  );
}
