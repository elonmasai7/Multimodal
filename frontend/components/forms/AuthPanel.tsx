"use client";

import { useState } from "react";

import { login, signup } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export function AuthPanel() {
  const token = useAuthStore((s) => s.token);
  const email = useAuthStore((s) => s.email);
  const setSession = useAuthStore((s) => s.setSession);
  const clearSession = useAuthStore((s) => s.clearSession);

  const [mode, setMode] = useState<"login" | "signup">("login");
  const [formEmail, setFormEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    setError(null);
    try {
      const auth = mode === "login" ? await login(formEmail, password) : await signup(formEmail, password, displayName);
      setSession({
        token: auth.id_token,
        refreshToken: auth.refresh_token,
        userId: auth.user_id,
        email: auth.email
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    }
  }

  if (token) {
    return (
      <div className="rounded-xl border border-emerald-300/30 bg-emerald-500/10 p-3 text-xs text-emerald-100">
        <p>Signed in as {email ?? "user"}</p>
        <button onClick={clearSession} className="mt-2 rounded-md border border-emerald-200/50 px-2 py-1">
          Sign out
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-2 rounded-xl border border-white/20 bg-slate-900/60 p-3">
      <div className="flex gap-2 text-xs">
        <button className="rounded px-2 py-1 hover:bg-white/10" onClick={() => setMode("login")}>Login</button>
        <button className="rounded px-2 py-1 hover:bg-white/10" onClick={() => setMode("signup")}>Sign up</button>
      </div>
      <input
        className="w-full rounded border border-white/20 bg-transparent px-2 py-1 text-xs"
        placeholder="Email"
        value={formEmail}
        onChange={(e) => setFormEmail(e.target.value)}
      />
      <input
        className="w-full rounded border border-white/20 bg-transparent px-2 py-1 text-xs"
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {mode === "signup" && (
        <input
          className="w-full rounded border border-white/20 bg-transparent px-2 py-1 text-xs"
          placeholder="Display name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
      )}
      {error && <p className="text-xs text-red-300">{error}</p>}
      <button onClick={submit} className="rounded bg-cyan-400 px-2 py-1 text-xs font-semibold text-slate-950">
        {mode === "login" ? "Login" : "Create account"}
      </button>
    </div>
  );
}
