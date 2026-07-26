"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ChevronsUpDown,
  LogOut,
  Settings,
  User as UserIcon,
} from "lucide-react";

import { api } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { useSession } from "@/lib/session";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { SidebarMenuButton } from "@/components/ui/sidebar";

/** The account menu at the foot of the sidebar: profile, settings, sign out. */
export function UserMenu() {
  const router = useRouter();
  const { t } = useI18n();
  const { user, profile } = useSession();

  const roles = user.roles.map((r) => r.name).join(", ");
  const subtitle =
    roles || user.email || (user.is_superuser ? t("user.superuser") : "");

  async function logout() {
    await api.post("/iam/auth/logout");
    router.replace("/");
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <SidebarMenuButton size="lg" className="h-auto py-2">
            <Avatar>
              {profile?.avatar && <AvatarImage src={profile.avatar} alt="" />}
              <AvatarFallback className="text-xs font-semibold uppercase">
                {user.username.slice(0, 2)}
              </AvatarFallback>
            </Avatar>
            <span className="grid min-w-0 flex-1 text-start leading-tight">
              <span className="truncate text-sm font-medium">
                {user.username}
              </span>
              <span className="truncate text-xs text-muted-foreground">
                {subtitle}
              </span>
            </span>
            <ChevronsUpDown className="ms-auto size-4 text-muted-foreground" />
          </SidebarMenuButton>
        }
      />
      <DropdownMenuContent side="top" align="end" className="min-w-56">
        {/* GroupLabel needs a Group ancestor, or base-ui throws on mount */}
        <DropdownMenuGroup>
          <DropdownMenuLabel className="text-muted-foreground">
            {t("common.signedInAs", { name: user.username })}
          </DropdownMenuLabel>
        </DropdownMenuGroup>
        <DropdownMenuSeparator />
        <DropdownMenuItem render={<Link href="/panel/profile" />}>
          <UserIcon /> {t("nav.profile")}
        </DropdownMenuItem>
        <DropdownMenuItem render={<Link href="/panel/settings" />}>
          <Settings /> {t("nav.settings")}
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem variant="destructive" onClick={logout}>
          <LogOut /> {t("common.logout")}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
