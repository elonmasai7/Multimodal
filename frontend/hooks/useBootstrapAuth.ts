"use client";

import { useEffect } from "react";

import { refreshAuthToken } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

function getTokenExpiry(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1]));
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

async function tryRefresh(refreshToken: string, setSession: ReturnType<typeof useAuthStore>["setSession"], currentState: { userId: string | null; email: string | null }) {
  try {
    const data = await refreshAuthToken(refreshToken);
    if (data.id_token) {
      setSession({
        token: data.id_token,
        refreshToken: data.refresh_token ?? refreshToken,
        userId: currentState.userId,
        email: currentState.email,
      });
      return data.id_token;
    }
  } catch {
    // Refresh failed — leave existing session intact
  }
  return null;
}

export function useBootstrapAuth() {
  const setSession = useAuthStore((s) => s.setSession);
  const store = useAuthStore();

  useEffect(() => {
    const token = window.localStorage.getItem("auth_token");
    const refreshToken = window.localStorage.getItem("refresh_token");
    const userId = window.localStorage.getItem("user_id");
    const email = window.localStorage.getItem("user_email");
    if (!token) return;

    const expiry = getTokenExpiry(token);
    const fiveMinutes = 5 * 60 * 1000;
    const isExpiredOrSoon = expiry !== null && Date.now() >= expiry - fiveMinutes;

    if (isExpiredOrSoon && refreshToken) {
      tryRefresh(refreshToken, setSession, { userId, email });
    } else {
      setSession({ token, refreshToken, userId, email });
    }

    // Proactive refresh: every 50 minutes
    const interval = setInterval(() => {
      const currentRefreshToken = window.localStorage.getItem("refresh_token");
      if (currentRefreshToken) {
        tryRefresh(currentRefreshToken, setSession, {
          userId: window.localStorage.getItem("user_id"),
          email: window.localStorage.getItem("user_email"),
        });
      }
    }, 50 * 60 * 1000);

    return () => clearInterval(interval);
  }, [setSession]);
}
