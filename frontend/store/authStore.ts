"use client";

import { create } from "zustand";

export type AuthState = {
  token: string | null;
  refreshToken: string | null;
  userId: string | null;
  email: string | null;
  setSession: (payload: { token: string; refreshToken: string | null; userId: string | null; email: string | null }) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  refreshToken: null,
  userId: null,
  email: null,
  setSession: ({ token, refreshToken, userId, email }) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("auth_token", token);
      if (refreshToken) window.localStorage.setItem("refresh_token", refreshToken);
      if (userId) window.localStorage.setItem("user_id", userId);
      if (email) window.localStorage.setItem("user_email", email);
    }
    set({ token, refreshToken, userId, email });
  },
  clearSession: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("auth_token");
      window.localStorage.removeItem("refresh_token");
      window.localStorage.removeItem("user_id");
      window.localStorage.removeItem("user_email");
    }
    set({ token: null, refreshToken: null, userId: null, email: null });
  }
}));
