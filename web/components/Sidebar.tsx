"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const nav = [
  { href: "/", label: "Dashboard", icon: "▦" },
  { href: "/scan", label: "New Scan", icon: "＋" },
  { href: "/products", label: "Products", icon: "📦" },
  { href: "/violations", label: "Violations", icon: "⚠" },
  { href: "/analytics", label: "Analytics", icon: "📊" },
  { href: "/settings", label: "Settings", icon: "⚙" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  async function logout() {
    const base =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
    const refresh =
      typeof window !== "undefined"
        ? localStorage.getItem("refresh_token")
        : null;
    try {
      if (refresh) {
        await fetch(`${base}/auth/logout`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
        });
      }
    } catch {
      /* revoke is best-effort; clear the session regardless */
    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    router.push("/login");
  }

  return (
    <aside className="flex h-full w-60 flex-col border-r border-slate-200 bg-white">
      <div className="flex items-center gap-2 border-b border-slate-100 px-5 py-4">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-[#1B4FD8] text-white">
          LG
        </div>
        <div>
          <div className="text-sm font-bold text-slate-900">LabelGuard AI</div>
          <div className="text-[10px] uppercase tracking-wide text-slate-400">
            Legal Metrology
          </div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 py-4">
        {nav.map((item) => {
          const active =
            item.href === "/"
              ? pathname === "/"
              : pathname?.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "bg-[#1B4FD8]/10 text-[#1B4FD8]"
                  : "text-slate-600 hover:bg-slate-50"
              }`}
            >
              <span className="w-5 text-center">{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="space-y-3 border-t border-slate-100 p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-200 text-xs font-semibold">
            OK
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-800">
              Officer Sharma
            </div>
            <div className="text-[10px] text-slate-400">OFFICER</div>
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full rounded-md border border-slate-200 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
