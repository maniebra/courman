"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

export const LOCALES = { en: "English", fa: "فارسی" } as const;
export type Locale = keyof typeof LOCALES;

const en = {
  "nav.dashboard": "Dashboard",
  "nav.manage": "Manage",
  "nav.admin": "Admin",
  "nav.profile": "Profile",
  "nav.settings": "Settings",

  "user.staff": "staff",

  "profile.title": "Your profile",
  "profile.subtitle": "How you show up to the rest of the course staff.",
  "profile.bio": "Bio",
  "profile.phone": "Phone number",
  "profile.avatar": "Avatar",
  "profile.changeAvatar": "Change photo",
  "profile.avatarError": "Could not upload the photo",
  "profile.saveError": "Could not save your profile",

  "settings.title": "Settings",
  "settings.subtitle": "Preferences stored in this browser.",
  "settings.appearance": "Appearance",
  "settings.appearanceHint": "Switch between light and dark.",
  "settings.light": "Light",
  "settings.dark": "Dark",
  "settings.language": "Language",
  "settings.languageHint": "Persian switches the whole panel to right-to-left.",

  "res.users": "Users",
  "res.user": "user",
  "res.roles": "Roles",
  "res.role": "role",
  "res.actions": "Actions",
  "res.action": "action",
  "res.courses": "Courses",
  "res.course": "course",

  "field.username": "Username",
  "field.password": "Password",
  "field.name": "Name",
  "field.firstName": "First name",
  "field.lastName": "Last name",
  "field.email": "Email",
  "field.active": "Active",
  "field.roles": "Roles",
  "field.actions": "Actions",
  "field.code": "Code",
  "field.semester": "Semester",
  "field.description": "Description",
  "field.staff": "Staff",
  "field.weight": "Weight",

  "list.count": "{count} records",
  "dash.subtitle": "Everything you can manage, at a glance.",

  "common.new": "New",
  "common.edit": "Edit",
  "common.delete": "Delete",
  "common.manage": "Manage",
  "common.save": "Save",
  "common.saving": "Saving…",
  "common.cancel": "Cancel",
  "common.done": "Done",
  "common.add": "Add",
  "common.loading": "Loading…",
  "common.none": "None.",
  "common.nothingHere": "Nothing here yet.",
  "common.yes": "yes",
  "common.no": "no",
  "common.empty": "—",
  "common.deleteConfirm": "Delete this {item}?",
  "common.deleted": "Deleted",
  "common.created": "Created",
  "common.saved": "Saved",
  "common.editTitle": "Edit {item}",
  "common.newTitle": "New {item}",
  "common.language": "Language",
  "common.theme": "Toggle theme",
  "common.logout": "Log out",
  "common.signedInAs": "Signed in as {name}",

  "err.load": "Could not load {item}",
  "err.save": "Could not save",
  "err.delete": "Could not delete",
  "err.update": "Could not update",

  "login.title": "Sign in to Courman",
  "login.desc": "Use your account credentials to continue.",
  "login.submit": "Sign in",
  "login.submitting": "Signing in…",
  "login.invalid": "Invalid username or password",

  "course.professors": "Professors",
  "course.headTas": "Head TAs",
  "course.tas": "TAs",
  "course.assigned": "{count} assigned",
  "course.addUser": "Add user…",
  "course.staffError": "Could not update staff",
  "course.notFound": "Could not load course",

  "course.students": "Students",
  "course.studentId": "Student ID",
  "course.studentName": "Name (optional)",
  "course.addStudentError": "Could not add the student",
  "course.removeStudentError": "Could not remove the student",

  "sheet.title": "Grading sheet",
  "sheet.none": "No grading sheet yet.",
  "sheet.create": "Create sheet",
  "sheet.open": "Open sheet",
  "sheet.titlePlaceholder": "Sheet title",
  "sheet.deleteConfirm": "Delete this sheet and every score on it?",
  "sheet.student": "Student",
  "sheet.total": "Total",
  "sheet.noStudents": "No students enrolled in this course yet.",
  "sheet.noSubgrades": "Add a sub-grade to start scoring.",
  "sheet.subgradeName": "Sub-grade name",
  "sheet.maxScore": "Max",
  "sheet.readOnly": "You can view this sheet but not change it.",
  "sheet.hint": "Arrow keys, Enter and Tab move between cells. Paste a block from Excel to fill many at once.",
  "sheet.comment": "Comment",
  "sheet.commentFor": "Comment on {part} for {student}",
  "sheet.commentPlaceholder": "What did they get wrong?",
  "sheet.commentError": "Could not save the comment",
  "sheet.clearComment": "Clear",
  "sheet.commentHint": "Ctrl + Enter to save",
  "sheet.createError": "Could not create the sheet",
  "sheet.deleteError": "Could not delete the sheet",
  "sheet.loadError": "Could not load the sheet",
  "sheet.subgradeError": "Could not save the sub-grade",
  "sheet.scoreError": "Could not save the score",

  "grading.title": "Grading components",
  "grading.total": "Weights total {total}%",
  "grading.notHundred": " — does not add up to 100%",
  "grading.noComponents": "No components yet.",
  "grading.componentName": "Component name",
  "grading.weight": "Weight %",
  "grading.deleteConfirm": "Delete this component and its tasks?",
  "grading.addError": "Could not add component",
  "grading.deleteError": "Could not delete component",
  "grading.loadError": "Could not load grading components",
  "grading.graders": "Graders",
  "grading.assign": "Assign",
  "grading.assignPlaceholder": "Assign grader…",
  "grading.assignError": "Could not assign grader",
  "grading.removeError": "Could not remove grader",
  "grading.tasksError": "Could not load grading tasks",
};

export type Key = keyof typeof en;

const fa: Record<Key, string> = {
  "nav.dashboard": "داشبورد",
  "nav.manage": "مدیریت",
  "nav.admin": "مدیریت",
  "nav.profile": "نمایه",
  "nav.settings": "تنظیمات",

  "user.staff": "کارمند",

  "profile.title": "نمایهٔ شما",
  "profile.subtitle": "چیزی که بقیهٔ کادر درس از شما می‌بینند.",
  "profile.bio": "درباره",
  "profile.phone": "شمارهٔ تماس",
  "profile.avatar": "تصویر",
  "profile.changeAvatar": "تغییر تصویر",
  "profile.avatarError": "بارگذاری تصویر ممکن نشد",
  "profile.saveError": "ذخیرهٔ نمایه ممکن نشد",

  "settings.title": "تنظیمات",
  "settings.subtitle": "تنظیم‌هایی که در همین مرورگر ذخیره می‌شوند.",
  "settings.appearance": "ظاهر",
  "settings.appearanceHint": "میان پوستهٔ روشن و تیره جابه‌جا شوید.",
  "settings.light": "روشن",
  "settings.dark": "تیره",
  "settings.language": "زبان",
  "settings.languageHint": "با انتخاب فارسی کل پنل راست‌به‌چپ می‌شود.",

  "res.users": "کاربران",
  "res.user": "کاربر",
  "res.roles": "نقش‌ها",
  "res.role": "نقش",
  "res.actions": "دسترسی‌ها",
  "res.action": "دسترسی",
  "res.courses": "درس‌ها",
  "res.course": "درس",

  "field.username": "نام کاربری",
  "field.password": "گذرواژه",
  "field.name": "نام",
  "field.firstName": "نام",
  "field.lastName": "نام خانوادگی",
  "field.email": "ایمیل",
  "field.active": "فعال",
  "field.roles": "نقش‌ها",
  "field.actions": "دسترسی‌ها",
  "field.code": "کد",
  "field.semester": "نیم‌سال",
  "field.description": "توضیحات",
  "field.staff": "کادر درس",
  "field.weight": "وزن",

  "list.count": "{count} مورد",
  "dash.subtitle": "هرچه می‌توانید مدیریت کنید، در یک نگاه.",

  "common.new": "جدید",
  "common.edit": "ویرایش",
  "common.delete": "حذف",
  "common.manage": "مدیریت",
  "common.save": "ذخیره",
  "common.saving": "در حال ذخیره…",
  "common.cancel": "انصراف",
  "common.done": "تمام",
  "common.add": "افزودن",
  "common.loading": "در حال بارگذاری…",
  "common.none": "هیچ‌کدام.",
  "common.nothingHere": "هنوز چیزی ثبت نشده است.",
  "common.yes": "بله",
  "common.no": "خیر",
  "common.empty": "—",
  "common.deleteConfirm": "این {item} حذف شود؟",
  "common.deleted": "حذف شد",
  "common.created": "ایجاد شد",
  "common.saved": "ذخیره شد",
  "common.editTitle": "ویرایش {item}",
  "common.newTitle": "{item} جدید",
  "common.language": "زبان",
  "common.theme": "تغییر پوسته",
  "common.logout": "خروج",
  "common.signedInAs": "وارد شده به عنوان {name}",

  "err.load": "بارگذاری {item} ممکن نشد",
  "err.save": "ذخیره ممکن نشد",
  "err.delete": "حذف ممکن نشد",
  "err.update": "به‌روزرسانی ممکن نشد",

  "login.title": "ورود به کورمن",
  "login.desc": "برای ادامه با حساب کاربری خود وارد شوید.",
  "login.submit": "ورود",
  "login.submitting": "در حال ورود…",
  "login.invalid": "نام کاربری یا گذرواژه نادرست است",

  "course.professors": "استادان",
  "course.headTas": "سرحل‌تمرین‌ها",
  "course.tas": "حل‌تمرین‌ها",
  "course.assigned": "{count} نفر",
  "course.addUser": "افزودن کاربر…",
  "course.staffError": "به‌روزرسانی کادر درس ممکن نشد",
  "course.notFound": "بارگذاری درس ممکن نشد",

  "course.students": "دانشجویان",
  "course.studentId": "شمارهٔ دانشجویی",
  "course.studentName": "نام (اختیاری)",
  "course.addStudentError": "افزودن دانشجو ممکن نشد",
  "course.removeStudentError": "حذف دانشجو ممکن نشد",

  "sheet.title": "کاربرگ نمره",
  "sheet.none": "هنوز کاربرگی ساخته نشده است.",
  "sheet.create": "ساخت کاربرگ",
  "sheet.open": "باز کردن کاربرگ",
  "sheet.titlePlaceholder": "عنوان کاربرگ",
  "sheet.deleteConfirm": "این کاربرگ و همهٔ نمره‌های آن حذف شود؟",
  "sheet.student": "دانشجو",
  "sheet.total": "جمع",
  "sheet.noStudents": "هنوز دانشجویی در این درس ثبت نشده است.",
  "sheet.noSubgrades": "برای شروع نمره‌دهی یک زیرنمره اضافه کنید.",
  "sheet.subgradeName": "نام زیرنمره",
  "sheet.maxScore": "سقف",
  "sheet.readOnly": "شما فقط می‌توانید این کاربرگ را ببینید.",
  "sheet.hint": "با کلیدهای جهت، Enter و Tab بین خانه‌ها جابه‌جا شوید. برای پر کردن گروهی، یک بلوک را از اکسل بچسبانید.",
  "sheet.comment": "توضیح",
  "sheet.commentFor": "توضیح {part} برای {student}",
  "sheet.commentPlaceholder": "اشکال کار کجا بود؟",
  "sheet.commentError": "ذخیرهٔ توضیح ممکن نشد",
  "sheet.clearComment": "پاک کردن",
  "sheet.commentHint": "برای ذخیره Ctrl + Enter بزنید",
  "sheet.createError": "ساخت کاربرگ ممکن نشد",
  "sheet.deleteError": "حذف کاربرگ ممکن نشد",
  "sheet.loadError": "بارگذاری کاربرگ ممکن نشد",
  "sheet.subgradeError": "ذخیرهٔ زیرنمره ممکن نشد",
  "sheet.scoreError": "ذخیرهٔ نمره ممکن نشد",

  "grading.title": "بخش‌های نمره",
  "grading.total": "مجموع وزن‌ها {total}٪",
  "grading.notHundred": " — مجموع ۱۰۰٪ نیست",
  "grading.noComponents": "هنوز بخشی ثبت نشده است.",
  "grading.componentName": "نام بخش",
  "grading.weight": "وزن ٪",
  "grading.deleteConfirm": "این بخش و وظایف آن حذف شود؟",
  "grading.addError": "افزودن بخش ممکن نشد",
  "grading.deleteError": "حذف بخش ممکن نشد",
  "grading.loadError": "بارگذاری بخش‌های نمره ممکن نشد",
  "grading.graders": "مصححان",
  "grading.assign": "تخصیص",
  "grading.assignPlaceholder": "تخصیص مصحح…",
  "grading.assignError": "تخصیص مصحح ممکن نشد",
  "grading.removeError": "حذف مصحح ممکن نشد",
  "grading.tasksError": "بارگذاری وظایف تصحیح ممکن نشد",
};

const dicts = { en, fa };

export type T = (key: Key, vars?: Record<string, string | number>) => string;

const I18nContext = createContext<{ locale: Locale; setLocale: (l: Locale) => void; t: T }>({
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
    <I18nContext.Provider value={{ locale, setLocale, t }}>{children}</I18nContext.Provider>
  );
}

export const useI18n = () => useContext(I18nContext);
