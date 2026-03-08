"use client";

import { useEffect } from "react";

import { useAuthStore } from "@/store/authStore";

export function useBootstrapAuth() {
  const setSession = useAuthStore((s) => s.setSession);

  useEffect(() => {
    const token = window.localStorage.getItem("auth_token");
    if (!token) return;
    setSession({
      token,
      refreshToken: window.localStorage.getItem("refresh_token"),
      userId: window.localStorage.getItem("user_id"),
      email: window.localStorage.getItem("user_email")
    });
  }, [setSession]);
}
