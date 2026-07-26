"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import { api, type User } from "@/lib/api";

export type Profile = {
  id: number;
  username: string;
  bio: string;
  phone_number: string;
  avatar: string | null;
};

export type Can = (action: string) => boolean;

const SessionContext = createContext<{
  user: User;
  profile: Profile | null;
  can: Can;
  reloadProfile: () => void;
} | null>(null);

/**
 * Fetches the signed-in user once and hands it to the whole panel. Everything
 * role-dependent reads from here, so there is a single source of truth for
 * "what may this person see".
 */
export function SessionProvider({
  children,
  fallback,
}: {
  children: React.ReactNode;
  fallback: React.ReactNode;
}) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);

  const reloadProfile = useCallback(() => {
    api
      .get<Profile>("/profiles/me")
      .then((res) => setProfile(res.data))
      .catch(() => setProfile(null));
  }, []);

  useEffect(() => {
    api
      .get<User>("/iam/auth/me")
      .then((res) => setUser(res.data))
      .catch(() => router.replace("/"));
    reloadProfile();
  }, [router, reloadProfile]);

  if (!user) return <>{fallback}</>;

  // superusers hold everything; everyone else is exactly their roles' actions
  const can: Can = (action) =>
    user.is_superuser || user.actions.includes(action);

  return (
    <SessionContext.Provider value={{ user, profile, can, reloadProfile }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used inside <SessionProvider>");
  return ctx;
}
