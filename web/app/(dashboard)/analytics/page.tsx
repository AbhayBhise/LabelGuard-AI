"use client";

import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

export default function AnalyticsPage() {
  const [byRule, setByRule] = useState<any[]>([]);
  const [brands, setBrands] = useState<any[]>([]);
  const [trend, setTrend] = useState<any[]>([]);

  useEffect(() => {
    getData("/analytics/violations-by-rule").then(setByRule).catch(() => {});
    getData("/analytics/brand-compliance").then(setBrands).catch(() => {});
    getData("/analytics/violations-over-time")
      .then((d) => setTrend(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, []);

  async function getData(path: string) {
    const base = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/v1";
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("access_token") || ""
        : "";
    const res = await fetch(`${base}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    return res.json();
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">
          Enforcement Analytics
        </h1>
        <p className="text-sm text-slate-500">
          Policy intelligence for compliance enforcement
        </p>
      </div>

      <div className="grid grid-cols-2 gap-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">
            Violations Over Time
            <span className="ml-2 font-normal text-slate-400">
              (last 30 days)
            </span>
          </h2>
          <div className="h-60">
            {trend.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-400">
                No violations recorded in the last 30 days.
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="violations"
                    stroke="#1B4FD8"
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-sm font-semibold text-slate-700">
            Top Non-Compliant Brands
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
                <th className="py-2">Brand</th>
                <th className="py-2">Scans</th>
              </tr>
            </thead>
            <tbody>
              {(Array.isArray(brands) ? brands : []).map((b) => (
                <tr key={b.brand} className="border-b border-slate-50">
                  <td className="py-2 font-medium text-slate-700">
                    {b.brand}
                  </td>
                  <td className="py-2 text-slate-500">{b.total_scans}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 text-sm font-semibold text-slate-700">
          Violations by Rule
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-left text-xs uppercase text-slate-400">
              <th className="py-2">Rule</th>
              <th className="py-2">Count</th>
              <th className="py-2">% of Violations</th>
            </tr>
          </thead>
          <tbody>
            {(Array.isArray(byRule) ? byRule : []).map((r) => (
              <tr key={r.rule_id} className="border-b border-slate-50">
                <td className="py-2 font-mono text-xs text-slate-700">
                  {r.rule_id}
                </td>
                <td className="py-2 text-slate-500">{r.count}</td>
                <td className="py-2 text-slate-500">{r.percentage}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
