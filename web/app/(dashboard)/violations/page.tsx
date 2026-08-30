"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import RuleBadge from "@/components/RuleBadge";
import { get } from "@/lib/api";

type Row = {
  id: string;
  rule_id: string;
  rule_title: string | null;
  severity: "CRITICAL" | "MAJOR" | "MINOR";
  violation_type: string;
  finding: string | null;
  found_value: string | null;
  scan_id: string;
  scanned_at: string | null;
  product_name: string | null;
};

const severities = ["", "CRITICAL", "MAJOR", "MINOR"];

export default function ViolationsPage() {
  const [items, setItems] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const [severity, setSeverity] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const qs = severity ? `?severity=${severity}` : "";
    get<{ items: Row[]; total: number }>(`/violations${qs}`)
      .then((r) => {
        setItems(r.items || []);
        setTotal(r.total || 0);
      })
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, [severity]);

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Violations</h1>
          <p className="text-sm text-slate-500">
            All compliance violations detected across scans
            {total ? ` · ${total} total` : ""}
          </p>
        </div>
        <div className="flex gap-1">
          {severities.map((s) => (
            <button
              key={s || "all"}
              onClick={() => setSeverity(s)}
              className={`rounded-md border px-3 py-1.5 text-xs font-medium ${
                severity === s
                  ? "border-[#1B4FD8] bg-[#1B4FD8]/10 text-[#1B4FD8]"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {s || "All"}
            </button>
          ))}
        </div>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3">Rule</th>
              <th className="px-5 py-3">Finding</th>
              <th className="px-5 py-3">Product</th>
              <th className="px-5 py-3">Date</th>
              <th className="px-5 py-3">Scan</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center text-slate-400">
                  Loading…
                </td>
              </tr>
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center text-slate-400">
                  No violations found.
                </td>
              </tr>
            ) : (
              items.map((v) => (
                <tr key={v.id} className="border-b border-slate-50 align-top">
                  <td className="px-5 py-3">
                    <RuleBadge
                      ruleId={v.rule_id}
                      severity={v.severity}
                      type={v.violation_type as any}
                    />
                  </td>
                  <td className="px-5 py-3 text-slate-700">
                    {v.finding || v.rule_title || "—"}
                    {v.found_value ? (
                      <span className="mt-0.5 block font-mono text-xs text-slate-400">
                        found: {v.found_value}
                      </span>
                    ) : null}
                  </td>
                  <td className="px-5 py-3 text-slate-600">
                    {v.product_name || "—"}
                  </td>
                  <td className="px-5 py-3 tabular-nums text-slate-500">
                    {v.scanned_at ? v.scanned_at.slice(0, 10) : "—"}
                  </td>
                  <td className="px-5 py-3">
                    <Link
                      href={`/scan/${v.scan_id}`}
                      className="text-[#1B4FD8] hover:underline"
                    >
                      View
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
