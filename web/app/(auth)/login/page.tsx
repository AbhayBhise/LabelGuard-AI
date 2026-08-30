"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { post } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await post<{ access_token: string; refresh_token: string }>(
        "/auth/login",
        { email, password }
      );
      localStorage.setItem("access_token", res.access_token);
      localStorage.setItem("refresh_token", res.refresh_token);
      router.push("/");
    } catch (err: any) {
      setError(err.message || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen">
      <div className="relative hidden w-1/2 flex-col justify-between bg-[#1B4FD8] p-12 text-white lg:flex">
        <div>
          <div className="text-2xl font-bold">LabelGuard AI</div>
          <div className="mt-1 text-sm text-blue-200">
            Ministry of Consumer Affairs · DoCA
          </div>
        </div>
        <div>
          <h1 className="text-4xl font-bold leading-tight">
            The AI Enforcement Officer
            <br />
            for Every Package in India
          </h1>
          <p className="mt-4 max-w-md text-blue-100">
            Scan any packaged commodity and generate a legally defensible
            compliance report under the Legal Metrology (PC) Rules, 2011 in
            under 10 seconds.
          </p>
        </div>
        <div className="flex gap-3 text-xs">
          {["OFFICER", "SUPERVISOR", "ADMIN", "VIEWER"].map((r) => (
            <span
              key={r}
              className="rounded-md border border-white/20 px-2 py-1"
            >
              {r}
            </span>
          ))}
        </div>
      </div>

      <div className="flex w-full items-center justify-center bg-[#F8FAFC] p-6 lg:w-1/2">
        <form
          onSubmit={handleSubmit}
          className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-8 shadow-sm"
        >
          <h2 className="text-lg font-semibold text-slate-900">
            Sign in to LabelGuard
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Use your enforcement account credentials.
          </p>

          {error && (
            <div className="mt-4 rounded-md bg-danger/10 px-3 py-2 text-sm text-danger">
              {error}
            </div>
          )}

          <div className="mt-6 space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-600">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-[#1B4FD8] focus:outline-none"
                placeholder="officer@labelguard.in"
                required
              />
            </div>
            <div>
              <label className="text-xs font-medium text-slate-600">
                Password
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-[#1B4FD8] focus:outline-none"
                placeholder="••••••••"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mt-6 w-full rounded-md bg-[#1B4FD8] py-2.5 text-sm font-semibold text-white hover:bg-[#1740ad] disabled:opacity-60"
          >
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <p className="mt-4 text-center text-xs text-slate-400">
            Demo: officer@labelguard.in / officer123
          </p>
        </form>
      </div>
    </div>
  );
}
