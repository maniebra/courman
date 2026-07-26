"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

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
  setLocale: (l: Locale) => void;
  t: T;
}>({
  locale: "en",
  setLocale: () => {},
  t: (key) => en[key],
});

const STORAGE_KEY = "courman.locale";
export const dirOf = (locale: Locale) => (locale === "fa" ? "rtl" : "ltr");

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    // localStorage is only readable after hydration, so reading it in an effect is
    // what keeps the SSR markup stable.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (saved === "fa" || saved === "en") setLocaleState(saved);
  }, []);

  useEffect(() => {
    document.documentElement.lang = locale;
    document.documentElement.dir = dirOf(locale);
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    localStorage.setItem(STORAGE_KEY, l);
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
