"use client";

import { useEffect, useState } from "react";
import { get } from "@/lib/api";

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [search, setSearch] = useState("");

  useEffect(() => {
    get<{ items: any[] }>(`/products?search=${search}`)
      .then((r) => setProducts(r.items || []))
      .catch(() => {});
  }, [search]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-slate-900">
          Product Repository
        </h1>
        <p className="text-sm text-slate-500">
          Browse previously scanned products and their compliance history
        </p>
      </div>

      <input
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder="Search by name, barcode or brand…"
        className="w-full max-w-md rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-[#1B4FD8] focus:outline-none"
      />

      <div className="grid grid-cols-3 gap-4">
        {products.map((p) => (
          <div
            key={p.id}
            className="rounded-xl border border-slate-200 bg-white p-5"
          >
            <div className="flex h-24 items-center justify-center rounded-md bg-slate-100 text-3xl">
              📦
            </div>
            <div className="mt-3 font-semibold text-slate-900">
              {p.product_name || "Unnamed product"}
            </div>
            <div className="text-xs text-slate-400">
              {p.brand || "Unknown brand"} · {p.category}
            </div>
            <div className="mt-2 font-mono text-xs text-slate-400">
              {p.barcode || "no barcode"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
