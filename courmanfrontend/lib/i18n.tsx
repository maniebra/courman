"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

import { api } from "@/lib/api";
import en from "@/locales/en.json";
import faStrings from "@/locales/fa.json";

export const LOCALES = { en: "English", fa: "فارسی" } as const;
export type Locale = keyof typeof LOCALES;

export type Key = keyof typeof en;

/** Typed as a full record, so a key missing from fa.json is a build error. */
const fa: Record<Key, string> = faStrings;

const dicts = { en, fa };

export type T = (key: Key, vars?: Record<string, string | number>) => string;

const I18nContext = createContext<{
  locale: Locale;
  setLocale: (l: Locale) => Promise<void>;
  t: T;
}>({
  locale: "en",
  setLocale: async () => {},
  t: (key) => en[key],
});

export const dirOf = (locale: Locale) => (locale === "fa" ? "rtl" : "ltr");

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    // The language is app-wide and admin-controlled, so it comes from the API
    // (unauthenticated) rather than from this browser.
    api
      .get<{ language: Locale }>("/iam/settings/")
      // eslint-disable-next-line react-hooks/set-state-in-effect
      .then((res) => setLocaleState(res.data.language))
      .catch(() => {});
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dirOf(locale);
  }, [locale]);

  /** Changes it for everyone; the API rejects callers without settings.manage. */
  const setLocale = useCallback(async (l: Locale) => {
    await api.put("/iam/settings/", { language: l });
    setLocaleState(l);
  }, []);

  const t = useCallback<T>(
    (key, vars) =>
      Object.entries(vars ?? {}).reduce<string>(
        (out, [k, v]) => out.replaceAll(`{${k}}`, String(v)),
        dicts[locale][key] ?? en[key],
      ),
    [locale],
  );

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
