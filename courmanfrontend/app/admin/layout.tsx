"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { LayoutDashboard, LogOut } from "lucide-react";

import { api, type User } from "@/lib/api";
import { resources } from "@/lib/resources";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/theme-toggle";
import { LocaleToggle } from "@/components/locale-toggle";
import { useI18n } from "@/lib/i18n";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { t, locale } = useI18n();
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    api
      .get<User>("/iam/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => router.replace("/"));
  }, [router]);

  if (!user) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
      </div>
    );
  }

  const nav = [
    { href: "/admin", label: t("nav.dashboard"), icon: LayoutDashboard },
    ...resources.map((r) => ({ href: `/admin/${r.key}`, label: t(r.labelKey), icon: r.icon })),
  ];

  async function handleLogout() {
    await api.post("/iam/auth/logout");
    router.replace("/");
  }

  return (
    <SidebarProvider>
      <Sidebar side={locale === "fa" ? "right" : "left"}>
        <SidebarHeader className="px-4 py-3 font-heading text-lg font-semibold">
          Courman
        </SidebarHeader>
        <SidebarContent>
          <SidebarGroup>
            <SidebarGroupLabel>{t("nav.manage")}</SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {nav.map((item) => (
                  <SidebarMenuItem key={item.href}>
                    <SidebarMenuButton
                      isActive={
                        item.href === "/admin"
                          ? pathname === item.href
                          : pathname.startsWith(item.href)
                      }
                      render={<Link href={item.href} />}
                    >
                      <item.icon />
                      <span>{item.label}</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarContent>
        <SidebarFooter className="gap-2 p-3">
          <p className="text-xs text-muted-foreground">
            {t("common.signedInAs", { name: user.username })}
          </p>
          <Button variant="outline" size="sm" onClick={handleLogout}>
            <LogOut /> {t("common.logout")}
          </Button>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="flex h-14 items-center gap-2 border-b px-4">
          <SidebarTrigger />
          <span className="text-sm font-medium">
            {nav.find((n) => n.href === pathname)?.label ?? t("nav.admin")}
          </span>
          <div className="ms-auto flex gap-1">
            <LocaleToggle />
            <ThemeToggle />
          </div>
        </header>
        <div className="flex flex-1 flex-col gap-6 p-6">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
