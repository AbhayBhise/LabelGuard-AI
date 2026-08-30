"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";
import ComplianceBadge, {
  ComplianceStatus,
} from "@/components/ComplianceBadge";
import { get } from "@/lib/api";

const donutColors = { COMPLIANT: "#16A34A", PARTIAL: "#D97706", NON_COMPLIANT: "#DC2626" };

type Summary = {
  total_scans: number;
  compliant: number;
  partial: number;
  non_compliant: number;
};

export default function DashboardPage() {
  const [summary, setSummary] = useState<Summary>({
    total_scans: 0,
    compliant: 0,
    partial: 0,
    non_compliant: 0,
  });
  const [scans, setScans] = useState<any[]>([]);
  const [byRule, setByRule] = useState<any[]>([]);

  useEffect(() => {
    get<Summary>("/analytics/summary").then(setSummary).catch(() => {});
    get<{ items: any[] }>("/scans?limit=6")
      .then((r) => setScans(r.items || []))
      .catch(() => {});
    get<any[]>("/analytics/violations-by-rule").then(setByRule).catch(() => {});
  }, []);

  const donutData = [
    { name: "COMPLIANT", value: summary.compliant },
    { name: "PARTIAL", value: summary.partial },
    { name: "NON_COMPLIANT", value: summary.non_compliant },
  ].filter((d) => d.value > 0);

  const stats = [
    { label: "Total Scans", value: summary.total_scans, color: "text-slate-900" },
    { label: "Compliant", value: summary.compliant, color: "text-success" },
    { label: "Non-Compliant", value: summary.non_compliant, color: "text-danger" },
    { label: "Partial", value: summary.partial, color: "text-warning" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
          <p className="text-sm text-slate-500">
            Compliance enforcement overview
          </p>
        </div>
        <Link
          href="/scan"
          className="rounded-md bg-[#1B4FD8] px-4 py-2 text-sm font-semibold text-white hover:bg-[#1740ad]"
        >
          + Start New Scan
        </Link>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {stats.map((s) => (
          <div
            key={s.label}
            className="rounded-xl border border-slate-200 bg-white p-5"
          >
            <div className="text-sm text-slate-500">{s.label}</div>
            <div className={`mt-2 text-3xl font-bold ${s.color}`}>
              {s.value}
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">
            Compliance Breakdown
          </h2>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={donutData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={80}
                  paddingAngle={2}
                >
                  {donutData.map((entry) => (
                    <Cell
                      key={entry.name}
                      fill={donutColors[entry.name as ComplianceStatus]}
                    />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-2 rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-4 text-sm font-semibold text-slate-700">
            Most Violated Rules
          </h2>
          <div className="h-52">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byRule} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis
                  type="category"
                  dataKey="rule_id"
                  width={60}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip />
                <Bar dataKey="count" fill="#1B4FD8" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white">
        <h2 className="border-b border-slate-100 p-5 text-sm font-semibold text-slate-700">
          Recent Scans
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 text-left text-xs uppercase tracking-wide text-slate-400">
              <th className="px-5 py-3">Scan ID</th>
              <th className="px-5 py-3">Source</th>
              <th className="px-5 py-3">Status</th>
              <th className="px-5 py-3">Score</th>
              <th className="px-5 py-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {scans.map((s) => (
              <tr key={s.id} className="border-b border-slate-50">
                <td className="px-5 py-3 font-mono text-xs text-slate-600">
                  {s.id.slice(0, 8)}
                </td>
                <td className="px-5 py-3 text-slate-600">
                  <span className="capitalize">{s.source}</span>
                </td>
                <td className="px-5 py-3">
                  <ComplianceBadge status={(s.overall_status || "PARTIAL") as ComplianceStatus} />
                </td>
                <td className="px-5 py-3 tabular-nums text-slate-600">
                  {s.compliance_score ?? "—"}
                </td>
                <td className="px-5 py-3">
                  <Link
                    href={`/scan/${s.id}`}
                    className="text-[#1B4FD8] hover:underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
