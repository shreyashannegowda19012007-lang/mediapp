import { create } from "zustand";
import { api, UserSession } from "@/lib/api";

export type RoleType = "customer" | "pharmacy" | "delivery" | "admin";

interface AuthState {
  user: UserSession | null;
  activeRole: RoleType;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchSession: () => Promise<void>;
  switchRole: (role: RoleType) => Promise<void>;
  setActiveRole: (role: RoleType) => void;
  login: (email: string, password?: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  activeRole: "customer",
  isLoading: false,
  error: null,

  fetchSession: async () => {
    try {
      set({ isLoading: true, error: null });
      const res = await api.auth.getSession();
      if (res.authenticated && res.user) {
        set({ user: res.user, activeRole: res.user.role });
      } else {
        set({ user: null });
      }
    } catch {
      // Keep state as is on network blip
    } finally {
      set({ isLoading: false });
    }
  },

  switchRole: async (role: RoleType) => {
    try {
      set({ isLoading: true, activeRole: role, error: null });
      if (get().user) {
        try {
          await api.auth.switchRole(role);
          await get().fetchSession();
        } catch {
          // Ignore if switch-role not permitted on current identity
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to switch role";
      set({ error: msg });
    } finally {
      set({ isLoading: false });
    }
  },

  setActiveRole: (role: RoleType) => {
    set({ activeRole: role });
  },

  login: async (email: string, password?: string) => {
    try {
      set({ isLoading: true, error: null });
      const res = await api.auth.login({ email, password });
      if (res.user) {
        set({ user: res.user, activeRole: res.user.role });
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Login failed";
      set({ error: msg });
      throw err;
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    try {
      await api.auth.logout();
      set({ user: null, activeRole: "customer" });
    } catch (err) {
      console.error(err);
    }
  },
}));
