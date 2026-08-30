"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

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

      <div className="border-t border-slate-100 p-4">
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
      </div>
    </aside>
  );
}
