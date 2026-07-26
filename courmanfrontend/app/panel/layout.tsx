"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard } from "lucide-react";

import { resources } from "@/lib/resources";
import { SessionProvider, useSession } from "@/lib/session";
import { UserMenu } from "@/components/user-menu";
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

export default function PanelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { t } = useI18n();

  return (
    <SessionProvider
      fallback={
        <div className="flex flex-1 items-center justify-center">
          <p className="text-sm text-muted-foreground">{t("common.loading")}</p>
        </div>
      }
    >
      <PanelShell>{children}</PanelShell>
    </SessionProvider>
  );
}

function PanelShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { t, locale } = useI18n();
  const { user } = useSession();

  const nav = [
    { href: "/panel", label: t("nav.dashboard"), icon: LayoutDashboard },
    ...resources
      .filter((r) => r.visible(user))
      .map((r) => ({
        href: `/panel/${r.key}`,
        label: t(r.labelKey),
        icon: r.icon,
      })),
  ];

  return (
    <SidebarProvider>
      <Sidebar side={locale === "fa" ? "right" : "left"}>
        <SidebarHeader className="flex-row! items-center gap-2 px-4 py-3">
          <span className="grid size-7 place-items-center rounded-md bg-primary font-heading text-sm font-bold text-primary-foreground">
            C
          </span>
          <span className="font-heading text-lg font-semibold">Courman</span>
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
                        item.href === "/panel"
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
        <SidebarFooter className="border-t p-2">
          <SidebarMenu>
            <SidebarMenuItem>
              <UserMenu />
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
      </Sidebar>
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 items-center gap-2 border-b bg-background/80 px-4 backdrop-blur">
          <SidebarTrigger />
          <span className="text-sm font-medium">
            {nav.find((n) => n.href === pathname)?.label ?? t("nav.admin")}
          </span>
        </header>
        <div className="flex flex-1 flex-col gap-6 bg-muted/30 p-6">
          {children}
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}
